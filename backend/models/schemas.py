# backend/models/schemas.py — Pydantic Schemas cho API AI Lawyer

from typing import List, Optional
from pydantic import BaseModel, Field

# --- LAW CITATION / RAG SCHEMAS ---

class LawCitation(BaseModel):
    law_id: str
    law_name: str
    article_number: str
    article_title: str
    official_source: str
    content: str
    relevance_score: Optional[float] = None

# --- CHAT SCHEMAS ---

class ChatMessage(BaseModel):
    role: str = Field(..., description="Vai trò: 'user' hoặc 'assistant'")
    content: str = Field(..., description="Nội dung tin nhắn")

class ChatRequest(BaseModel):
    message: str = Field(..., description="Nội dung câu hỏi hoặc tình huống pháp lý của người dùng")
    history: List[ChatMessage] = Field(default=[], description="Lịch sử các tin nhắn trước đó trong phiên")
    category: str = Field(default="Tư vấn Tổng hợp", description="Lĩnh vực luật lựa chọn")
    api_key: Optional[str] = Field(default=None, description="Gemini API Key do client gửi lên (nếu có)")
    model: Optional[str] = Field(default=None, description="Tên model chỉ định (nếu muốn override)")

class ChatResponse(BaseModel):
    success: bool = Field(..., description="Trạng thái thành công")
    reply: str = Field(..., description="Nội dung câu trả lời tư vấn của AI Luật sư")
    category: str = Field(..., description="Lĩnh vực luật")
    model_used: str = Field(..., description="Model Gemini đã xử lý")
    disclaimer: str = Field(..., description="Lời nhắc miễn trừ trách nhiệm pháp lý")
    citations: List[LawCitation] = Field(default=[], description="Các điều luật chính thống được đối chiếu qua RAG")
    follow_ups: List[str] = Field(default=[], description="Các câu hỏi / hướng hành động gợi ý tiếp theo")

class HealthResponse(BaseModel):
    status: str
    api_key_configured: bool
    default_model: str
    version: str = "1.0.0"

