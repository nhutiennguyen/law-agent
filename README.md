# ⚖️ AI Luật Sư — Cố Vấn Pháp Lý Trí Tuệ Nhân Tạo (Legal AI Advisor)

> Nền tảng Cố vấn Pháp lý Trí tuệ Nhân tạo chuyên sâu theo Hệ thống Pháp luật Việt Nam. Ứng dụng mô hình ngôn ngữ lớn **Google Gemini (2.5 Flash / 2.5 Pro)** với tư duy pháp lý chặt chẽ theo **quy chuẩn 4 bước của Luật sư** kết hợp **Động cơ RAG đối chiếu trực tiếp từ Cơ sở dữ liệu Quốc gia về Văn bản Pháp luật (vbpl.vn)**.

---

## 🌟 ĐẶC ĐIỂM NỔI BẬT

1. **Chuẩn mực tư vấn 4 bước (RAG Verified):**
   - **Bước 1:** Tóm tắt tình huống & Nhận diện bản chất quan hệ pháp lý.
   - **Bước 2:** Căn cứ pháp lý áp dụng (Tự động trích dẫn và gắn link điều luật gốc từ `vbpl.vn`).
   - **Bước 3:** Phân tích quyền, nghĩa vụ & Đánh giá rủi ro thực tế.
   - **Bước 4:** Khuyến nghị hành động & Lộ trình thực tế.
2. **📑 Rà Soát & Thẩm Định Hợp Đồng (Contract Reviewer PRO):**
   - Hỗ trợ kéo thả hoặc chọn file: **PDF** (chuẩn vector & scan), **Word (.docx)**, **Text (.txt)**, **Ảnh hợp đồng**.
   - Bóc tách theo góc nhìn chủ thể bảo vệ quyền lợi (Bên Mua/Bán, Thuê/Cho thuê, Lao động...).
   - Xuất Ma trận Rủi ro 5 phần & Bảng Điều khoản Bất lợi / Phương án sửa đổi (Redline Table).
3. **🔨 Đấu Trường Phiên Tòa Giả Lập (AI Moot Court LIVE):**
   - Đối chất tranh tụng thời gian thực với **Luật sư đối tụng** (`⚔️`) sắc sảo, vạch trần lỗ hổng chứng cứ.
   - **Hội đồng xét xử / Thẩm phán** (`⚖️`) điều hành phiên xử, đánh giá vi phạm tố tụng.
   - **Thước đo thuyết phục (Persuasion Meter)** biến động theo từng luận điểm.
   - Tuyên án bản án sơ thẩm đầy đủ phần: Nhận định của Tòa, Quyết định và Án phí.
4. **📚 Cơ Sở Dữ Liệu Pháp Luật Quốc Gia (vbpl.vn):**
   - Tích hợp sẵn các đạo luật quan trọng: Bộ luật Dân sự 2015, Bộ luật Lao động 2019, Luật Đất đai 2024 (hiệu lực 01/08/2024), Luật Nhà ở 2023, Luật Thương mại 2005, Bộ luật Tố tụng Dân sự 2015.
   - Thanh tra cứu nhanh trực tiếp trên Sidebar và Modal xem chi tiết nguyên văn điều luật.
5. **Thiết kế Legal-Tech đẳng cấp:** Giao diện tối màu sang trọng (Dark Slate Navy `#0B0F19` + Metallic Gold `#D4AF37`), hỗ trợ Markdown, bảng biểu, trích dẫn pháp lý chuyên nghiệp.

---

