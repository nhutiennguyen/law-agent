# backend/core/rag_engine.py — Động cơ RAG truy xuất văn bản quy phạm pháp luật Việt Nam
# Hỗ trợ Namespace Isolation & Domain-Scoped Routing (Chống Loạn Thông Tin)

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set

logger = logging.getLogger("ai_lawyer.rag")

# Bản đồ ánh xạ tên viết tắt chuyên ngành của giới Luật sư Việt Nam sang law_id
LEGAL_ACRONYMS_MAP = {
    "blds": "blds_2015",
    "bld dân sự": "blds_2015",
    "dân sự": "blds_2015",
    "blhs": "blhs_2015",
    "hình sự": "blhs_2015",
    "bllđ": "bld_2019",
    "bld": "bld_2019",
    "lao động": "bld_2019",
    "lđđ": "ldd_2024",
    "đất đai": "ldd_2024",
    "nhà ở": "housing_law_2023",
    "lno": "housing_law_2023",
    "ldn": "ldn_2020",
    "doanh nghiệp": "ldn_2020",
    "lhngđ": "lhngd_2014",
    "lhngd": "lhngd_2014",
    "hôn nhân": "lhngd_2014",
    "gia đình": "lhngd_2014",
    "thương mại": "commercial_law_2005",
    "blttds": "blttds_2015",
    "tố tụng dân sự": "blttds_2015",
    "bltths": "bltths_2015",
    "tố tụng hình sự": "bltths_2015",
    "nghị định 100": "traffic_decree_100_123",
    "nđ 100": "traffic_decree_100_123",
    "nđ100": "traffic_decree_100_123",
    "nđ 123": "traffic_decree_100_123",
    "giao thông": "traffic_decree_100_123",
    "bhxh": "social_insurance_2024",
    "bảo hiểm xã hội": "social_insurance_2024",
    "thuế": "tax_property_laws",
    "thuế tncn": "tax_property_laws",
    "thuế nhà đất": "tax_property_laws",
    "án lệ": "supreme_court_precedents",
    "an le": "supreme_court_precedents",
    "tandtc": "supreme_court_precedents",
}

# Bản đồ phát hiện Domain theo từ khóa chuyên môn
DOMAIN_KEYWORDS = {
    "labor": [
        "sa thải", "đuổi việc", "nghỉ việc", "tiền lương", "hđlđ", "hợp đồng lao động", 
        "thử việc", "lao động", "trợ cấp thôi việc", "quấy rối", "chậm lương", "ngược đãi"
    ],
    "marriage_family": [
        "ly hôn", "kết hôn", "nuôi con", "tài sản chung", "vợ chồng", "cấp dưỡng", 
        "đơn phương ly hôn", "thuận tình", "con dưới 36 tháng", "chia tài sản", "hôn nhân"
    ],
    "criminal": [
        "lừa đảo", "chiếm đoạt", "trộm cắp", "cố ý gây thương tích", "tội phạm", "ở tù", 
        "hình sự", "cho vay lãi nặng", "tín dụng đen", "lạm dụng tín nhiệm", "hung khí", "thương tật"
    ],
    "land": [
        "sổ đỏ", "chuyển nhượng đất", "bán đất", "thu hồi đất", "bồi thường đất", "đất đai", 
        "quyền sử dụng đất", "đất không có giấy tờ", "tranh chấp đất", "giải tỏa"
    ],
    "corporate": [
        "cổ phần", "cổ đông", "vốn góp", "công ty tnhh", "đại diện pháp luật", "doanh nghiệp", 
        "chuyển nhượng vốn", "đại hội đồng cổ đông", "điều lệ công ty", "giám đốc"
    ],
    "civil": [
        "thừa kế", "di chúc", "đặt cọc", "phạt cọc", "vô hiệu", "hợp đồng thuê", "dân sự", 
        "chậm trả tiền", "lãi suất", "phạt vi phạm", "hàng thừa kế", "thời hiệu khởi kiện"
    ],
    "procedure": [
        "tạm giữ", "tạm giam", "người bào chữa", "luật sư bào chữa", "khởi tố", "chứng cứ", 
        "nghĩa vụ chứng minh", "tố tụng", "tòa án giải quyết"
    ],
    "commercial": [
        "thương mại", "phạt vi phạm 8%", "miễn trách nhiệm", "bất khả kháng"
    ],
    "housing": [
        "nhà ở", "thuê nhà ở", "chấm dứt thuê nhà", "đòi nhà"
    ],
    "traffic": [
        "nồng độ cồn", "thổi cồn", "tốc độ", "chạy quá tốc độ", "vượt đèn đỏ", "tước bằng lái", 
        "gplx", "giữ xe", "xe máy", "ô tô", "tai nạn giao thông", "nghị định 100", "nghị định 123", "khí thở"
    ],
    "social_insurance": [
        "bhxh", "bảo hiểm xã hội", "rút 1 lần", "rút một lần", "thai sản", "nghỉ sinh con", 
        "ốm đau", "hưu trí", "trợ cấp thất nghiệp", "đóng bảo hiểm", "sổ bảo hiểm"
    ],
    "tax": [
        "thuế", "thu nhập cá nhân", "thuế tncn", "giảm trừ gia cảnh", "người phụ thuộc", 
        "lũy tiến", "thuế bán đất", "thuế chuyển nhượng", "lệ phí trước bạ", "miễn thuế bán nhà"
    ],
    "precedents": [
        "án lệ", "án lệ 02", "án lệ 25", "án lệ 04", "nhờ đứng tên", "tiền lệ", "tòa án nhân dân tối cao", "phán quyết án lệ"
    ]
}

