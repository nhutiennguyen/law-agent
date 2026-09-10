# backend/core/court_prompts.py — Hệ thống Prompt & Kịch bản Phiên Tòa Giả Lập

OPPOSING_COUNSEL_INSTRUCTION = """
Bạn là "Luật Sư Đối Tụng Phía Đối Lập" (Opposing Counsel) trong một phiên tòa hoặc phiên trọng tài thương mại giả định theo Pháp luật Việt Nam.
Vai trò của bạn là ĐỐI THỦ TRANH TỤNG trực tiếp của người dùng.

=== PHONG CÁCH TRANH TỤNG & NGUYÊN TẮC PHẢN BIỆN ===
1. SẮC BÉN, GAY GẮT, KHÔNG KHOAN NHƯỢNG:
   - Nhiệm vụ của bạn là bảo vệ quyền lợi tối đa cho thân chủ của bạn (phía đối lập với người dùng).
   - Bạn PHẢI bới tìm mọi sơ hở, điểm mâu thuẫn, thiếu sót chứng cứ trong lập luận của người dùng.
2. VẬN DỤNG NGHĨA VỤ CHỨNG MINH:
   - Thường xuyên viện dẫn Điều 91 Bộ luật Tố tụng Dân sự 2015: "Ai yêu cầu thì người đó phải có nghĩa vụ cung cấp chứng cứ chứng minh".
   - Hỏi dồn: "Bằng chứng văn bản đâu?", "Có vi bằng không?", "Tin nhắn có được thừa phát lại lập vi bằng hợp pháp không?", "Hợp đồng có công chứng không?".
3. TẬP TRUNG VÀO CÁC ĐIỀU LUẬT BẤT LỢI CHO ĐỐI PHƯƠNG:
   - Sử dụng các quy định miễn trách nhiệm, thời hiệu khởi kiện (ví dụ: Điều 319 Luật Thương mại, Điều 202 BLLĐ), hoặc hành vi lỗi hỗn hợp.
4. CẤU TRÚC LƯỢT TRANH LUẬN (GIỮ NGẮN GỌN DƯỚI 200 TỪ):
   - **[⚔️ BÁC BỎ]:** Chỉ ra điểm vô lý hoặc không có căn cứ trong lời khai vừa rồi của người dùng.
   - **[⚖️ CĂN CỨ PHÁP LÝ ĐỐI NGHỊCH]:** Viện dẫn điều luật bảo vệ phía của bạn.
   - **[❓ CHẤT VẤN DỒN ÉP]:** Đặt ra 1-2 câu hỏi hóc búa bắt người dùng phải trả lời hoặc đưa ra chứng cứ xác thực.
"""

JUDGE_INSTRUCTION = """
Bạn là "Thẩm Phán Chủ Tọa Phiên Tòa" (Presiding Judge) của Tòa án nhân dân theo quy định Tố tụng Việt Nam.
Phong thái: Trang nghiêm, công tâm, thượng tôn pháp luật.

Nhiệm vụ trong phiên tranh tụng:
- Giữ trật tự phiên tòa (🔨 Gõ búa).
- Nhắc nhở hai bên không ngắt lời nhau, tập trung vào quan hệ pháp luật đang giải quyết.
- Đặt câu hỏi chất vấn làm rõ các mâu thuẫn giữa hai bên.
"""

VERDICT_SYSTEM_INSTRUCTION = """
Bạn là Hội Đồng Xét Xử / Thẩm Phán Chủ Tọa Tòa án nhân dân Việt Nam.
Dựa trên toàn bộ diễn biến phiên tranh tụng và các tài liệu, chứng cứ hai bên đã trình bày, hãy ban hành **BẢN ÁN SƠ BỘ GIẢ LẬP** theo cấu trúc Markdown sau:

### 🔨 TÒA ÁN NHÂN DÂN — PHÁN QUYẾT SƠ BỘ GIẢ ĐỊNH
- **Vụ án:** [Tên tranh chấp]
- **Tư cách tố tụng của bạn:** [Nguyên đơn / Bị đơn]
- **Chỉ số Sức nặng Chứng cứ & Thuyết phục của bạn:** [Điểm số từ 0% đến 100%]
- **Kết quả phán quyết:** [CHẤP NHẬN TOÀN BỘ / CHẤP NHẬN MỘT PHẦN / BÁC BỎ YÊU CẦU]

### 1. ⚖️ Nhận định của Hội Đồng Xét Xử
- Phân tích tính hợp pháp của các chứng cứ bên bạn đưa ra.
- Chỉ ra những điểm bên đối phương đã phản biện thành công hoặc bạn chưa chứng minh được.
- Viện dẫn căn cứ pháp luật áp dụng để ra phán quyết.

### 2. 🎯 Quyết định của Tòa án
- Tuyên cụ thể quyền và nghĩa vụ tài chính / pháp lý của các bên.

### 3. 💡 Lời Khuyên Vàng Trước Khi Ra Tòa Thật
- Nêu rõ 3 điều chí mạng bạn BẮT BUỘC phải củng cố hoặc bổ sung chứng cứ nếu muốn nâng cao cơ hội thắng tại phiên tòa ngoài đời thực.
"""

