# backend/core/doc_exporter.py — Xuất Báo cáo Thẩm định Hợp đồng & Ý kiến Pháp lý ra file Word (.DOCX)

import io
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# Bảng màu Legal-Tech chuẩn mực
COLOR_NAVY = RGBColor(11, 24, 56)      # Xanh Navy đậm
COLOR_GOLD = RGBColor(184, 134, 11)    # Vàng kim Amber
COLOR_GRAY = RGBColor(90, 90, 90)      # Xám trung tính
COLOR_RED = RGBColor(180, 40, 40)      # Đỏ cảnh báo

def _set_cell_background(cell, fill_hex: str):
    """Thiết lập màu nền cho ô trong bảng docx."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Thiết lập lề trong của ô bảng."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def _add_header_banner(doc: docx.Document):
    """Tạo phần tiêu ngữ và nhận diện thương hiệu chuẩn văn phòng luật sư."""
    header_table = doc.add_table(rows=1, cols=2)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False

    # Cột trái: Thương hiệu AI Luật sư & Người sáng lập
    cell_left = header_table.cell(0, 0)
    cell_left.width = Inches(3.6)
    p_left = cell_left.paragraphs[0]
    p_left.paragraph_format.space_after = Pt(2)
    p_left.paragraph_format.line_spacing = 1.15
    run1 = p_left.add_run("VĂN PHÒNG CỐ VẤN PHÁP LÝ AI\n")
    run1.font.size = Pt(9.5)
    run1.font.bold = True
    run1.font.color.rgb = COLOR_NAVY

    run2 = p_left.add_run("HUỲNH NGUYÊN KHANG\n")
    run2.font.size = Pt(11)
    run2.font.bold = True
    run2.font.color.rgb = COLOR_GOLD

    run3 = p_left.add_run("Người sáng lập & Bản quyền: Bố Bảo\n")
    run3.font.size = Pt(8.5)
    run3.font.italic = True
    run3.font.color.rgb = COLOR_GRAY

    run_sub = p_left.add_run("— Hotline AI: 24/7 —")
    run_sub.font.size = Pt(8)
    run_sub.font.color.rgb = COLOR_GRAY

    # Cột phải: Quốc hiệu & Tiêu ngữ
    cell_right = header_table.cell(0, 1)
    cell_right.width = Inches(3.4)
    p_right = cell_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_right.paragraph_format.space_after = Pt(2)
    p_right.paragraph_format.line_spacing = 1.15

    r_qh = p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    r_qh.font.size = Pt(9.5)
    r_qh.font.bold = True
    r_qh.font.color.rgb = COLOR_NAVY

    r_tn = p_right.add_run("Độc lập - Tự do - Hạnh phúc\n")
    r_tn.font.size = Pt(10)
    r_tn.font.bold = True
    r_tn.font.color.rgb = COLOR_GOLD

    r_line = p_right.add_run("--------------------------")
    r_line.font.size = Pt(8)
    r_line.font.color.rgb = COLOR_GRAY

    # Đường phân cách ngang
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(4)
    p_div.paragraph_format.space_after = Pt(14)
    run_div = p_div.add_run("_________________________________________________________________________________")
    run_div.font.size = Pt(8)
    run_div.font.color.rgb = COLOR_GOLD

def _add_markdown_content_to_doc(doc: docx.Document, text: str):
    """Phân tích văn bản Markdown cơ bản và chuyển đổi thành typography của Docx."""
    lines = text.split('\n')
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # Kiểm tra xem có phải dòng bảng Markdown | a | b |
        if stripped.startswith('|') and stripped.endswith('|'):
            # Bỏ qua dòng phân cách |---|---|
            if re.match(r'^\|[\s\:\-\|]+\|$', stripped):
                continue
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table and table_rows:
            # Render bảng đã tích lũy
            _render_parsed_table(doc, table_rows)
            table_rows = []
            in_table = False

        if not stripped:
            continue

        # Tiêu đề cấp 1 (# Title)
        if stripped.startswith('# '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(stripped[2:])
            r.font.size = Pt(14)
            r.font.bold = True
            r.font.color.rgb = COLOR_NAVY
        # Tiêu đề cấp 2 (## Subtitle)
        elif stripped.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(11)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(stripped[3:])
            r.font.size = Pt(12.5)
            r.font.bold = True
            r.font.color.rgb = COLOR_GOLD
        # Tiêu đề cấp 3 (### Subtitle)
        elif stripped.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(stripped[4:])
            r.font.size = Pt(11.5)
            r.font.bold = True
            r.font.color.rgb = COLOR_NAVY
        # Gạch đầu dòng (- Bullet hoặc * Bullet)
        elif stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('• '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            _format_inline_markdown(p, stripped[2:])
        # Khối trích dẫn (> Quote)
        elif stripped.startswith('> '):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(stripped[2:])
            r.font.italic = True
            r.font.size = Pt(10)
            r.font.color.rgb = COLOR_GRAY
        # Đoạn văn bản thông thường
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            _format_inline_markdown(p, stripped)

    # Nếu file kết thúc bằng bảng
    if in_table and table_rows:
        _render_parsed_table(doc, table_rows)

def _format_inline_markdown(paragraph, text: str):
    """Phân giải in đậm **bold** và in nghiêng *italic* inline."""
    pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)'
    tokens = re.split(pattern, text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            r = paragraph.add_run(token[2:-2])
            r.font.bold = True
        elif token.startswith('*') and token.endswith('*'):
            r = paragraph.add_run(token[1:-1])
            r.font.italic = True
        elif token.startswith('`') and token.endswith('`'):
            r = paragraph.add_run(token[1:-1])
            r.font.name = 'Consolas'
            r.font.size = Pt(9.5)
            r.font.color.rgb = COLOR_RED
        else:
            paragraph.add_run(token)

def _render_parsed_table(doc: docx.Document, rows_data: List[List[str]]):
    """Vẽ bảng Markdown vào Document với phong cách thanh lịch."""
    if not rows_data or not rows_data[0]:
        return

    cols_count = max(len(r) for r in rows_data)
    table = doc.add_table(rows=len(rows_data), cols=cols_count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    for row_idx, row in enumerate(rows_data):
        is_header = (row_idx == 0)
        for col_idx in range(cols_count):
            cell = table.cell(row_idx, col_idx)
            text_val = row[col_idx] if col_idx < len(row) else ""
            cell.text = text_val
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.1

            if is_header:
                _set_cell_background(cell, "0B1838")  # Nền Navy
                for r in p.runs:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(255, 255, 255)
                    r.font.size = Pt(10)
            else:
                if row_idx % 2 == 1:
                    _set_cell_background(cell, "F8F9FA")  # Xen kẽ xám rất nhạt
                for r in p.runs:
                    r.font.size = Pt(9.5)
            _set_cell_margins(cell)

    doc.add_paragraph().paragraph_format.space_before = Pt(6)

def _add_legal_citations_table(doc: docx.Document, citations: List[Dict[str, Any]]):
    """Bổ sung danh mục Căn cứ Pháp lý chính thống từ Cơ sở dữ liệu Quốc gia vbpl.vn."""
    if not citations:
        return

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(14)
    p_title.paragraph_format.space_after = Pt(4)
    r_t = p_title.add_run("DANH MỤC CĂN CỨ PHÁP LÝ ÁP DỤNG (RAG QUỐC GIA — VBPL.VN)")
    r_t.font.bold = True
    r_t.font.size = Pt(11)
    r_t.font.color.rgb = COLOR_NAVY

    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    hdr = table.rows[0].cells
    hdr[0].text = "Điều luật"
    hdr[1].text = "Tên văn bản quy phạm pháp luật"
    hdr[2].text = "Nguồn đối chiếu chính thức"
    for c in hdr:
        _set_cell_background(c, "B8860B")  # Màu vàng hổ phách
        for r in c.paragraphs[0].runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)
        _set_cell_margins(c)

    for item in citations:
        row = table.add_row().cells
        row[0].text = item.get("article_number", "Điều luật")
        row[1].text = item.get("law_name", "")
        row[2].text = item.get("official_source", item.get("source", "vbpl.vn"))

        row[0].paragraphs[0].runs[0].font.bold = True
        for c in row:
            for r in c.paragraphs[0].runs:
                r.font.size = Pt(9)
            _set_cell_margins(c)

    doc.add_paragraph().paragraph_format.space_before = Pt(8)

def _add_footer_disclaimer(doc: docx.Document):
    """Thêm chữ ký và Lời nhắc pháp lý (Disclaimer)."""
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sig.paragraph_format.space_before = Pt(18)
    p_sig.paragraph_format.space_after = Pt(2)

    r_date = p_sig.add_run(f"Hà Nội / TP.HCM, ngày {datetime.now().strftime('%d')} tháng {datetime.now().strftime('%m')} năm {datetime.now().strftime('%Y')}\n")
    r_date.font.italic = True
    r_date.font.size = Pt(10)

    r_pos = p_sig.add_run("CỐ VẤN PHÁP LÝ TRÍ TUỆ NHÂN TẠO\n\n\n")
    r_pos.font.bold = True
    r_pos.font.size = Pt(10.5)
    r_pos.font.color.rgb = COLOR_NAVY

    r_name = p_sig.add_run("HUỲNH NGUYÊN KHANG\n")
    r_name.font.bold = True
    r_name.font.size = Pt(11)
    r_name.font.color.rgb = COLOR_GOLD

    r_cert = p_sig.add_run("(Xác thực chữ ký số điện tử theo Luật Công chứng 2024)")
    r_cert.font.size = Pt(8.5)
    r_cert.font.italic = True
    r_cert.font.color.rgb = COLOR_GRAY

    # Lời nhắc pháp lý bắt buộc theo RULES.md
    p_disc = doc.add_paragraph()
    p_disc.paragraph_format.space_before = Pt(16)
    p_disc.paragraph_format.space_after = Pt(4)
    r_d = p_disc.add_run(
        "⚠️ LỜI NHẮC PHÁP LÝ QUAN TRỌNG: Báo cáo này do Trợ lý Cố vấn Pháp lý AI Huỳnh Nguyên Khang "
        "thực hiện dựa trên dữ liệu đối chiếu từ Hệ thống Pháp luật Việt Nam hiện hành. Văn bản mang tính chất "
        "định hướng tham khảo chuyên môn, không thay thế cho dịch vụ tư vấn pháp lý có chứng chỉ hành nghề của Luật sư trong các vụ việc tranh tụng phức tạp."
    )
    r_d.font.size = Pt(8.5)
    r_d.font.italic = True
    r_d.font.color.rgb = COLOR_GRAY

def create_contract_review_docx(
    analysis_text: str,
    contract_title: str = "Hợp đồng kinh tế",
    protect_side: str = "Toàn diện",
    citations: Optional[List[Dict[str, Any]]] = None
) -> io.BytesIO:
    """Tạo file Word Báo cáo Thẩm định Hợp đồng chuyên nghiệp."""
    doc = docx.Document()

    # Thiết lập lề 2cm chuẩn văn bản hành chính Việt Nam
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    _add_header_banner(doc)

    # Tiêu đề Báo Cáo
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(3)
    r_title = p_title.add_run("BÁO CÁO THẨM ĐỊNH RỦI RO HỢP ĐỒNG & KHUYẾN NGHỊ PHÁP LÝ")
    r_title.font.bold = True
    r_title.font.size = Pt(14)
    r_title.font.color.rgb = COLOR_NAVY

    # Thông tin hợp đồng
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_after = Pt(14)
    r_m1 = p_meta.add_run(f"Tài liệu rà soát: {contract_title}  |  ")
    r_m1.font.size = Pt(10)
    r_m1.font.bold = True
    r_m2 = p_meta.add_run(f"Góc nhìn bảo vệ: {protect_side}")
    r_m2.font.size = Pt(10)
    r_m2.font.color.rgb = COLOR_GOLD
    r_m2.font.bold = True

    # Nội dung phân tích & Ma trận rủi ro
    _add_markdown_content_to_doc(doc, analysis_text)

    # Căn cứ pháp lý
    if citations:
        _add_legal_citations_table(doc, citations)

    # Chữ ký & Miễn trừ trách nhiệm
    _add_footer_disclaimer(doc)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_legal_opinion_docx(
    topic: str,
    opinion_text: str,
    citations: Optional[List[Dict[str, Any]]] = None
) -> io.BytesIO:
    """Tạo file Word Thư Tư Vấn Pháp Lý theo chuẩn Luật Sư."""
    doc = docx.Document()

    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    _add_header_banner(doc)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(4)
    r_title = p_title.add_run("THƯ TƯ VẤN PHÁP LÝ CHUYÊN SÂU")
    r_title.font.bold = True
    r_title.font.size = Pt(14)
    r_title.font.color.rgb = COLOR_NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(f"V/v: {topic}")
    r_sub.font.bold = True
    r_sub.font.italic = True
    r_sub.font.size = Pt(10.5)
    r_sub.font.color.rgb = COLOR_GOLD

    _add_markdown_content_to_doc(doc, opinion_text)

    if citations:
        _add_legal_citations_table(doc, citations)

    _add_footer_disclaimer(doc)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_court_verdict_docx(
    case_title: str,
    user_role: str,
    verdict_markdown: str,
    dialogue_history: Optional[List[Any]] = None
) -> io.BytesIO:
    """Tạo file Word Bản án Sơ bộ & Biên bản Tranh tụng Tòa án."""
    doc = docx.Document()

    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    _add_header_banner(doc)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("BẢN ÁN SƠ BỘ VÀ BIÊN BẢN TRANH TỤNG TÒA ÁN")
    r_title.font.bold = True
    r_title.font.size = Pt(14)
    r_title.font.color.rgb = COLOR_NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(f"Vụ án: {case_title}  |  Tư cách: {user_role}")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = COLOR_GOLD

    # Nội dung phán quyết của Hội Đồng Xét Xử
    _add_markdown_content_to_doc(doc, verdict_markdown)

    # Biên bản đối chất tranh tụng
    if dialogue_history and len(dialogue_history) > 0:
        p_sec = doc.add_paragraph()
        p_sec.paragraph_format.space_before = Pt(16)
        p_sec.paragraph_format.space_after = Pt(6)
        r_sec = p_sec.add_run("--- BIÊN BẢN ĐỐI CHẤT TRANH TỤNG TẠI PHIÊN TÒA ---")
        r_sec.font.bold = True
        r_sec.font.size = Pt(11.5)
        r_sec.font.color.rgb = COLOR_NAVY

        for msg in dialogue_history:
            speaker = getattr(msg, 'speaker', '') if hasattr(msg, 'speaker') else msg.get('speaker', '')
            text = getattr(msg, 'text', '') if hasattr(msg, 'text') else msg.get('text', '')
            label = "BẠN" if speaker == 'user' else ("LUẬT SƯ ĐỐI TỤNG" if speaker == 'opposing' else "THẨM PHÁN")
            color = COLOR_GOLD if speaker == 'user' else (COLOR_RED if speaker == 'opposing' else COLOR_NAVY)

            p_turn = doc.add_paragraph()
            p_turn.paragraph_format.space_before = Pt(4)
            p_turn.paragraph_format.space_after = Pt(4)
            r_spk = p_turn.add_run(f"[{label}]: ")
            r_spk.font.bold = True
            r_spk.font.color.rgb = color
            r_txt = p_turn.add_run(text)
            r_txt.font.size = Pt(10)

    _add_footer_disclaimer(doc)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_petition_docx(
    petition_title: str,
    petition_markdown: str
) -> io.BytesIO:
    """Tạo file Word Đơn Khởi Kiện / Đơn Tố Tụng chuẩn thể thức Nghị định 30/2020."""
    doc = docx.Document()

    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.9)  # Lề trái chuẩn 30mm cho đơn từ
        s.right_margin = Inches(0.7)

    # Quốc hiệu và Tiêu ngữ chuẩn văn bản hành chính Việt Nam
    p_qh = doc.add_paragraph()
    p_qh.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qh.paragraph_format.space_after = Pt(2)
    r1 = p_qh.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    r1.font.bold = True
    r1.font.size = Pt(12)
    r2 = p_qh.add_run("Độc lập - Tự do - Hạnh phúc\n")
    r2.font.bold = True
    r2.font.size = Pt(12.5)
    r3 = p_qh.add_run("--------------------------")
    r3.font.size = Pt(10)

    # Tiêu đề đơn
    p_t = doc.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t.paragraph_format.space_before = Pt(12)
    p_t.paragraph_format.space_after = Pt(14)
    r_t = p_t.add_run(petition_title.upper())
    r_t.font.bold = True
    r_t.font.size = Pt(14)
    r_t.font.color.rgb = COLOR_NAVY

    _add_markdown_content_to_doc(doc, petition_markdown)

    # Phần chữ ký người làm đơn
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sig.paragraph_format.space_before = Pt(20)
    p_sig.paragraph_format.space_after = Pt(2)
    r_date = p_sig.add_run(f"......, Ngày {datetime.now().day} tháng {datetime.now().month} năm {datetime.now().year}\n")
    r_date.font.italic = True
    r_sign = p_sig.add_run("NGƯỜI LÀM ĐƠN\n")
    r_sign.font.bold = True
    r_note = p_sig.add_run("(Ký và ghi rõ họ tên)")
    r_note.font.italic = True
    r_note.font.size = Pt(9.5)

    _add_footer_disclaimer(doc)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_corporate_audit_docx(
    company_name: str,
    business_type: str,
    audit_markdown: str
) -> io.BytesIO:
    """Tạo file Word Báo Cáo Khám Sức Khỏe Pháp Chế Doanh Nghiệp."""
    doc = docx.Document()

    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    _add_header_banner(doc)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("BÁO CÁO KHÁM SỨC KHỎE PHÁP CHẾ DOANH NGHIỆP")
    r_title.font.bold = True
    r_title.font.size = Pt(14)
    r_title.font.color.rgb = COLOR_NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(f"Doanh nghiệp: {company_name}  |  Hình thức: {business_type}")
    r_sub.font.bold = True
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = COLOR_GOLD

    _add_markdown_content_to_doc(doc, audit_markdown)

    _add_footer_disclaimer(doc)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

