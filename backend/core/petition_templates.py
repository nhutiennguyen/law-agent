# backend/core/petition_templates.py — Hệ thống Biểu mẫu Đơn từ Tố tụng & Hành chính chuẩn TANDTC
# Áp dụng:
# 1. Đơn Khởi Kiện Dân Sự: Mẫu số 23-DS (Ban hành kèm theo Nghị quyết số 01/2017/NQ-HĐTP của Hội đồng Thẩm phán TANDTC)
# 2. Đơn Tố Giác Tội Phạm: Theo Bộ luật Tố tụng Hình sự 2015 & Thông tư liên tịch 01/2017
# 3. Đơn Thuận Tình Ly Hôn: Mẫu đơn yêu cầu giải quyết việc dân sự (NQ 01/2017/NQ-HĐTP) & Luật HNGĐ 2014
# 4. Thông Báo Đòi Nợ & Thực Hiện Hợp Đồng: Theo chuẩn Bộ luật Dân sự 2015
# 5. Đơn Khiếu Nại Quyết Định Hành Chính: Theo Luật Khiếu nại 2011 & Luật Đất đai

PETITION_TYPES = [
    {
        "id": "civil_lawsuit",
        "name": "Đơn Khởi Kiện Dân Sự / Kinh Tế",
        "icon": "⚖️",
        "standard_form": "Mẫu số 23-DS (Nghị quyết số 01/2017/NQ-HĐTP)",
        "agency": "Tòa án Nhân dân cấp có thẩm quyền (Quận/Huyện hoặc Tỉnh/TP)",
        "description": "Dùng khởi kiện đòi nợ, tranh chấp hợp đồng mua bán, thuê nhà, bồi thường thiệt hại, tranh chấp quyền sử dụng đất."
    },
    {
        "id": "criminal_report",
        "name": "Đơn Tố Giác / Tố Cáo Tội Phạm",
        "icon": "🚔",
        "standard_form": "Theo Bộ luật Tố tụng Hình sự 2015",
        "agency": "Cơ quan Cảnh sát Điều tra Công an cấp Quận/Huyện/Tỉnh hoặc Viện Kiểm sát",
        "description": "Dùng khi bị lừa đảo chiếm đoạt tài sản (Điều 174 BLHS), lạm dụng tín nhiệm (Điều 175 BLHS), cho vay lãi nặng, đe dọa bạo lực."
    },
    {
        "id": "mutual_divorce",
        "name": "Đơn Yêu Cầu Công Nhận Thuận Tình Ly Hôn",
        "icon": "💔",
        "standard_form": "Mẫu đơn yêu cầu việc dân sự theo Luật HNGĐ 2014 & NQ 01/2017",
        "agency": "Tòa án Nhân dân nơi cư trú của một trong hai vợ chồng",
        "description": "Dùng khi hai vợ chồng đồng thuận chấm dứt hôn nhân, đã thỏa thuận xong quyền nuôi con và phân chia tài sản chung."
    },
    {
        "id": "debt_notice",
        "name": "Thông Báo Đòi Nợ & Cảnh Báo Khởi Kiện",
        "icon": "📜",
        "standard_form": "Văn bản đôn đốc thực hiện nghĩa vụ theo Bộ luật Dân sự 2015",
        "agency": "Gửi trực tiếp cho bên nợ/bên vi phạm hợp đồng (qua Bưu điện bảo đảm có báo phát)",
        "description": "Dùng tạo áp lực pháp lý bắt buộc bên vi phạm thanh toán nợ trước khi chính thức nộp đơn ra Tòa hoặc Công an."
    },
    {
        "id": "admin_complaint",
        "name": "Đơn Khiếu Nại Quyết Định Hành Chính (Đất đai, Thu phạt)",
        "icon": "🏛️",
        "standard_form": "Theo quy định Luật Khiếu nại 2011",
        "agency": "Chủ tịch UBND hoặc Người đứng đầu cơ quan ban hành quyết định hành chính",
        "description": "Khiếu nại quyết định thu hồi đất, bồi thường tái định cư, xử phạt vi phạm hành chính, cưỡng chế sai luật."
    }
]

PETITION_SYSTEM_PROMPT = """
Bạn là "Chuyên Gia Soạn Thảo Văn Bản Tố Tụng & Hành Chính Cấp Cao" thuộc Văn phòng Cố vấn Pháp lý Huỳnh Nguyên Khang.
Nhiệm vụ của bạn là tiếp nhận dữ kiện của người dùng và soạn thảo một bản ĐƠN TỐ TỤNG / THÔNG BÁO PHÁP LÝ hoàn chỉnh, chuẩn xác 100% về mặt biểu mẫu, văn phong đanh thép, viện dẫn chính xác các Điều khoản pháp luật hiện hành và sẵn sàng để in ra ký tên nộp cơ quan có thẩm quyền.

=== TIÊU CHUẨN SOẠN THẢO BẮT BUỘC (MARKDOWN CHUẨN VĂN BẢN HÀNH CHÍNH) ===
1. QUỐC HIỆU & TIÊU NGỮ:
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
-----------------

2. TIÊU ĐỀ ĐƠN:
Viết IN HOA toàn bộ (ví dụ: ĐƠN KHỞI KIỆN, ĐƠN TỐ GIÁC TỘI PHẠM, ĐƠN YÊU CẦU CÔNG NHẬN THUẬN TÌNH LY HÔN).

3. KÍNH GỬI:
Chỉ định rõ ràng cơ quan có thẩm quyền thụ lý giải quyết (ví dụ: "Kính gửi: Tòa án nhân dân quận/huyện...").

4. THÔNG TIN CÁC BÊN:
Ghi rõ họ tên, năm sinh, số CCCD/Căn cước/VNeID, địa chỉ thường trú, chỗ ở hiện nay và số điện thoại liên hệ.

5. NỘI DUNG SỰ VIỆC (RÀNH MẠCH, THEO TRÌNH TỰ THỜI GIAN):
Tóm tắt ngắn gọn nhưng đanh thép: Ai, ngày nào, thỏa thuận gì, vi phạm ra sao, gây thiệt hại bao nhiêu tiền.

6. CĂN CỨ PHÁP LUẬT VIỆN DẪN:
Trích dẫn chính xác Điều khoản của Bộ luật Dân sự, Bộ luật Tố tụng Dân sự, Bộ luật Hình sự, Luật Đất đai hoặc Luật Hôn nhân Gia đình liên quan trực tiếp.

7. YÊU CẦU CỤ THỂ ĐỀ NGHỊ CƠ QUAN THẨM QUYỀN GIẢI QUYẾT:
Liệt kê từng yêu cầu rõ ràng (Ví dụ: Buộc thanh toán tiền gốc và tiền lãi, Buộc bồi thường thiệt hại, Khởi tố vụ án hình sự, Giao con cho ai trực tiếp nuôi dưỡng...).

8. TÀI LIỆU, CHỨNG CỨ KÈM THEO ĐƠN (DANH MỤC CHỨNG CỨ):
Liệt kê chi tiết bản sao công chứng CCCD, Hợp đồng, Giấy vay tiền, Sao kê chuyển khoản ngân hàng, Vi bằng...

9. PHẦN KÝ TÊN CỦA NGƯỜI LÀM ĐƠN.
"""
