# backend/core/gemini_service.py — Service kết nối Gemini qua Google GenAI SDK tích hợp RAG

import re
import json
import logging
import unicodedata
from typing import List, Optional, Any, Dict

# Tự động nạp chứng chỉ gốc từ hệ điều hành (Windows Certificate Store)
# để khắc phục lỗi SSL khi chạy qua Avast, Kaspersky hoặc Corporate Proxy
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from google import genai
from google.genai import types

from backend.core.config import settings
from backend.core.legal_prompts import (
    LEGAL_SYSTEM_INSTRUCTION,
    CONTRACT_REVIEW_SYSTEM_INSTRUCTION,
    LEGAL_DISCLAIMER
)
from backend.core.court_prompts import (
    OPPOSING_COUNSEL_INSTRUCTION,
    VERDICT_SYSTEM_INSTRUCTION
)
from backend.core.petition_templates import (
    PETITION_SYSTEM_PROMPT,
    PETITION_TYPES
)
from backend.core.negotiation_prompts import (
    NEGOTIATION_COACH_SYSTEM_INSTRUCTION
)
from backend.core.rag_engine import rag_engine
from backend.models.schemas import (
    ChatMessage,
    ChatResponse,
    ContractReviewResponse,
    CourtTurnMessage,
    CourtTurnResponse,
    VerdictResponse,
    LawCitation,
    NegotiationTurnResponse,
    EvidenceAuditResponse,
    EvidenceAuditItem,
    PetitionGenerateResponse,
    CorporateAuditResponse,
    CorporatePillarAudit
)

logger = logging.getLogger("ai_lawyer.gemini")

