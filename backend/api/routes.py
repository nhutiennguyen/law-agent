import logging
import re
import mimetypes
import unicodedata
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Request, status
from fastapi.responses import StreamingResponse, Response
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
    LawCitation,
    ExportContractDocxRequest,
    ExportChatDocxRequest
)
from backend.core.gemini_service import legal_service
from backend.core.config import settings
from backend.core.legal_prompts import SUPPORTED_CATEGORIES
from backend.core.court_prompts import PRESET_COURT_CASES
from backend.core.contract_parser import contract_parser
from backend.core.rag_engine import rag_engine
from backend.core.doc_exporter import create_contract_review_docx, create_legal_opinion_docx
from backend.core.security import (
    chat_limiter,
    upload_limiter,
    validate_message_length,
    validate_uploaded_file
)

logger = logging.getLogger("ai_lawyer.api")
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
async def legal_chat(request: ChatRequest, req: Request):
    """Tiếp nhận câu hỏi pháp lý và trả lời theo chuẩn mực của Luật sư kết hợp RAG."""
    # 1. Chống spam / DDoS
    chat_limiter.check_rate_limit(req)

    # 2. Kiểm tra dữ liệu đầu vào
    msg = request.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung câu hỏi không được để trống."
        )
    validate_message_length(msg)

    try:
        response = await legal_service.consult_legal_matter(
            message=msg,
            history=request.history,
            category=request.category,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Lỗi khi xử lý chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hệ thống AI đang bận hoặc gặp sự cố tạm thời. Vui lòng thử lại sau giây lát."
        )

@router.post("/chat/stream")
async def legal_chat_stream(request: ChatRequest, req: Request):
    """Tiếp nhận câu hỏi pháp lý và truyền luồng câu trả lời (Server-Sent Events) theo thời gian thực."""
    # 1. Chống spam
    chat_limiter.check_rate_limit(req)

    # 2. Kiểm tra dữ liệu đầu vào
    msg = request.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung câu hỏi không được để trống."
        )
    validate_message_length(msg)

    return StreamingResponse(
        legal_service.consult_legal_matter_stream(
            message=msg,
            history=request.history,
            category=request.category,
            custom_api_key=request.api_key,
            model_override=request.model
        ),
        media_type="text/event-stream"
    )

# --- CONTRACT REVIEW ---

@router.post("/review-contract", response_model=ContractReviewResponse)
async def review_contract(
    req: Request,
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    party_role: str = Form("Bên tham gia hợp đồng"),
    focus_areas: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    """Thẩm định và rà soát hợp đồng (hỗ trợ upload PDF, DOCX, TXT, Hình ảnh scan hoặc dán trực tiếp text)."""
    # 1. Chống spam upload làm tràn RAM
    upload_limiter.check_rate_limit(req)

    contract_text = ""
    filename = "hop_dong_truc_tuyen.txt"
    raw_bytes = None
    mime_type = None

    if file:
        filename = file.filename or "uploaded_file"
        file_bytes = await file.read()
        
        # 2. Kiểm tra định dạng và dung lượng file (< 10MB)
        validate_uploaded_file(filename, len(file_bytes))
        mime_type = file.content_type
        if not mime_type or mime_type == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(filename)
            mime_type = guessed or "application/octet-stream"
        
        try:
            extracted_text, is_scanned = contract_parser.extract_text_from_bytes(file_bytes, filename)
            contract_text = extracted_text
            # Nếu là file ảnh hoặc file PDF, lưu raw_bytes để Gemini Vision OCR trực tiếp
            fn_lower = filename.lower()
            if is_scanned or any(fn_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]):
                raw_bytes = file_bytes
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    elif text_content and text_content.strip():
        contract_text = text_content.strip()
        # Giới hạn độ dài dán text tối đa 50.000 ký tự (~20 trang văn bản)
        if len(contract_text) > 50000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Văn bản dán vào vượt quá 50.000 ký tự. Với hợp đồng dài, vui lòng tải file trực tiếp (PDF/Word)."
            )
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Lỗi thẩm định hợp đồng: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quá trình thẩm định gặp sự cố hoặc file bị lỗi cấu trúc. Vui lòng thử lại với file khác."
        )