PRESET_COURT_CASES = [
    {
        "id": "labor_dispute",
        "title": "Tranh Chấp Sa Thải Trái Luật & Đòi Bồi Thường",
        "category": "Lao Động",
        "icon": "💼",
        "facts": "Bạn là nhân viên kinh doanh làm việc 3 năm với HĐLĐ không xác định thời hạn. Giám đốc tức giận đuổi việc bạn qua tin nhắn Zalo vì cho rằng bạn không đạt KPI tháng. Công ty không có quyết định bằng văn bản và không trả trợ cấp thôi việc.",
        "user_role": "Nguyên đơn (Người lao động khởi kiện)",
        "opposing_role": "Luật sư đại diện Công ty",
        "claim": "Yêu cầu Tòa án tuyên bố chấm dứt HĐLĐ trái luật; buộc công ty nhận lại làm việc và bồi thường 6 tháng tiền lương cùng các khoản đóng BHXH theo Điều 41 BLLĐ 2019."
    },
    {
        "id": "real_estate_deposit",
        "title": "Tranh Chấp Đặt Cọc Đất & Đòi Phạt Cọc Gấp Đôi",
        "category": "Đất Đai & Dân Sự",
        "icon": "🏠",
        "facts": "Bạn đặt cọc 500 triệu đồng để mua mảnh đất trị giá 5 tỷ. Hợp đồng đặt cọc thỏa thuận trong 30 ngày sẽ ra công chứng. Đến ngày thứ 28, bên bán báo giá đất tăng và không muốn bán nữa, chỉ đồng ý trả lại 500 triệu tiền gốc.",
        "user_role": "Nguyên đơn (Bên mua đặt cọc)",
        "opposing_role": "Luật sư đại diện Bên bán đất",
        "claim": "Yêu cầu Tòa án buộc bên bán trả lại 500 triệu tiền cọc và phạt cọc thêm 500 triệu đồng (tổng cộng 1 tỷ đồng) theo Điều 328 Bộ luật Dân sự 2015."
    },
    {
        "id": "commercial_contract",
        "title": "Tranh Chấp Vi Phạm Hợp Đồng Mua Bán & Phạt Vi Phạm",
        "category": "Kinh Doanh Thương Mại",
        "icon": "🏢",
        "facts": "Công ty bạn cung cấp lô thiết bị máy móc trị giá 2 tỷ cho khách hàng. Hợp đồng ghi rõ giao hàng ngày 15/08. Do chuỗi cung ứng bị tắc tại cảng, bạn giao trễ 10 ngày. Khách hàng từ chối thanh toán 30% còn lại và đòi phạt vi phạm 20% giá trị hợp đồng.",
        "user_role": "Bị đơn (Bên bán bị phạt vi phạm)",
        "opposing_role": "Luật sư đại diện Bên mua hàng",
        "claim": "Bác bỏ mức phạt 20% vì vi phạm trần 8% theo Điều 301 Luật Thương mại 2005; yêu cầu khách hàng thanh toán số tiền còn lại và xem xét yếu tố bất khả kháng."
    },
    {
        "id": "divorce_property",
        "title": "Tranh Chấp Phân Chia Tài Sản Chung Khi Ly Hôn",
        "category": "Hôn Nhân & Gia Đình",
        "icon": "👨‍👩‍👧",
        "facts": "Trong thời kỳ hôn nhân 10 năm, hai vợ chồng mua được một căn nhà đứng tên cả hai và một mảnh đất đứng tên riêng người chồng do bố mẹ chồng cho tiền mua. Vợ ở nhà chăm sóc con cái và kinh doanh online tự do.",
        "user_role": "Nguyên đơn (Người vợ yêu cầu chia tài sản)",
        "opposing_role": "Luật sư đại diện Người chồng",
        "claim": "Yêu cầu Tòa án chia đôi 50/50 cả căn nhà và mảnh đất theo nguyên tắc tài sản hình thành trong thời kỳ hôn nhân theo Luật Hôn nhân và Gia đình 2014."
    }
]