class GeminiLegalService:
    def __init__(self):
        pass

    def _get_client(self, custom_api_key: Optional[str] = None) -> genai.Client:
        """Khởi tạo Google GenAI client với API key được ưu tiên từ request, sau đó là biến môi trường."""
        api_key = (custom_api_key or "").strip() or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "Chưa gắn API Key trên máy chủ! Vui lòng cấu hình GEMINI_API_KEY trong file .env "
                "hoặc mở biểu tượng ⚙️ 'Cài đặt Kết nối' để nhập API Key."
            )
        return genai.Client(api_key=api_key)

    def _resolve_model(self, model_override: Optional[str] = None) -> str:
        """Chuẩn hóa model name, tự động dùng model mới nhất nếu model cũ bị deprecated hoặc nghẽn quota."""
        model = (model_override or "").strip()
        if not model or "2.5" in model or "2.0" in model or "1.5" in model or model in ["gemini-3.5-flash", "gemini-3.6-flash"]:
            return settings.DEFAULT_MODEL
        return model

    def _generate_with_fallback(self, client: genai.Client, primary_model: str, contents: Any, config: Any):
        """Gọi model với cơ chế tự động fallback nếu model gặp 503 high demand hoặc 429 quota."""
        resolved_primary = self._resolve_model(primary_model)
        model_queue = [resolved_primary]
        for m in [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
        ]:
            if m not in model_queue:
                model_queue.append(m)

        last_error = None
        for m in model_queue:
            try:
                resp = client.models.generate_content(model=m, contents=contents, config=config)
                return resp, m
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Model {m} failed ({err_str[:80]}), trying next fallback...")
                last_error = e
        raise last_error

    @staticmethod
    def _extract_json_dict(text: str) -> Dict[str, Any]:
        """Trích xuất và parse an toàn JSON dictionary từ phản hồi LLM."""
        raw = (text or "").strip()
        try:
            return json.loads(raw)
        except Exception:
            pass

        m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end+1])
            except Exception:
                pass

        raise ValueError(f"Không thể trích xuất JSON hợp lệ từ phản hồi AI: {raw[:150]}")

    def _is_conversational_or_meta_query(self, message: str) -> bool:
        """Nhận diện các câu hỏi chào hỏi, hỏi danh tính, hỏi người sáng lập để không kích hoạt RAG luật máy móc."""
        # Chuẩn hóa loại bỏ toàn bộ dấu tiếng Việt để so khớp không bao giờ trượt
        nfkd = unicodedata.normalize('NFKD', message.strip().lower())
        norm = ''.join([c for c in nfkd if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D').strip()
        cleaned = re.sub(r'[^\w\s]', '', norm).strip()

        # 0. Loại trừ ngay nếu người dùng đang nói về người thân/bố trong gia đình:
        # Ví dụ: "bố tôi bảo", "bố bảo tôi làm giấy tờ", "bố bảo chia đất", "bố mẹ bảo"
        family_father_patterns = [
            "bo toi", "bo em", "bo minh", "bo me", "ba me",
            "bo bao toi", "bo bao em", "bo bao minh", "bo bao phai",
            "bo bao chia", "bo bao lam", "bo bao ky", "bo bao di",
            "bo bao ban", "bo bao mua", "bo dan", "bo keu"
        ]
        if any(p in norm for p in family_father_patterns):
            return False

        # 1. Chào hỏi thông thường
        greetings = [
            "chao", "hello", "hi", "alo", "e", "ban oi", "hi ban", "hey",
            "chao ban", "chao bot", "xin chao", "chao cau", "chao em"
        ]
        if cleaned in greetings or any(cleaned == g for g in greetings):
            return True

        # 2. Hỏi trực tiếp về người sáng lập / tác giả / nguồn gốc
        creator_questions = [
            "bo bao la ai", "ai la bo bao", "ai tao ra", "ai sang lap",
            "ai lam ra", "ai phat trien", "nguoi sang lap", "cha de", "ong chu",
            "tac gia la ai", "ai lap trinh", "ai code ra", "nguon goc cua ban"
        ]
        if any(p in norm for p in creator_questions):
            return True

        # 3. Hỏi về danh tính / bạn là ai / bạn tên gì
        if any(p in norm for p in ["ban la ai", "ten gi", "ban ten", "may la ai", "bot la ai", "huynh nguyen khang la ai"]):
            return True

        # 4. Thắc mắc / hỏi lại ngắn: "là sao", "sao vậy", "nghĩa là gì", "ý bạn là gì"
        clarifications = [
            "la sao", "sao the", "sao vay", "nghia la sao", "nghia la gi",
            "y la sao", "y ban la gi", "y cua ban", "tai sao", "the la sao", "the nao"
        ]
        if cleaned in clarifications or any(cleaned == c for c in clarifications):
            return True

        # 5. Hỏi về khả năng / bạn làm được gì
        if any(p in norm for p in ["lam duoc gi", "giup duoc gi", "biet gi", "tinh nang", "huong dan"]):
            return True

        # 6. Khen ngợi / Cảm ơn / Tán gẫu ngắn
        if cleaned in ["cam on", "thank you", "thanks", "ok", "oke", "tuyet voi", "gioi qua", "hay qua"]:
            return True

        return False

    def _extract_follow_ups(self, text: str) -> tuple[str, List[str]]:
        """Tách khối [GỢI Ý HỎI TIẾP] khỏi văn bản trả lời để hiển thị chip tương tác mượt mà."""
        follow_ups = []
        cleaned_text = text

        # 1. Tìm khối chuẩn [GỢI Ý HỎI TIẾP]
        pattern = r'\[GỢI Ý HỎI TIẾP\]\s*:\s*\n?((?:[-*•\d\.]\s*[^\n]+\n?)+)'
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            block = match.group(1)
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            for line in lines:
                cleaned_line = re.sub(r'^[-*•\d\.]+\s*', '', line).strip()
                cleaned_line = cleaned_line.strip('<>[]{}"\'')
                if cleaned_line and len(cleaned_line) > 5:
                    follow_ups.append(cleaned_line)
            cleaned_text = text[:match.start()].rstrip()
        else:
            # 2. Pattern linh hoạt nếu model trả về không có ngoặc vuông
            alt_pattern = r'(?:GỢI Ý HỎI TIẾP|CÂU HỎI GỢI Ý|HƯỚNG ĐI TIẾP THEO)\s*:\s*\n?((?:[-*•\d\.]\s*[^\n]+\n?)+)'
            alt_match = re.search(alt_pattern, text, flags=re.IGNORECASE)
            if alt_match:
                block = alt_match.group(1)
                lines = [line.strip() for line in block.split('\n') if line.strip()]
                for line in lines:
                    cleaned_line = re.sub(r'^[-*•\d\.]+\s*', '', line).strip()
                    cleaned_line = cleaned_line.strip('<>[]{}"\'')
                    if cleaned_line and len(cleaned_line) > 5:
                        follow_ups.append(cleaned_line)
                cleaned_text = text[:alt_match.start()].rstrip()

        return cleaned_text, follow_ups[:4]

    async def consult_legal_matter(
        self,
        message: str,
        history: List[ChatMessage] = [],
        category: str = "Tư vấn Tổng hợp",
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> ChatResponse:
        """Xử lý yêu cầu tư vấn pháp lý với Gemini theo phong cách luật sư thực chiến, tự nhiên."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        is_meta = self._is_conversational_or_meta_query(message)

        # 1. RAG Retrieval: Chỉ tìm kiếm các điều luật nếu đây là tình huống pháp luật thực sự
        relevant_articles = []
        rag_context_prompt = ""

        if not is_meta:
            relevant_articles = rag_engine.search(message, category=category, top_k=3)
            if relevant_articles:
                rag_context_prompt = "\n=== VĂN BẢN QUY PHẠM PHÁP LUẬT THAM CHIẾU (NGUỒN CHÍNH THỐNG VBPL.VN) ===\n"
                for art in relevant_articles:
                    rag_context_prompt += (
                        f"\n【{art['law_name']} - {art['article_number']}: {art['article_title']}】\n"
                        f"{art['content']}\n"
                        f"Nguồn xác thực Nhà nước: {art['official_source']}\n"
                    )
                rag_context_prompt += (
                    "\nLƯU Ý DÀNH CHO BẠN: Hãy vận dụng các điều luật trên vào phân tích thực tế một cách tự nhiên, "
                    "dễ hiểu, giải thích thẳng vào câu trả lời thân chủ cần. Tránh chép nguyên văn khô cứng như sách giáo khoa!\n"
                )
        else:
            rag_context_prompt = (
                "\n[CHỈ DẪN GIAO TIẾP]: Người dùng đang giao tiếp tự nhiên, chào hỏi, hoặc thắc mắc làm rõ ý. "
                "Hãy trả lời thật tự nhiên, điềm đạm, khiêm tốn, lịch sự và đúng trọng tâm. "
                "TUYỆT ĐỐI KHÔNG tự động nói dông dài ca ngợi người sáng lập (chỉ giới thiệu ngắn gọn 1 câu nếu người dùng hỏi trực tiếp 'Bố Bảo là ai' hoặc 'Ai tạo ra bạn'). "
                "Nếu người dùng nói 'là sao' hoặc thắc mắc, hãy giải thích ngắn gọn, rõ ràng xem họ đang muốn làm rõ vấn đề gì.\n"
            )

        contents = []
        for item in history:
            role = "model" if item.role in ["assistant", "model"] else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item.content)]
                )
            )

        # Gắn kèm chỉ định lĩnh vực và bối cảnh
        category_header = f"[Lĩnh vực tham vấn: {category}]\n" if category and category != "Tư vấn Tổng hợp" and not is_meta else ""
        user_content_text = f"{category_header}{rag_context_prompt}\n[Câu hỏi của người dùng]:\n{message}"

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_content_text)]
            )
        )

        config = types.GenerateContentConfig(
            system_instruction=LEGAL_SYSTEM_INSTRUCTION,
            temperature=0.5 if is_meta else 0.35,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )

            raw_reply_text = response.text if response and response.text else "Không nhận được phản hồi từ mô hình."

            # Tách khối gợi ý hỏi tiếp để hiển thị chip tương tác mượt mà
            clean_reply, follow_ups = self._extract_follow_ups(raw_reply_text)

            citations_list = [
                LawCitation(
                    law_id=a["law_id"],
                    law_name=a["law_name"],
                    article_number=a["article_number"],
                    article_title=a["article_title"],
                    official_source=a["official_source"],
                    content=a["content"],
                    relevance_score=a.get("relevance_score")
                )
                for a in relevant_articles
            ]

            return ChatResponse(
                success=True,
                reply=clean_reply,
                category=category,
                model_used=used_model,
                disclaimer=LEGAL_DISCLAIMER,
                citations=citations_list,
                follow_ups=follow_ups
            )

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Lỗi khi gọi Gemini API: {err_msg}")
            if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg:
                user_err = "Khóa Gemini API Key không hợp lệ. Vui lòng kiểm tra lại trong menu Cài đặt."
            elif "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                user_err = "Hạn ngạch (Quota) của Gemini API Key hiện tại đã tạm thời hết. Vui lòng thử lại sau hoặc đổi API Key."
            else:
                user_err = f"Đã xảy ra lỗi khi kết nối với máy chủ AI: {err_msg}"
            raise RuntimeError(user_err)

    async def consult_legal_matter_stream(
        self,
        message: str,
        history: List[ChatMessage] = [],
        category: str = "Tư vấn Tổng hợp",
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ):
        """Xử lý tư vấn pháp lý với Gemini dưới dạng Server-Sent Events (SSE) stream."""
        try:
            client = self._get_client(custom_api_key)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
            return

        model_name = self._resolve_model(model_override)
        is_meta = self._is_conversational_or_meta_query(message)

        relevant_articles = []
        rag_context_prompt = ""

        if not is_meta:
            relevant_articles = rag_engine.search(message, category=category, top_k=3)
            if relevant_articles:
                rag_context_prompt = "\n=== VĂN BẢN QUY PHẠM PHÁP LUẬT THAM CHIẾU (NGUỒN CHÍNH THỐNG VBPL.VN) ===\n"
                for art in relevant_articles:
                    rag_context_prompt += (
                        f"\n【{art['law_name']} - {art['article_number']}: {art['article_title']}】\n"
                        f"{art['content']}\n"
                        f"Nguồn xác thực Nhà nước: {art['official_source']}\n"
                    )
                rag_context_prompt += (
                    "\nLƯU Ý DÀNH CHO BẠN: Hãy vận dụng các điều luật trên vào phân tích thực tế một cách tự nhiên, "
                    "dễ hiểu, giải thích thẳng vào câu trả lời thân chủ cần. Tránh chép nguyên văn khô cứng như sách giáo khoa!\n"
                )
        else:
            rag_context_prompt = (
                "\n[CHỈ DẪN GIAO TIẾP]: Người dùng đang giao tiếp tự nhiên, chào hỏi, hoặc thắc mắc làm rõ ý. "
                "Hãy trả lời thật tự nhiên, điềm đạm, khiêm tốn, lịch sự và đúng trọng tâm. "
                "TUYỆT ĐỐI KHÔNG tự động nói dông dài ca ngợi người sáng lập (chỉ giới thiệu ngắn gọn 1 câu nếu người dùng hỏi trực tiếp 'Bố Bảo là ai' hoặc 'Ai tạo ra bạn'). "
                "Nếu người dùng nói 'là sao' hoặc thắc mắc, hãy giải thích ngắn gọn, rõ ràng xem họ đang muốn làm rõ vấn đề gì.\n"
            )

        citations_list = [
            {
                "law_id": a["law_id"],
                "law_name": a["law_name"],
                "article_number": a["article_number"],
                "article_title": a["article_title"],
                "official_source": a["official_source"],
                "content": a["content"],
                "relevance_score": a.get("relevance_score")
            }
            for a in relevant_articles
        ]

        # 1. Gửi sự kiện danh sách điều luật trích dẫn RAG
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations_list}, ensure_ascii=False)}\n\n"

        contents = []
        for item in history:
            role = "model" if item.role in ["assistant", "model"] else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item.content)]
                )
            )

        category_header = f"[Lĩnh vực tham vấn: {category}]\n" if category and category != "Tư vấn Tổng hợp" and not is_meta else ""
        user_content_text = f"{category_header}{rag_context_prompt}\n[Câu hỏi của người dùng]:\n{message}"

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_content_text)]
            )
        )

        config = types.GenerateContentConfig(
            system_instruction=LEGAL_SYSTEM_INSTRUCTION,
            temperature=0.5 if is_meta else 0.35,
            top_p=0.95,
        )

        model_queue = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
        ]
        resolved = self._resolve_model(model_override)
        if resolved and resolved in model_queue:
            model_queue.remove(resolved)
            model_queue.insert(0, resolved)

        stream_success = False
        full_reply_text = ""
        used_model = model_queue[0]

        for m in model_queue:
            try:
                stream = client.models.generate_content_stream(model=m, contents=contents, config=config)
                for chunk in stream:
                    if chunk.text:
                        full_reply_text += chunk.text
                        yield f"data: {json.dumps({'type': 'token', 'token': chunk.text}, ensure_ascii=False)}\n\n"
                used_model = m
                stream_success = True
                break
            except Exception as e:
                logger.warning(f"Streaming model {m} failed ({str(e)[:80]}), trying next fallback...")
                if not full_reply_text:
                    continue
                else:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
                    return

        if not stream_success:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Tất cả mô hình AI đang bận hoặc quá tải quota. Vui lòng thử lại sau giây lát.'}, ensure_ascii=False)}\n\n"
            return

        # Tách khối gợi ý hỏi tiếp để hiển thị chips tương tác
        clean_reply, follow_ups = self._extract_follow_ups(full_reply_text)

        yield f"data: {json.dumps({'type': 'follow_ups', 'follow_ups': follow_ups}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'model_used': used_model, 'disclaimer': LEGAL_DISCLAIMER}, ensure_ascii=False)}\n\n"

    async def review_contract_document(
        self,
        contract_text: str,
        filename: str,
        raw_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        party_role: str = "Bên tham gia hợp đồng",
        focus_areas: Optional[str] = None,
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> ContractReviewResponse:
        """Thẩm định và rà soát hợp đồng theo ma trận 5 phần tích hợp RAG & Multimodal Vision OCR."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        # RAG search theo nội dung hợp đồng
        sample_query = f"{party_role} {focus_areas or ''} {contract_text[:1000]}"
        relevant_articles = rag_engine.search(sample_query, top_k=3)

        rag_laws_text = ""
        if relevant_articles:
            rag_laws_text = "\n=== VĂN BẢN LUẬT THAM CHIẾU ĐỐI CHIẾU ĐIỀU KHOẢN HỢP ĐỒNG (VBPL.VN) ===\n"
            for art in relevant_articles:
                rag_laws_text += f"\n【{art['law_name']} - {art['article_number']}: {art['article_title']}】\n{art['content']}\n"

        prompt_instruction = (
            f"Vui lòng thẩm định hợp đồng đính kèm cho tôi.\n"
            f"- Vị thế của tôi trong hợp đồng: {party_role}\n"
            f"- Trọng tâm rà soát: {focus_areas or 'Rà soát toàn diện các điều khoản rủi ro, gài bẫy và vi phạm luật'}\n"
            f"- Tên tài liệu: {filename}\n"
            f"{rag_laws_text}\n"
        )

        parts = [types.Part.from_text(text=prompt_instruction)]

        # Multimodal Vision: Nếu có raw_bytes (ảnh chụp scan, PDF có con dấu/chữ ký) thì truyền trực tiếp vào Gemini Vision
        has_bytes = bool(raw_bytes and mime_type)
        has_text = bool(contract_text and contract_text.strip())

        if has_bytes:
            parts.append(
                types.Part.from_bytes(
                    data=raw_bytes,
                    mime_type=mime_type
                )
            )
            if has_text:
                parts.append(
                    types.Part.from_text(
                        text=f"\n=== VĂN BẢN TRÍCH XUẤT ĐÍNH KÈM (THAM KHẢO THÊM) ===\n\n{contract_text}"
                    )
                )
        elif has_text:
            parts.append(
                types.Part.from_text(
                    text=f"\n=== NỘI DUNG VĂN BẢN HỢP ĐỒNG ===\n\n{contract_text}"
                )
            )
        else:
            raise ValueError("Không tìm thấy nội dung văn bản hợp đồng để thẩm định.")

        contents = [types.Content(role="user", parts=parts)]

        config = types.GenerateContentConfig(
            system_instruction=CONTRACT_REVIEW_SYSTEM_INSTRUCTION,
            temperature=0.15,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )

            result_text = response.text if response and response.text else "Không nhận được kết quả thẩm định."

            citations_list = [
                LawCitation(
                    law_id=a["law_id"],
                    law_name=a["law_name"],
                    article_number=a["article_number"],
                    article_title=a["article_title"],
                    official_source=a["official_source"],
                    content=a["content"]
                )
                for a in relevant_articles
            ]

            return ContractReviewResponse(
                success=True,
                filename=filename,
                review_result=result_text,
                model_used=model_name,
                disclaimer=LEGAL_DISCLAIMER,
                citations=citations_list
            )

        except Exception as e:
            logger.error(f"Lỗi khi rà soát hợp đồng: {str(e)}")
            raise RuntimeError(f"Lỗi thẩm định hợp đồng: {str(e)}")

    # --- PHIÊN TÒA GIẢ LẬP METHODS (MOOT COURT) ---

    async def simulate_court_turn(
        self,
        case_title: str,
        case_facts: str,
        user_role: str,
        user_argument: str,
        dialogue_history: List[CourtTurnMessage] = [],
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> CourtTurnResponse:
        """Xử lý lượt đối chất phản biện của Luật sư đối phương trong phiên tòa giả lập có RAG."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        # RAG search các quy định pháp luật phục vụ bên đối tụng
        relevant_articles = rag_engine.search(f"{case_title} {user_argument}", top_k=2)
        law_injection = ""
        if relevant_articles:
            law_injection = "\n=== CĂN CỨ LUẬT BẤT LỢI CHO ĐỐI PHƯƠNG ĐỂ BẠN DÙNG TẤN CÔNG ===\n"
            for a in relevant_articles:
                law_injection += f"- {a['law_name']} ({a['article_number']}: {a['article_title']}): {a['content'][:300]}...\n"

        history_text = ""
        for msg in dialogue_history:
            speaker_label = "BẠN" if msg.speaker == "user" else ("LUẬT SƯ ĐỐI TỤNG" if msg.speaker == "opposing" else "THẨM PHÁN")
            history_text += f"\n[{speaker_label}]: {msg.text}\n"

        prompt = (
            f"=== BỐI CẢNH VỤ ÁN TRANH CHẤP TẠI TÒA ===\n"
            f"Vụ án: {case_title}\n"
            f"Tình tiết vụ việc: {case_facts}\n"
            f"Vị thế của người dùng: {user_role}\n"
            f"Vị thế của bạn: Luật sư đối tụng của bên kia\n\n"
            f"{law_injection}\n"
            f"=== DIỄN BIẾN TRANH TỤNG TRƯỚC ĐÓ ===\n{history_text or '(Bắt đầu lượt tranh tụng đầu tiên)'}\n\n"
            f"=== LỜI KHAI / LẬP LUẬN MỚI NHẤT CỦA NGƯỜI DÙNG ===\n{user_argument}\n\n"
            f"YÊU CẦU ĐỐI VỚI BẠN:\n"
            f"1. Phản biện gay gắt, bóc tách sơ hở và chất vấn dồn ép theo quy chuẩn OPPOSING_COUNSEL_INSTRUCTION.\n"
            f"2. Cuối câu trả lời, hãy kèm 2 dòng đặc biệt để hệ thống chấm điểm:\n"
            f"SCORE: [Một con số từ 0 đến 100 thể hiện mức độ vững chắc chứng cứ hiện tại của người dùng]\n"
            f"TIP: [Một câu ngắn gợi ý thân chủ nên đưa ra chứng cứ gì để lật ngược tình thế]"
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            system_instruction=OPPOSING_COUNSEL_INSTRUCTION,
            temperature=0.3,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )

            raw_text = response.text or ""
            persuasion_score = 50
            tip = None

            score_match = re.search(r"SCORE:\s*(\d+)", raw_text)
            if score_match:
                persuasion_score = max(5, min(95, int(score_match.group(1))))
                raw_text = re.sub(r"SCORE:\s*\d+", "", raw_text)

            tip_match = re.search(r"TIP:\s*(.+)", raw_text)
            if tip_match:
                tip = tip_match.group(1).strip()
                raw_text = re.sub(r"TIP:\s*.+", "", raw_text)

            statement = raw_text.strip()

            citations_list = [
                LawCitation(
                    law_id=a["law_id"],
                    law_name=a["law_name"],
                    article_number=a["article_number"],
                    article_title=a["article_title"],
                    official_source=a["official_source"],
                    content=a["content"]
                )
                for a in relevant_articles
            ]

            return CourtTurnResponse(
                speaker="opposing",
                statement=statement,
                persuasion_score=persuasion_score,
                tip=tip,
                model_used=model_name,
                citations=citations_list
            )

        except Exception as e:
            logger.error(f"Lỗi lượt tranh tụng: {str(e)}")
            raise RuntimeError(f"Lỗi trong phiên đối chất: {str(e)}")

    async def generate_court_verdict(
        self,
        case_title: str,
        case_facts: str,
        user_role: str,
        dialogue_history: List[CourtTurnMessage],
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> VerdictResponse:
        """Thẩm phán tổng kết và tuyên án sơ bộ dựa trên toàn bộ diễn biến tranh tụng."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        history_text = ""
        for msg in dialogue_history:
            speaker_label = "BẠN" if msg.speaker == "user" else ("LUẬT SƯ ĐỐI TỤNG" if msg.speaker == "opposing" else "THẨM PHÁN")
            history_text += f"\n[{speaker_label}]: {msg.text}\n"

        prompt = (
            f"=== HỒ SƠ VỤ ÁN XÉT XỬ ===\n"
            f"Tên vụ án: {case_title}\n"
            f"Nội dung sự việc: {case_facts}\n"
            f"Tư cách tố tụng của người dùng: {user_role}\n\n"
            f"=== TOÀN BỘ BIÊN BẢN PHIÊN TRANH TỤNG TẠI TÒA ===\n{history_text}\n\n"
            f"Yêu cầu: Hãy đóng vai Hội Đồng Xét Xử tuyên bản án sơ bộ theo đúng quy định VERDICT_SYSTEM_INSTRUCTION."
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            system_instruction=VERDICT_SYSTEM_INSTRUCTION,
            temperature=0.2,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )

            verdict_text = response.text or "Không thể tạo bản án sơ bộ."

            return VerdictResponse(
                success=True,
                verdict_markdown=verdict_text,
                model_used=model_name
            )
        except Exception as e:
            logger.error(f"Lỗi tuyên án: {str(e)}")
            raise RuntimeError(f"Lỗi khi ban hành phán quyết: {str(e)}")

    async def simulate_negotiation_turn(
        self,
        scenario_title: str,
        user_role: str,
        opponent_role: str,
        context: str,
        user_message: str,
        dialogue_history: List[Dict[str, str]],
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> NegotiationTurnResponse:
        """Mô phỏng lượt đối chất thương lượng và nhận xét chiến thuật."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        history_text = ""
        for msg in dialogue_history:
            spk = msg.get("speaker", "user") if isinstance(msg, dict) else getattr(msg, "speaker", "user")
            txt = msg.get("text", "") if isinstance(msg, dict) else getattr(msg, "text", "")
            lbl = "BẠN" if spk == "user" else "ĐỐI PHƯƠNG"
            history_text += f"[{lbl}]: {txt}\n"

        prompt = (
            f"=== BỐI CẢNH ĐÀM PHÁN & TRANH CHẤP ===\n"
            f"Chủ đề: {scenario_title}\n"
            f"Tư cách của bạn (Người dùng): {user_role}\n"
            f"Đối phương cần thương lượng: {opponent_role}\n"
            f"Bối cảnh cụ thể: {context}\n\n"
            f"=== LỊCH SỬ THƯƠNG LƯỢNG TRƯỚC ĐÓ ===\n{history_text or '(Chưa có cuộc trò chuyện trước đó)'}\n\n"
            f"=== LƯỢT PHÁT BIỂU MỚI NHẤT CỦA BẠN ===\n\"{user_message}\"\n\n"
            f"Hãy phản hồi theo đúng cấu trúc của NEGOTIATION_COACH_SYSTEM_INSTRUCTION:\n"
            f"[ĐỐI PHƯƠNG PHẢN HỒI]: <nội dung đối phương nói>\n"
            f"[NHẬN XÉT CHIẾN THUẬT]: <phân tích điểm hớ, mách nước chiêu cờ, câu thoại mẫu gợi ý>\n"
            f"SCORE: <con số từ 0 đến 100>"
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            system_instruction=NEGOTIATION_COACH_SYSTEM_INSTRUCTION,
            temperature=0.35,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )
            raw_text = response.text or ""

            opponent_reply = "Tôi ghi nhận ý kiến của bạn nhưng chúng ta cần thỏa thuận lại."
            tactical_analysis = ""
            score = 50
            recommended_counter = ""

            opp_match = re.search(r"\[ĐỐI PHƯƠNG PHẢN HỒI\]:\s*(.*?)(?=\[NHẬN XÉT CHIẾN THUẬT\]|SCORE:|$)", raw_text, re.DOTALL)
            if opp_match:
                opponent_reply = opp_match.group(1).strip()

            tac_match = re.search(r"\[NHẬN XÉT CHIẾN THUẬT\]:\s*(.*?)(?=SCORE:|$)", raw_text, re.DOTALL)
            if tac_match:
                tactical_analysis = tac_match.group(1).strip()

            score_match = re.search(r"SCORE:\s*(\d+)", raw_text)
            if score_match:
                score = min(100, max(0, int(score_match.group(1))))

            counter_match = re.search(r"Câu thoại mẫu gợi ý cho bạn:[\s*]*[\"“](.*?)[\"”]", tactical_analysis, re.DOTALL)
            if counter_match:
                recommended_counter = counter_match.group(1).strip()

            return NegotiationTurnResponse(
                opponent_reply=opponent_reply,
                tactical_analysis=tactical_analysis,
                deal_readiness_score=score,
                recommended_counter=recommended_counter,
                model_used=used_model
            )
        except Exception as e:
            logger.error(f"Lỗi đàm phán: {str(e)}")
            raise RuntimeError(f"Lỗi trong quá trình huấn luyện đàm phán: {str(e)}")

    async def audit_evidence_items(
        self,
        case_summary: str,
        evidence_items: List[str],
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> EvidenceAuditResponse:
        """Thẩm tra sức nặng và tính pháp lý của từng tài liệu chứng cứ."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        evidence_str = "\n".join([f"- {i+1}. {item}" for i, item in enumerate(evidence_items)])

        prompt = (
            f"=== THẨM TRA VÀ ĐÁNH GIÁ SỨC NẶNG CHỨNG CỨ TỐ TỤNG ===\n"
            f"Tóm tắt vụ án / Yêu cầu tranh chấp:\n{case_summary}\n\n"
            f"Danh sách tài liệu, chứng cứ hiện có:\n{evidence_str}\n\n"
            f"Yêu cầu: Dựa trên Bộ luật Tố tụng Dân sự 2015 (Điều 86-97) và Bộ luật Tố tụng Hình sự 2015, "
            f"hãy thẩm định 3 thuộc tính: Tính khách quan, Tính hợp pháp, Tính liên quan.\n"
            f"Xếp loại từng chứng cứ theo thang điểm: A+ (Vàng/Tuyệt đối), A (Mạnh), B (Bổ trợ), C (Yếu), F (Không giá trị/Bất hợp pháp).\n"
            f"Nêu rõ sơ hở dễ bị bác bỏ và giải pháp khắc phục (lập vi bằng Thừa phát lại, đề nghị Tòa thu thập chứng cứ, công chứng, sao kê có dấu...). \n"
            f"CHỈ TRẢ VỀ JSON HỢP LỆ (KHÔNG THÊM LỜI GIẢI THÍCH NGOÀI JSON) theo cấu trúc:\n"
            f"{{\n"
            f'  "overall_strength": "Vững chắc / Khá / Yếu / Cần bổ sung khẩn cấp",\n'
            f'  "average_grade": "A",\n'
            f'  "items": [\n'
            f'    {{\n'
            f'      "item": "Tên chứng cứ",\n'
            f'      "grade": "A",\n'
            f'      "probative_value": "Mô tả giá trị chứng minh",\n'
            f'      "vulnerability": "Sơ hở, rủi ro bị bác bỏ",\n'
            f'      "remedy": "Biện pháp củng cố / lập vi bằng / công chứng cụ thể"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "general_recommendations": "Chiến thuật củng cố hồ sơ chứng cứ tổng thể"\n'
            f"}}"
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            system_instruction="Bạn là Chuyên gia Giám định & Thẩm tra Chứng cứ Tố tụng hàng đầu Việt Nam thuộc Văn phòng Luật sư Huỳnh Nguyên Khang. Luôn phản hồi JSON hợp lệ.",
            temperature=0.2,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )
            data = self._extract_json_dict(response.text or "{}")
            items_list = [
                EvidenceAuditItem(
                    item=it.get("item", "Chứng cứ"),
                    grade=it.get("grade", "B"),
                    probative_value=it.get("probative_value", "Có giá trị tham khảo"),
                    vulnerability=it.get("vulnerability", "Chưa được công chứng hoặc lập vi bằng"),
                    remedy=it.get("remedy", "Lập vi bằng Thừa phát lại")
                )
                for it in data.get("items", [])
            ]

            return EvidenceAuditResponse(
                success=True,
                overall_strength=data.get("overall_strength", "Cần củng cố"),
                average_grade=data.get("average_grade", "B"),
                items=items_list,
                general_recommendations=data.get("general_recommendations", "Cần liên hệ Thừa phát lại hoặc đề nghị Tòa án thu thập chứng cứ để hoàn thiện hồ sơ."),
                model_used=used_model
            )
        except Exception as e:
            logger.error(f"Lỗi thẩm tra chứng cứ: {str(e)}")
            raise RuntimeError(f"Không thể thẩm tra chứng cứ: {str(e)}")

    async def generate_legal_petition(
        self,
        petition_type: str,
        plaintiff_info: dict,
        defendant_info: dict,
        facts: str,
        claims: str,
        evidence_list: Optional[str] = "",
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> PetitionGenerateResponse:
        """Soạn thảo văn bản tố tụng hoặc hành chính chuẩn mẫu biểu Việt Nam."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        pet_meta = next((p for p in PETITION_TYPES if p["id"] == petition_type), None)
        title = pet_meta["name"] if pet_meta else "ĐƠN KHỞI KIỆN / TỐ TỤNG"
        standard_form = pet_meta["standard_form"] if pet_meta else "Theo mẫu chuẩn"
        agency = pet_meta["agency"] if pet_meta else "Cơ quan có thẩm quyền"

        rag_query = f"{title} {facts[:200]} {claims[:200]}"
        rag_hits = rag_engine.search(rag_query, top_k=4)
        rag_context = ""
        if rag_hits:
            rag_context = "\n=== CĂN CỨ PHÁP LUẬT CHÍNH THỨC ĐỐI CHIẾU ===\n" + "\n".join([
                f"- Điều {h['article_number']} ({h['law_name']}): {h['article_title']}\n  Trích: {h['content'][:150]}..."
                for h in rag_hits
            ])

        prompt = (
            f"=== LỆNH SOẠN THẢO VĂN BẢN TỐ TỤNG / HÀNH CHÍNH ===\n"
            f"Loại văn bản: {title}\n"
            f"Biểu mẫu áp dụng: {standard_form}\n"
            f"Cơ quan kính gửi giải quyết: {agency}\n\n"
            f"=== THÔNG TIN BÊN LÀM ĐƠN / NGUYÊN ĐƠN ===\n"
            f"Họ và tên: {plaintiff_info.get('name', '...')}\n"
            f"Số CCCD/Căn cước: {plaintiff_info.get('id_number', '...')}\n"
            f"Địa chỉ thường trú / Nơi ở hiện tại: {plaintiff_info.get('address', '...')}\n"
            f"Số điện thoại liên hệ: {plaintiff_info.get('phone', '...')}\n\n"
            f"=== THÔNG TIN BÊN BỊ ĐƠN / BÊN BỊ TỐ CÁO / BÊN NHẬN THÔNG BÁO ===\n"
            f"Họ và tên / Tên tổ chức: {defendant_info.get('name', '...')}\n"
            f"Địa chỉ / Trụ sở: {defendant_info.get('address', '...')}\n"
            f"Số điện thoại (nếu có): {defendant_info.get('phone', '...')}\n\n"
            f"=== TÓM TẮT DIỄN BIẾN SỰ VIỆC ===\n{facts}\n\n"
            f"=== NỘI DUNG YÊU CẦU GIẢI QUYẾT ===\n{claims}\n\n"
            f"=== TÀI LIỆU, CHỨNG CỨ KÈM THEO ===\n{evidence_list or 'Bản sao CCCD, Hợp đồng, Giấy tờ chuyển khoản, Vi bằng...'}\n"
            f"{rag_context}\n\n"
            f"Hãy soạn thảo hoàn chỉnh toàn văn bản đơn theo đúng chuẩn thể thức văn bản hành chính Việt Nam (Nghị quyết 01/2017/NQ-HĐTP và Nghị định 30/2020/NĐ-CP). "
            f"Văn phong nghiêm trang, đanh thép, viện dẫn chính xác các điều luật có hiệu lực mới nhất."
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            system_instruction=PETITION_SYSTEM_PROMPT,
            temperature=0.2,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )
            return PetitionGenerateResponse(
                success=True,
                petition_type=petition_type,
                petition_title=title,
                content_markdown=response.text or "Không thể tạo nội dung đơn từ.",
                model_used=used_model,
                disclaimer=LEGAL_DISCLAIMER
            )
        except Exception as e:
            logger.error(f"Lỗi tạo đơn: {str(e)}")
            raise RuntimeError(f"Không thể soạn thảo đơn pháp lý: {str(e)}")

    async def audit_corporate_compliance(
        self,
        company_name: str,
        business_type: str,
        employee_count: int,
        industry: str,
        compliance_notes: str,
        custom_api_key: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> CorporateAuditResponse:
        """Khám sức khỏe pháp chế doanh nghiệp theo 8 trụ cột pháp lý 2026."""
        client = self._get_client(custom_api_key)
        model_name = self._resolve_model(model_override)

        prompt = (
            f"=== KHÁM SỨC KHỎE PHÁP CHẾ DOANH NGHIỆP 2026 ===\n"
            f"Tên doanh nghiệp: {company_name}\n"
            f"Mô hình công ty: {business_type}\n"
            f"Quy mô nhân sự: {employee_count} nhân sự\n"
            f"Ngành nghề kinh doanh: {industry}\n"
            f"Ghi chú tình trạng hiện tại: {compliance_notes}\n\n"
            f"Hãy thẩm định toàn diện rủi ro pháp lý theo đúng 8 TRỤ CỘT PHÁP CHẾ:\n"
            f"1. legal_entity (Pháp nhân & Giấy phép con - Luật Doanh nghiệp 2020)\n"
            f"2. labor_social (Lao động, Tiền lương & BHXH - BLLĐ 2019, Luật BHXH 2024 hiệu lực 2025)\n"
            f"3. contracts (Hợp đồng & Đối tác - BLDS 2015, Luật Thương mại 2005)\n"
            f"4. ip_brand (Sở hữu trí tuệ, Nhãn hiệu & Bí mật kinh doanh - Luật SHTT 2022)\n"
            f"5. tax_invoice (Thuế & Hóa đơn điện tử - Luật QLTH, NĐ 123/2020/NĐ-CP)\n"
            f"6. fire_environment (PCCC & Giấy phép Môi trường - Luật PCCC 2024, Luật BVMT 2020)\n"
            f"7. data_privacy (Bảo vệ dữ liệu cá nhân - Nghị định 13/2023/NĐ-CP)\n"
            f"8. cyber_ecommerce (TMĐT & Bản quyền số - Nghị định 52/2013, NĐ 85/2021)\n\n"
            f"CHỈ TRẢ VỀ JSON HỢP LỆ THEO CẤU TRÚC (status nhận 'compliant', 'warning', hoặc 'critical'):\n"
            f"{{\n"
            f'  "compliance_score": 75,\n'
            f'  "summary": "Tóm tắt tình trạng tuân thủ pháp luật tổng quan",\n'
            f'  "pillars": [\n'
            f'    {{\n'
            f'      "pillar_id": "legal_entity",\n'
            f'      "pillar_name": "Pháp nhân & Giấy phép con",\n'
            f'      "status": "warning",\n'
            f'      "risk_summary": "Rủi ro phát hiện",\n'
            f'      "remediation_action": "Phương án khắc phục khẩn cấp",\n'
            f'      "legal_basis": "Điều ... Luật ..."\n'
            f'    }}\n'
            f'  ]\n'
            f"}}"
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(
            system_instruction="Bạn là Giám đốc Pháp chế Cấp cao thuộc Văn phòng Cố vấn Pháp lý Huỳnh Nguyên Khang. Luôn thẩm định chuẩn xác và trả về JSON hợp lệ.",
            temperature=0.2,
            top_p=0.95,
        )

        try:
            response, used_model = self._generate_with_fallback(
                client=client,
                primary_model=model_name,
                contents=contents,
                config=config,
            )
            data = self._extract_json_dict(response.text or "{}")
            pillars_list = [
                CorporatePillarAudit(
                    pillar_id=p.get("pillar_id", "pillar"),
                    pillar_name=p.get("pillar_name", "Trụ cột pháp lý"),
                    status=p.get("status", "warning"),
                    risk_summary=p.get("risk_summary", "Cần rà soát"),
                    remediation_action=p.get("remediation_action", "Cập nhật hồ sơ"),
                    legal_basis=p.get("legal_basis", "Quy định pháp luật hiện hành")
                )
                for p in data.get("pillars", [])
            ]

            return CorporateAuditResponse(
                success=True,
                company_name=company_name,
                compliance_score=data.get("compliance_score", 70),
                summary=data.get("summary", "Đã hoàn thành rà soát pháp chế doanh nghiệp."),
                pillars=pillars_list,
                model_used=used_model
            )
        except Exception as e:
            logger.error(f"Lỗi khám sức khỏe pháp chế: {str(e)}")
            raise RuntimeError(f"Không thể thẩm định pháp chế doanh nghiệp: {str(e)}")

legal_service = GeminiLegalService()