# --- EXPORT WORD (.DOCX) API ---

def _slugify_filename(text: str, default: str = "document") -> str:
    """Chuyển đổi tên file thành ký tự ASCII an toàn cho HTTP Header Content-Disposition."""
    nfkd = unicodedata.normalize('NFKD', text)
    ascii_text = ''.join([c for c in nfkd if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D')
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', ascii_text).strip('_')
    return clean or default

@router.post("/export-contract-docx")
async def export_contract_docx(request: ExportContractDocxRequest, req: Request):
    """Xuất Báo cáo Thẩm định Hợp đồng thành file Microsoft Word (.DOCX) chuẩn Luật sư."""
    chat_limiter.check_rate_limit(req)
    try:
        bio = create_contract_review_docx(
            analysis_text=request.analysis_text,
            contract_title=request.contract_title,
            protect_side=request.protect_side,
            citations=request.citations
        )
        safe_title = _slugify_filename(request.contract_title, "Hop_dong")
        filename = f"Bao_cao_tham_dinh_{safe_title[:30]}.docx"
        return Response(
            content=bio.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.exception(f"Lỗi khi xuất file Word hợp đồng: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể tạo file Word. Vui lòng thử lại.")

@router.post("/export-chat-docx")
async def export_chat_docx(request: ExportChatDocxRequest, req: Request):
    """Xuất Ý kiến Tư vấn Pháp lý thành Thư tư vấn Word (.DOCX) chuyên nghiệp."""
    chat_limiter.check_rate_limit(req)
    try:
        bio = create_legal_opinion_docx(
            topic=request.topic,
            opinion_text=request.opinion_text,
            citations=request.citations
        )
        safe_topic = _slugify_filename(request.topic, "Tu_van_phap_ly")
        filename = f"Thu_tu_van_phap_ly_{safe_topic[:30]}.docx"
        return Response(
            content=bio.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.exception(f"Lỗi khi xuất file Word thư tư vấn: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể tạo file Word. Vui lòng thử lại.")

# --- PHIÊN TÒA GIẢ LẬP (MOOT COURT API) ---

@router.get("/moot-court/presets")
async def get_court_presets():
    """Lấy danh sách các kịch bản vụ án tranh tụng mẫu tại Tòa."""
    return PRESET_COURT_CASES

@router.post("/moot-court/turn", response_model=CourtTurnResponse)
async def court_turn(request: CourtTurnRequest, req: Request):
    """Xử lý lượt đối chất phản biện của Luật sư đối phương."""
    # 1. Chống spam
    chat_limiter.check_rate_limit(req)

    # 2. Kiểm tra độ dài lời tranh tụng
    arg = request.user_argument.strip()
    if not arg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lời tranh luận không được để trống."
        )
    validate_message_length(arg)

    try:
        response = await legal_service.simulate_court_turn(
            case_title=request.case_title,
            case_facts=request.case_facts,
            user_role=request.user_role,
            user_argument=arg,
            dialogue_history=request.dialogue_history,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Lỗi đối chất phiên tòa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Phiên tòa tạm dừng do lỗi xử lý. Vui lòng gửi lại luận điểm."
        )

@router.post("/moot-court/verdict", response_model=VerdictResponse)
async def court_verdict(request: VerdictRequest, req: Request):
    """Yêu cầu Thẩm phán tuyên án sơ bộ dựa trên toàn bộ diễn biến tranh tụng."""
    chat_limiter.check_rate_limit(req)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Lỗi tuyên án: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hội đồng xét xử đang bận, vui lòng thử lại sau giây lát."
        )
