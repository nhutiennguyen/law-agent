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