class CategoryItem(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    sample_questions: List[str]

class ContractReviewResponse(BaseModel):
    success: bool
    filename: str
    review_result: str
    model_used: str
    disclaimer: str
    citations: List[LawCitation] = Field(default=[], description="Các điều luật liên quan trong hợp đồng")

# --- DOCX EXPORT SCHEMAS ---

class ExportContractDocxRequest(BaseModel):
    analysis_text: str = Field(..., description="Nội dung kết quả thẩm định hợp đồng")
    contract_title: str = Field(default="Hợp đồng kinh tế", description="Tên văn bản hợp đồng")
    protect_side: str = Field(default="Toàn diện", description="Góc nhìn bảo vệ")
    citations: Optional[List[dict]] = Field(default=None, description="Danh sách các điều luật đối chiếu")

class ExportChatDocxRequest(BaseModel):
    topic: str = Field(default="Tư vấn Pháp lý", description="Tiêu đề câu hỏi hoặc chủ đề tư vấn")
    opinion_text: str = Field(..., description="Nội dung ý kiến tư vấn của luật sư AI")
    citations: Optional[List[dict]] = Field(default=None, description="Danh sách các căn cứ pháp luật")


# --- PHIÊN TÒA GIẢ LẬP SCHEMAS (MOOT COURT) ---

class CourtTurnMessage(BaseModel):
    speaker: str = Field(..., description="'user', 'opposing', hoặc 'judge'")
    text: str = Field(..., description="Nội dung lời trình bày hoặc phản biện")

class CourtTurnRequest(BaseModel):
    case_title: str
    case_facts: str
    user_role: str
    user_argument: str
    dialogue_history: List[CourtTurnMessage] = Field(default=[])
    api_key: Optional[str] = None
    model: Optional[str] = None

class CourtTurnResponse(BaseModel):
    speaker: str = "opposing"
    statement: str
    persuasion_score: int = Field(default=50, description="Điểm thuyết phục của bạn hiện tại từ 0 - 100%")
    tip: Optional[str] = None
    model_used: str
    citations: List[LawCitation] = Field(default=[])

class VerdictRequest(BaseModel):
    case_title: str
    case_facts: str
    user_role: str
    dialogue_history: List[CourtTurnMessage]
    api_key: Optional[str] = None
    model: Optional[str] = None

class VerdictResponse(BaseModel):
    success: bool
    verdict_markdown: str
    model_used: str

class ExportVerdictDocxRequest(BaseModel):
    case_title: str
    user_role: str
    verdict_markdown: str
    dialogue_history: Optional[List[CourtTurnMessage]] = []

# --- LEGAL CALCULATOR SCHEMAS ---

class LegalCalculationRequest(BaseModel):
    calc_type: str = Field(..., description="'court_fee', 'late_interest', 'property_tax', hoặc 'severance_allowance'")
    amount: Optional[float] = Field(default=0.0, description="Giá ngạch tranh chấp (cho án phí)")
    dispute_type: Optional[str] = Field(default="civil", description="'civil', 'economic', hoặc 'administrative'")
    has_valuation: Optional[bool] = Field(default=True, description="Có giá ngạch hay không")
    principal: Optional[float] = Field(default=0.0, description="Số tiền nợ gốc chậm trả")
    start_date: Optional[str] = Field(default="", description="Ngày bắt đầu chậm trả (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default="", description="Ngày thanh toán / chốt nợ (YYYY-MM-DD)")
    rate_percent_per_year: Optional[float] = Field(default=None, description="Lãi suất thỏa thuận (%/năm)")
    price: Optional[float] = Field(default=0.0, description="Giá trị chuyển nhượng bất động sản")
    is_first_home: Optional[bool] = Field(default=False, description="Miễn thuế BĐS duy nhất")
    salary: Optional[float] = Field(default=0.0, description="Mức lương bình quân 6 tháng liền kề")
    working_years: Optional[float] = Field(default=0.0, description="Số năm làm việc thực tế tính trợ cấp")

class LegalCalculationResponse(BaseModel):
    success: bool
    title: str
    result_details: dict
    legal_basis: str
    summary_text: str

# --- PETITION GENERATOR SCHEMAS ---

class PetitionGenerateRequest(BaseModel):
    petition_type: str = Field(..., description="'civil_lawsuit', 'criminal_report', 'mutual_divorce', 'debt_notice', 'admin_complaint'")
    plaintiff_info: dict = Field(..., description="Thông tin người làm đơn / nguyên đơn (họ tên, CCCD, địa chỉ, sđt)")
    defendant_info: dict = Field(..., description="Thông tin người bị kiện / bị tố cáo")
    facts: str = Field(..., description="Tóm tắt diễn biến sự việc theo thời gian")
    claims: str = Field(..., description="Các yêu cầu đề nghị giải quyết")
    evidence_list: Optional[str] = Field(default="", description="Danh mục chứng cứ kèm theo")
    api_key: Optional[str] = None
    model: Optional[str] = None

class PetitionGenerateResponse(BaseModel):
    success: bool
    petition_type: str
    petition_title: str
    content_markdown: str
    model_used: str
    disclaimer: str

class ExportPetitionDocxRequest(BaseModel):
    petition_title: str
    content_markdown: str

# --- NEGOTIATION COACH SCHEMAS ---

class NegotiationTurnRequest(BaseModel):
    scenario_title: str
    user_role: str
    opponent_role: str
    context: str
    user_message: str
    dialogue_history: List[dict] = Field(default=[])
    api_key: Optional[str] = None
    model: Optional[str] = None

class NegotiationTurnResponse(BaseModel):
    opponent_reply: str
    tactical_analysis: str
    deal_readiness_score: int
    recommended_counter: str
    model_used: str

# --- EVIDENCE AUDITOR SCHEMAS ---

class EvidenceAuditRequest(BaseModel):
    case_summary: str = Field(..., description="Tóm tắt tình huống và yêu cầu khởi kiện")
    evidence_items: List[str] = Field(..., description="Danh sách các tài liệu, chứng cứ hiện có")
    api_key: Optional[str] = None
    model: Optional[str] = None

class EvidenceAuditItem(BaseModel):
    item: str
    grade: str
    probative_value: str
    vulnerability: str
    remedy: str

class EvidenceAuditResponse(BaseModel):
    success: bool
    overall_strength: str
    average_grade: str
    items: List[EvidenceAuditItem]
    general_recommendations: str
    model_used: str

# --- CORPORATE COMPLIANCE AUDIT SCHEMAS ---

class CorporateAuditRequest(BaseModel):
    company_name: str
    business_type: str
    employee_count: int
    industry: str
    compliance_notes: str
    api_key: Optional[str] = None
    model: Optional[str] = None

class CorporatePillarAudit(BaseModel):
    pillar_id: str
    pillar_name: str
    status: str
    risk_summary: str
    remediation_action: str
    legal_basis: str

class CorporateAuditResponse(BaseModel):
    success: bool
    company_name: str
    compliance_score: int
    summary: str
    pillars: List[CorporatePillarAudit]
    model_used: str

class ExportCorporateAuditDocxRequest(BaseModel):
    company_name: str
    business_type: str
    industry: str
    compliance_score: int
    summary: str
    pillars: List[dict]

