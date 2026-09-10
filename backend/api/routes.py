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
    ExportChatDocxRequest,
    ExportVerdictDocxRequest,
    LegalCalculationRequest,
    LegalCalculationResponse,
    PetitionGenerateRequest,
    PetitionGenerateResponse,
    ExportPetitionDocxRequest,
    NegotiationTurnRequest,
    NegotiationTurnResponse,
    EvidenceAuditRequest,
    EvidenceAuditResponse,
    CorporateAuditRequest,
    CorporateAuditResponse,
    ExportCorporateAuditDocxRequest
)
from backend.core.gemini_service import legal_service
from backend.core.config import settings
from backend.core.legal_prompts import SUPPORTED_CATEGORIES
from backend.core.court_prompts import PRESET_COURT_CASES
from backend.core.contract_parser import contract_parser
from backend.core.rag_engine import rag_engine
from backend.core.doc_exporter import (
    create_contract_review_docx,
    create_legal_opinion_docx,
    create_court_verdict_docx,
    create_petition_docx,
    create_corporate_audit_docx
)
from backend.core.legal_calculator import (
    calculate_court_fee,
    calculate_late_interest,
    calculate_property_tax,
    calculate_severance_allowance
)
from backend.core.petition_templates import PETITION_TYPES
from backend.core.negotiation_prompts import PRESET_NEGOTIATION_SCENARIOS
from backend.core.telegram_bot import process_telegram_update
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

# --- LEGAL CALCULATOR API ---

