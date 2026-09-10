# LEGAL_KNOWLEDGE_BASE.md — Cẩm Nang Quản Trị Kho Tri Thức Pháp Luật

Tài liệu hướng dẫn cách tổ chức, chuẩn bị và nạp dữ liệu văn bản pháp luật vào hệ thống AI Lawyer để chuẩn bị cho giai đoạn tích hợp RAG (Retrieval-Augmented Generation).

---

## 1. CÁC BỘ LUẬT TRỌNG TÂM CẦN NẠP

| Lĩnh vực | Văn bản quy phạm pháp luật chính | Mục tiêu tư vấn |
| :--- | :--- | :--- |
| **Lao động** | • Bộ luật Lao động 2019 (45/2019/QH14)<br>• Nghị định 12/2022/NĐ-CP (Xử phạt vi phạm hành chính lao động)<br>• Luật Bảo hiểm xã hội | Tiền lương, chậm trả lương, đơn phương chấm dứt HĐLĐ, sa thải, thai sản, trợ cấp thôi việc. |
| **Dân sự & Hợp đồng** | • Bộ luật Dân sự 2015 (91/2015/QH13)<br>• Luật Thương mại 2005 | Đặt cọc, phạt vi phạm hợp đồng, bồi thường thiệt hại ngoài hợp đồng, vay nợ, thừa kế. |
| **Đất đai & Bất động sản** | • Luật Đất đai 2024 (31/2024/QH15)<br>• Luật Nhà ở 2023 (27/2023/QH15)<br>• Luật Kinh doanh Bất động sản 2023 | Tranh chấp ranh giới, cấp sổ đỏ, hợp đồng mua bán căn hộ/nhà ở, đặt cọc mua đất. |
| **Doanh nghiệp & Thuế** | • Luật Doanh nghiệp 2020 (59/2020/QH14)<br>• Luật Đầu tư 2020<br>• Luật Quản lý Thuế | Thành lập công ty, chuyển nhượng phần vốn góp, nghĩa vụ của người đại diện pháp luật. |
| **Hôn nhân & Gia đình** | • Luật Hôn nhân và Gia đình 2014 | Ly hôn, phân chia tài sản chung/riêng, quyền nuôi con, cấp dưỡng. |

---

## 2. QUY TRÌNH CHUẨN BỊ VĂN BẢN (DATA PIPELINE)

Để AI có thể trích dẫn chính xác và không bị nhầm lẫn điều khoản:
1. **Nguồn dữ liệu:** Chỉ thu thập văn bản từ các nguồn chính thống (Cơ sở dữ liệu quốc gia về văn bản pháp luật `vbpl.vn`, Cổng thông tin điện tử Chính phủ, Thư viện Pháp luật).
2. **Định dạng lưu trữ (`data/raw_laws/`):** Lưu dạng Markdown hoặc Text sạch, mỗi chương/mục/điều có tiêu đề rõ ràng:
   ```markdown
   # BỘ LUẬT LAO ĐỘNG 2019 (45/2019/QH14)
   
   ## Điều 35. Quyền đơn phương chấm dứt hợp đồng lao động của người lao động
   1. Người lao động có quyền đơn phương chấm dứt hợp đồng lao động nhưng phải báo trước cho người sử dụng lao động như sau:
   a) Ít nhất 45 ngày nếu làm việc theo hợp đồng lao động không xác định thời hạn;
   ...
   ```
3. **Phân đoạn (Chunking Strategy):** Khi làm RAG, mỗi chunk tối ưu nên chứa trọn vẹn **1 Điều luật** kèm theo metadata: Tên văn bản, Số hiệu, Chương, Điều, Từ khóa chính.