## 📂 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
c:\Users\Admin\Documents\ai-lawyer\
├── .agents/
│   └── rules/
│       └── legal_agent_rules.md      # Quy tắc workspace cho Antigravity IDE
├── docs/
│   ├── ARCHITECTURE.md               # Thiết kế kiến trúc hệ thống chi tiết & lộ trình
│   └── LEGAL_KNOWLEDGE_BASE.md       # Cẩm nang dữ liệu văn bản luật RAG
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                 # REST API (Chat, Review Contract, Moot Court, Laws Search)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Quản lý cấu hình & biến môi trường
│   │   ├── contract_parser.py        # Parser đa định dạng (PDF, DOCX, TXT, OCR)
│   │   ├── court_prompts.py          # Đối tụng ⚔️ & Thẩm phán ⚖️ Phiên tòa giả lập
│   │   ├── gemini_service.py         # Kết nối Gemini qua Google GenAI SDK & RAG injection
│   │   ├── legal_prompts.py          # System Prompt & 4-Step Legal Framework
│   │   └── rag_engine.py             # Động cơ RAG đối chiếu CSDL vbpl.vn
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                # Pydantic Schemas
│   ├── main.py                       # Điểm khởi chạy FastAPI & StaticFiles mount
│   └── requirements.txt              # Danh sách dependencies
├── frontend/
│   ├── css/
│   │   └── styles.css                # Hệ thống CSS Design System (Legal-Tech theme)
│   ├── js/
│   │   └── app.js                    # Controller 3-trong-1 (Chat, Review, Moot Court, RAG)
│   ├── assets/                       # Biểu tượng & hình ảnh
│   └── index.html                    # Giao diện Web Canvas tích hợp đầy đủ các chế độ
├── data/
│   ├── legal_store/                  # CSDL Văn bản luật quốc gia chính thức (vbpl.vn)
│   │   ├── labor_code_2019.json      # Bộ luật Lao động 2019
│   │   ├── civil_code_2015.json      # Bộ luật Dân sự 2015
│   │   ├── land_law_2024.json        # Luật Đất đai 2024 (mới nhất)
│   │   ├── housing_law_2023.json     # Luật Nhà ở 2023
│   │   ├── commercial_law_2005.json  # Luật Thương mại 2005
│   │   └── civil_procedure_code_2015.json # Bộ luật Tố tụng Dân sự 2015
│   └── raw_laws/                     # Kho văn bản luật thô
├── .env.example                      # File mẫu cấu hình biến môi trường
├── README.md                         # Tài liệu hướng dẫn sử dụng (file này)
└── RULES.md                          # Bộ quy tắc quản trị, chuẩn mực code & đạo đức AI
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY NHANH

### Bước 1: Mở Workspace trong Antigravity IDE
Vào **File ➔ Open Folder...** và chọn thư mục:
`C:\Users\Admin\Documents\ai-lawyer`

### Bước 2: Cài đặt thư viện phụ thuộc
Mở terminal trong thư mục `ai-lawyer` và chạy:
```powershell
pip install -r backend/requirements.txt
```

### Bước 3: Cấu hình Gemini API Key
Bạn có thể cấu hình bằng 1 trong 2 cách:
* **Cách 1 (File `.env`):** Tạo file `.env` bằng cách copy từ `.env.example`:
  ```powershell
  copy .env.example .env
  ```
  Sau đó mở file `.env` và điền khóa:
  ```env
  GEMINI_API_KEY=AIzaSy...
  ```
* **Cách 2 (Trên giao diện Web):** Khởi động web và bấm vào nút **⚙️ Cài đặt API Key** ở góc dưới bên trái để nhập trực tiếp.

### Bước 4: Khởi động Web Server
Chạy lệnh:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Bước 5: Trải nghiệm ứng dụng
Mở trình duyệt bất kỳ (Chrome, Edge) và truy cập:
👉 **http://127.0.0.1:8000**

---

## 📜 QUY CHUẨN PHÁP LÝ & ĐẠO ĐỨC
Vui lòng đọc kỹ file [RULES.md](RULES.md) trước khi phát triển thêm tính năng hoặc chỉnh sửa mã nguồn. Mọi ý kiến do AI cung cấp phải luôn đính kèm tuyên bố miễn trừ trách nhiệm pháp lý.
