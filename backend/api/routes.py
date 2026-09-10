# backend/api/routes.py — Định tuyến API endpoints

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    CategoryItem,
    ContractReviewResponse,
    CourtTurnRequest,
    CourtTurnResponse,
    VerdictRequest,
    VerdictResponse,
    LawCitation
)
from backend.core.gemini_service import legal_service
from backend.core.config import settings
from backend.core.legal_prompts import SUPPORTED_CATEGORIES
from backend.core.court_prompts import PRESET_COURT_CASES
from backend.core.contract_parser import contract_parser
from backend.core.rag_engine import rag_engine

router = APIRouter(prefix="/api", tags=["Legal AI"])

# --- SYSTEM & CATEGORIES ---

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Kiểm tra trạng thái hoạt động của hệ thống."""
    return HealthResponse(
        status="healthy",
        api_key_configured=bool(settings.GEMINI_API_KEY),
        default_model=settings.DEFAULT_MODEL,
        version=settings.VERSION
    )

@router.get("/categories", response_model=List[CategoryItem])
async def get_categories():
    """Lấy danh sách các lĩnh vực pháp lý được hỗ trợ kèm câu hỏi mẫu."""
    return [CategoryItem(**cat) for cat in SUPPORTED_CATEGORIES]

# --- RAG LEGAL STORE API ---

@router.get("/laws/search", response_model=List[LawCitation])
async def search_laws(
    q: str = Query(..., description="Từ khóa hoặc số điều luật tra cứu"),
    domain: Optional[str] = Query(None, description="Lọc theo lĩnh vực pháp lý (criminal, civil, labor, land, corporate, marriage_family, procedure)")
):
    """Tra cứu trực tiếp các điều luật trong kho dữ liệu pháp luật chính thống (hỗ trợ lọc theo domain)."""
    results = rag_engine.search(q, domain=domain, top_k=6)
    return [
        LawCitation(
            law_id=r["law_id"],
            law_name=r["law_name"],
            article_number=r["article_number"],
            article_title=r["article_title"],
            official_source=r["official_source"],
            content=r["content"],
            relevance_score=r.get("relevance_score")
        )
        for r in results
    ]

@router.get("/laws/article/{law_id}/{article_number}", response_model=LawCitation)
async def get_law_article(law_id: str, article_number: str):
    """Lấy nguyên văn một điều luật cụ thể."""
    art = rag_engine.get_article(law_id, article_number)
    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy điều luật này trong kho lưu trữ.")
    return LawCitation(**art)

# --- CHAT CONSULTATION ---

@router.post("/chat", response_model=ChatResponse)
async def legal_chat(request: ChatRequest):
    """Tiếp nhận câu hỏi pháp lý và trả lời theo chuẩn mực 4 bước của Luật sư kết hợp RAG."""
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung câu hỏi không được để trống."
        )

    try:
        response = await legal_service.consult_legal_matter(
            message=request.message,
            history=request.history,
            category=request.category,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi không xác định: {str(e)}")

# --- CONTRACT REVIEW ---

@router.post("/review-contract", response_model=ContractReviewResponse)
async def review_contract(
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    party_role: str = Form("Bên tham gia hợp đồng"),
    focus_areas: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    """Thẩm định và rà soát hợp đồng (hỗ trợ upload PDF, DOCX, TXT, Hình ảnh scan hoặc dán trực tiếp text)."""
    contract_text = ""
    filename = "hop_dong_truc_tuyen.txt"
    raw_bytes = None
    mime_type = None

    if file:
        filename = file.filename
        file_bytes = await file.read()
        mime_type = file.content_type
        
        try:
            extracted_text, is_scanned = contract_parser.extract_text_from_bytes(file_bytes, filename)
            if is_scanned:
                raw_bytes = file_bytes
                contract_text = extracted_text
            else:
                contract_text = extracted_text
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    elif text_content and text_content.strip():
        contract_text = text_content.strip()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng tải lên file hợp đồng (PDF, Word, TXT, Ảnh) hoặc dán nội dung hợp đồng."
        )

    try:
        response = await legal_service.review_contract_document(
            contract_text=contract_text,
            filename=filename,
            raw_bytes=raw_bytes,
            mime_type=mime_type,
            party_role=party_role,
            focus_areas=focus_areas,
            custom_api_key=api_key,
            model_override=model
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi thẩm định: {str(e)}")

# --- PHIÊN TÒA GIẢ LẬP (MOOT COURT API) ---

@router.get("/moot-court/presets")
async def get_court_presets():
    """Lấy danh sách các kịch bản vụ án tranh tụng mẫu tại Tòa."""
    return PRESET_COURT_CASES

@router.post("/moot-court/turn", response_model=CourtTurnResponse)
async def court_turn(request: CourtTurnRequest):
    """Xử lý lượt đối chất phản biện của Luật sư đối phương."""
    if not request.user_argument.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lời tranh luận không được để trống."
        )

    try:
        response = await legal_service.simulate_court_turn(
            case_title=request.case_title,
            case_facts=request.case_facts,
            user_role=request.user_role,
            user_argument=request.user_argument,
            dialogue_history=request.dialogue_history,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi đối chất: {str(e)}")

@router.post("/moot-court/verdict", response_model=VerdictResponse)
async def court_verdict(request: VerdictRequest):
    """Yêu cầu Thẩm phán tuyên án sơ bộ dựa trên toàn bộ diễn biến tranh tụng."""
    if not request.dialogue_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần có ít nhất một lượt tranh tụng trước khi tuyên án."
        )

    try:
        response = await legal_service.generate_court_verdict(
            case_title=request.case_title,
            case_facts=request.case_facts,
            user_role=request.user_role,
            dialogue_history=request.dialogue_history,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi tuyên án: {str(e)}")