@router.post("/calculate", response_model=LegalCalculationResponse)
async def calculate_legal_metrics(request: LegalCalculationRequest):
    """Tính toán án phí, lãi suất chậm trả, thuế bất động sản, hoặc trợ cấp thôi việc chuẩn xác theo luật."""
    calc_type = request.calc_type
    if calc_type == "court_fee":
        res = calculate_court_fee(
            amount=request.amount or 0.0,
            dispute_type=request.dispute_type or "civil",
            has_valuation=request.has_valuation if request.has_valuation is not None else True
        )
    elif calc_type == "late_interest":
        if not request.start_date or not request.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng cung cấp ngày bắt đầu và ngày kết thúc.")
        res = calculate_late_interest(
            principal=request.principal or 0.0,
            start_date_str=request.start_date,
            end_date_str=request.end_date,
            rate_percent_per_year=request.rate_percent_per_year
        )
    elif calc_type == "property_tax":
        res = calculate_property_tax(
            price=request.price or 0.0,
            is_first_home=bool(request.is_first_home)
        )
    elif calc_type == "severance_allowance":
        res = calculate_severance_allowance(
            salary=request.salary or 0.0,
            working_years=request.working_years or 0.0
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không hỗ trợ loại tính toán: {calc_type}")

    return LegalCalculationResponse(**res)


# --- PETITION GENERATOR API ---

@router.get("/petitions/types")
async def get_petition_types():
    """Lấy danh sách các biểu mẫu đơn từ tố tụng & hành chính được hỗ trợ."""
    return PETITION_TYPES

@router.post("/petitions/generate", response_model=PetitionGenerateResponse)
async def generate_petition(request: PetitionGenerateRequest, req: Request):
    """Soạn thảo đơn từ tố tụng, đơn khiếu nại, thông báo đòi nợ chuẩn văn bản hành chính."""
    chat_limiter.check_rate_limit(req)
    if not request.facts or not request.claims:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng nhập đầy đủ diễn biến sự việc và yêu cầu giải quyết.")

    try:
        response = await legal_service.generate_legal_petition(
            petition_type=request.petition_type,
            plaintiff_info=request.plaintiff_info,
            defendant_info=request.defendant_info,
            facts=request.facts,
            claims=request.claims,
            evidence_list=request.evidence_list or "",
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except Exception as e:
        logger.exception(f"Lỗi soạn thảo đơn: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi khi soạn thảo đơn từ: {str(e)}")

@router.post("/petitions/export-docx")
async def export_petition_docx(request: ExportPetitionDocxRequest):
    """Xuất đơn từ đã soạn thảo ra file Word (.docx) chuẩn thể thức Nghị quyết 01/2017 & Nghị định 30/2020."""
    try:
        docx_bytes = create_petition_docx(
            petition_title=request.petition_title,
            petition_markdown=request.content_markdown
        )
        safe_filename = _slugify_filename(request.petition_title, "Don_to_tung")[:40] + ".docx"
        return Response(
            content=docx_bytes.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
        )
    except Exception as e:
        logger.exception(f"Lỗi xuất Word đơn từ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể tạo file Word đơn từ.")


# --- MOOT COURT WORD EXPORT API ---

@router.post("/moot-court/export-docx")
async def export_verdict_docx(request: ExportVerdictDocxRequest):
    """Xuất bản án sơ bộ và biên bản tranh tụng ra file Word (.docx) chuẩn Tòa án."""
    try:
        docx_bytes = create_court_verdict_docx(
            case_title=request.case_title,
            user_role=request.user_role,
            verdict_markdown=request.verdict_markdown,
            dialogue_history=request.dialogue_history or []
        )
        safe_filename = "Ban_An_So_Bo_" + _slugify_filename(request.case_title, "Vu_an")[:30] + ".docx"
        return Response(
            content=docx_bytes.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
        )
    except Exception as e:
        logger.exception(f"Lỗi xuất Word bản án: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể tạo file Word bản án.")


# --- NEGOTIATION COACH API ---

@router.get("/negotiate/presets")
async def get_negotiation_presets():
    """Lấy danh sách các kịch bản đàm phán mô phỏng mẫu."""
    return PRESET_NEGOTIATION_SCENARIOS

@router.post("/negotiate/turn", response_model=NegotiationTurnResponse)
async def negotiate_turn(request: NegotiationTurnRequest, req: Request):
    """Mô phỏng lượt đối chất thương lượng và nhận xét chiến thuật."""
    chat_limiter.check_rate_limit(req)
    if not request.user_message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nội dung phát biểu thương lượng không được để trống.")

    try:
        response = await legal_service.simulate_negotiation_turn(
            scenario_title=request.scenario_title,
            user_role=request.user_role,
            opponent_role=request.opponent_role,
            context=request.context,
            user_message=request.user_message,
            dialogue_history=request.dialogue_history,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except Exception as e:
        logger.exception(f"Lỗi đàm phán: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi đàm phán: {str(e)}")


# --- EVIDENCE AUDITOR API ---

@router.post("/evidence/audit", response_model=EvidenceAuditResponse)
async def audit_evidence(request: EvidenceAuditRequest, req: Request):
    """Thẩm tra sức nặng và tính pháp lý của từng tài liệu chứng cứ."""
    chat_limiter.check_rate_limit(req)
    if not request.evidence_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng cung cấp ít nhất một tài liệu chứng cứ.")

    try:
        response = await legal_service.audit_evidence_items(
            case_summary=request.case_summary,
            evidence_items=request.evidence_items,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except Exception as e:
        logger.exception(f"Lỗi thẩm tra chứng cứ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi khi thẩm tra chứng cứ: {str(e)}")


# --- CORPORATE COMPLIANCE AUDIT API ---

@router.post("/corporate/audit", response_model=CorporateAuditResponse)
async def audit_corporate(request: CorporateAuditRequest, req: Request):
    """Khám sức khỏe pháp chế doanh nghiệp theo 8 trụ cột pháp lý 2026."""
    chat_limiter.check_rate_limit(req)
    if not request.company_name or not request.industry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng nhập tên công ty và ngành nghề hoạt động.")

    try:
        response = await legal_service.audit_corporate_compliance(
            company_name=request.company_name,
            business_type=request.business_type,
            employee_count=request.employee_count,
            industry=request.industry,
            compliance_notes=request.compliance_notes,
            custom_api_key=request.api_key,
            model_override=request.model
        )
        return response
    except Exception as e:
        logger.exception(f"Lỗi khám sức khỏe pháp chế: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi thẩm định pháp chế: {str(e)}")

@router.post("/corporate/export-docx")
async def export_corporate_docx(request: ExportCorporateAuditDocxRequest):
    """Xuất báo cáo khám sức khỏe pháp chế doanh nghiệp ra file Word (.docx)."""
    try:
        md_text = f"## 1. TỔNG QUAN ĐÁNH GIÁ SỨC KHỎE PHÁP CHẾ\n"
        md_text += f"- **Điểm tuân thủ tổng thể:** {request.compliance_score}/100\n"
        md_text += f"- **Nhận định chung:** {request.summary}\n\n"
        md_text += f"## 2. KẾT QUẢ RÀ SOÁT CHI TIẾT THEO 8 TRỤ CỘT PHÁP CHẾ\n\n"

        for p in request.pillars:
            status_badge = "🟢 ĐẠT YÊU CẦU" if p.get("status") == "compliant" else ("🟡 CẢNH BÁO RỦI RO" if p.get("status") == "warning" else "🔴 NGUY CƠ VI PHẠM NGHIÊM TRỌNG")
            md_text += f"### Trụ cột: {p.get('pillar_name', '')} ({status_badge})\n"
            md_text += f"- **Rủi ro tiềm ẩn:** {p.get('risk_summary', '')}\n"
            md_text += f"- **Hành động khắc phục cấp bách:** {p.get('remediation_action', '')}\n"
            md_text += f"- **Căn cứ pháp lý:** {p.get('legal_basis', '')}\n\n"

        docx_bytes = create_corporate_audit_docx(
            company_name=request.company_name,
            business_type=request.business_type,
            audit_markdown=md_text
        )
        safe_filename = "Bao_Cao_Phap_Che_" + _slugify_filename(request.company_name, "Doanh_nghiep")[:30] + ".docx"
        return Response(
            content=docx_bytes.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
        )
    except Exception as e:
        logger.exception(f"Lỗi xuất Word pháp chế: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể tạo file Word báo cáo pháp chế.")


# --- TELEGRAM BOT WEBHOOK API ---

@router.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Tiếp nhận và xử lý cập nhật tin nhắn từ Telegram Webhook."""
    try:
        update_data = await request.json()
        await process_telegram_update(update_data)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Lỗi xử lý telegram webhook: {str(e)}")
        return {"ok": False, "error": str(e)}