class LegalRAGEngine:
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "legal_store"
        else:
            self.data_dir = data_dir

        self.articles: List[Dict] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Tải toàn bộ các điều luật từ các file JSON trong data/legal_store/"""
        self.articles = []
        if not self.data_dir.exists():
            logger.warning(f"Thư mục dữ liệu luật không tồn tại: {self.data_dir}")
            return

        for json_file in sorted(self.data_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.articles.extend(data)
                    elif isinstance(data, dict):
                        self.articles.append(data)
            except Exception as e:
                logger.error(f"Lỗi tải file {json_file.name}: {str(e)}")

        logger.info(f"Đã nạp thành công {len(self.articles)} điều luật vào động cơ RAG.")

    def detect_intent(self, query_lower: str) -> Dict:
        """
        Nhận diện ý định pháp lý:
        1. Tên luật cụ thể được nhắc tới (explicit_law_id).
        2. Các lĩnh vực liên quan (detected_domains).
        """
        explicit_law_id = None
        for kw, law_id in LEGAL_ACRONYMS_MAP.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                explicit_law_id = law_id
                break

        detected_domains: Set[str] = set()
        for dom, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    detected_domains.add(dom)

        return {
            "explicit_law_id": explicit_law_id,
            "detected_domains": list(detected_domains)
        }

    def search(self, query: str, category: Optional[str] = None, domain: Optional[str] = None, top_k: int = 4) -> List[Dict]:
        """
        Tìm kiếm các Điều luật liên quan nhất dựa trên Scoped Hybrid Score:
        - Phân giải Namespace & Acronyms
        - Tự động nhận diện Domain để chống nhiễu (Domain Boost)
        - So khớp chính xác số điều & từ khóa
        """
        if not self.articles or not query.strip():
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))
        query_digits = set(re.findall(r"\d+", query_lower))

        # Phân tích ý định & miền pháp luật
        intent = self.detect_intent(query_lower)
        explicit_law_id = intent["explicit_law_id"]
        detected_domains = intent["detected_domains"]
        if domain and domain not in detected_domains:
            detected_domains.append(domain)

        # Kiểm tra xem người dùng có nhắc đến số điều luật cụ thể không (ví dụ: "điều 35", "điều 174", "328")
        article_matches = re.findall(r"điều\s+(\d+)", query_lower)
        article_targets = [f"điều {num}" for num in article_matches]

        scored_articles = []

        for item in self.articles:
            score = 0
            item_law_id = item.get("law_id", "").lower()
            item_domain = item.get("domain", "").lower()
            art_num_lower = item.get("article_number", "").lower()
            art_title_lower = item.get("article_title", "").lower()
            law_name_lower = item.get("law_name", "").lower()
            content_lower = item.get("content", "").lower()
            keywords = [kw.lower() for kw in item.get("keywords", [])]

            # --- A. TRỌNG SỐ MIỀN & TÊN LUẬT ĐÍCH DANH (CHỐNG LOẠN THÔNG TIN) ---
            if explicit_law_id:
                if item_law_id == explicit_law_id:
                    score += 65
                else:
                    score -= 30  # Phạt nặng các luật khác khi người dùng đã chỉ đích danh tên luật!

            if item_domain in detected_domains:
                score += 45

            # --- B. TRÙNG KHỚP SỐ ĐIỀU LUẬT ---
            for target in article_targets:
                if target == art_num_lower:
                    score += 60

            art_digits = set(re.findall(r"\d+", art_num_lower))
            if query_digits and art_digits and query_digits.intersection(art_digits):
                score += 40

            if query_lower in art_num_lower:
                score += 35

            if query_lower in art_title_lower:
                score += 30

            # --- C. KHỚP TỪ KHÓA CHUYÊN NGÀNH ---
            for kw in keywords:
                if kw in query_lower:
                    score += 20
                else:
                    kw_tokens = set(kw.split())
                    matched_tokens = kw_tokens.intersection(query_words)
                    if len(matched_tokens) >= 2:
                        score += 10

            # --- D. KHỚP TIÊU ĐỀ & NỘI DUNG ---
            title_tokens = set(re.findall(r"\w+", art_title_lower))
            matched_title = title_tokens.intersection(query_words)
            score += len(matched_title) * 4

            content_tokens = set(re.findall(r"\w+", content_lower))
            matched_content = content_tokens.intersection(query_words)
            score += min(len(matched_content) * 0.5, 12)

            if score > 5:
                scored_articles.append({
                    **item,
                    "relevance_score": round(score, 1)
                })

        # Sắp xếp theo điểm giảm dần và lấy top_k
        scored_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_articles[:top_k]

    def get_article(self, law_id: str, article_number: str) -> Optional[Dict]:
        """Tra cứu chính xác một điều luật theo law_id và article_number."""
        target_num = article_number.strip().lower()
        for item in self.articles:
            if item.get("law_id") == law_id and item.get("article_number", "").lower() == target_num:
                return item
        return None

    def list_all(self) -> List[Dict]:
        """Danh sách tóm tắt toàn bộ các điều luật đã nạp."""
        return [
            {
                "article_id": item.get("article_id"),
                "law_id": item.get("law_id"),
                "law_name": item.get("law_name"),
                "domain": item.get("domain"),
                "status": item.get("status", "HIỆU LỰC"),
                "article_number": item.get("article_number"),
                "article_title": item.get("article_title"),
                "official_source": item.get("official_source")
            }
            for item in self.articles
        ]

rag_engine = LegalRAGEngine()
