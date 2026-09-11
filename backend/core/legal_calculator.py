# backend/core/legal_calculator.py — Bộ công cụ tính toán pháp lý & tài chính tố tụng tự động
# Áp dụng chuẩn xác quy định pháp luật Việt Nam:
# 1. Án phí Tòa án: Nghị quyết 326/2016/UBTVQH14 của Ủy ban Thường vụ Quốc hội
# 2. Tiền lãi chậm trả: Điều 357 & Điều 468 Bộ luật Dân sự 2015
# 3. Thuế & Lệ phí BĐS: Luật Thuế TNCN & Nghị định 10/2022/NĐ-CP (Lệ phí trước bạ)
# 4. Trợ cấp thôi việc: Điều 46 Bộ luật Lao động 2019

from datetime import datetime
from typing import Dict, Any, Optional

class LegalCalculator:
    @staticmethod
    def calculate_court_fee(dispute_value: float, case_type: str = "civil") -> Dict[str, Any]:
        """
        Tính án phí sơ thẩm và tiền tạm ứng án phí theo Nghị quyết 326/2016/UBTVQH14.
        case_type: 'civil' (Dân sự thông thường), 'commercial' (Kinh doanh thương mại), 'non_monetary' (Không có giá ngạch)
        """
        if dispute_value <= 0 or case_type == "non_monetary":
            fee = 300000.0  # 300,000 VND án phí không có giá ngạch
            advance_fee = 300000.0
            bracket_desc = "Vụ việc không có giá ngạch (Ly hôn, đòi nhà, tranh chấp phi tài sản)"
            formula_desc = "Án phí cố định: 300.000 VNĐ"
            return {
                "dispute_value": 0,
                "court_fee": fee,
                "advance_fee": advance_fee,
                "bracket_desc": bracket_desc,
                "formula_desc": formula_desc,
                "case_type": "Không có giá ngạch",
                "legal_basis": "Nghị quyết số 326/2016/UBTVQH14 (Mục 1 Danh mục án phí, lệ phí Tòa án)"
            }

        val = float(dispute_value)
        fee = 0.0
        bracket_desc = ""
        formula_desc = ""

        if case_type == "commercial":
            # Biểu án phí Kinh doanh thương mại có giá ngạch
            if val <= 60000000:
                fee = 3000000.0
                bracket_desc = "Từ 60 triệu đồng trở xuống"
                formula_desc = "Mức cố định: 3.000.000 VNĐ"
            elif val <= 400000000:
                fee = val * 0.05
                bracket_desc = "Từ trên 60 triệu đến 400 triệu đồng"
                formula_desc = "5% giá trị tranh chấp"
            elif val <= 800000000:
                fee = 20000000.0 + (val - 400000000) * 0.04
                bracket_desc = "Từ trên 400 triệu đến 800 triệu đồng"
                formula_desc = "20.000.000 VNĐ + 4% của phần vượt quá 400.000.000 VNĐ"
            elif val <= 2000000000:
                fee = 36000000.0 + (val - 800000000) * 0.03
                bracket_desc = "Từ trên 800 triệu đến 2 tỷ đồng"
                formula_desc = "36.000.000 VNĐ + 3% của phần vượt quá 800.000.000 VNĐ"
            elif val <= 4000000000:
                fee = 72000000.0 + (val - 2000000000) * 0.02
                bracket_desc = "Từ trên 2 tỷ đến 4 tỷ đồng"
                formula_desc = "72.000.000 VNĐ + 2% của phần vượt quá 2.000.000.000 VNĐ"
            else:
                fee = 112000000.0 + (val - 4000000000) * 0.001
                bracket_desc = "Từ trên 4 tỷ đồng"
                formula_desc = "112.000.000 VNĐ + 0.1% của phần vượt quá 4.000.000.000 VNĐ"
        else:
            # Biểu án phí Dân sự có giá ngạch (Khoản 1 Mục II Danh mục NQ 326)
            if val <= 6000000:
                fee = 300000.0
                bracket_desc = "Từ 6 triệu đồng trở xuống"
                formula_desc = "Mức cố định: 300.000 VNĐ"
            elif val <= 400000000:
                fee = val * 0.05
                bracket_desc = "Từ trên 6 triệu đến 400 triệu đồng"
                formula_desc = "5% giá trị tranh chấp"
            elif val <= 800000000:
                fee = 20000000.0 + (val - 400000000) * 0.04
                bracket_desc = "Từ trên 400 triệu đến 800 triệu đồng"
                formula_desc = "20.000.000 VNĐ + 4% của phần vượt quá 400.000.000 VNĐ"
            elif val <= 2000000000:
                fee = 36000000.0 + (val - 800000000) * 0.03
                bracket_desc = "Từ trên 800 triệu đến 2 tỷ đồng"
                formula_desc = "36.000.000 VNĐ + 3% của phần vượt quá 800.000.000 VNĐ"
            elif val <= 4000000000:
                fee = 72000000.0 + (val - 2000000000) * 0.02
                bracket_desc = "Từ trên 2 tỷ đến 4 tỷ đồng"
                formula_desc = "72.000.000 VNĐ + 2% của phần vượt quá 2.000.000.000 VNĐ"
            else:
                fee = 112000000.0 + (val - 4000000000) * 0.001
                bracket_desc = "Từ trên 4 tỷ đồng"
                formula_desc = "112.000.000 VNĐ + 0.1% của phần vượt quá 4.000.000.000 VNĐ"

        # Tạm ứng án phí sơ thẩm: 50% mức án phí dự tính (Điều 7 Nghị quyết 326)
        advance_fee = fee * 0.5

        return {
            "dispute_value": val,
            "court_fee": round(fee),
            "advance_fee": round(advance_fee),
            "bracket_desc": bracket_desc,
            "formula_desc": formula_desc,
            "case_type": "Kinh doanh thương mại" if case_type == "commercial" else "Dân sự",
            "legal_basis": "Nghị quyết số 326/2016/UBTVQH14 (Điều 7 và Danh mục mức án phí TAND)"
        }

    @staticmethod
    def calculate_late_interest(
        principal: float,
        start_date: str,
        end_date: Optional[str] = None,
        annual_rate: float = 10.0
    ) -> Dict[str, Any]:
        """
        Tính tiền lãi do chậm thực hiện nghĩa vụ trả tiền theo Điều 357 & Điều 468 BLDS 2015.
        Mức lãi suất luật định: 10%/năm nếu không có thỏa thuận (hoặc tối đa 20%/năm).
        """
        try:
            d_start = datetime.strptime(start_date.strip(), "%Y-%m-%d")
            if end_date and end_date.strip():
                d_end = datetime.strptime(end_date.strip(), "%Y-%m-%d")
            else:
                d_end = datetime.now()
        except Exception:
            # Fallback nếu format khác (dd/mm/yyyy)
            d_start = datetime.strptime(start_date.strip(), "%d/%m/%Y")
            d_end = datetime.strptime(end_date.strip(), "%d/%m/%Y") if end_date else datetime.now()

        days = (d_end - d_start).days
        if days < 0:
            days = 0

        # Lãi suất theo ngày = Lãi suất năm / 365
        rate = float(annual_rate)
        # Giới hạn trần lãi suất theo Điều 468 BLDS 2015 không quá 20%/năm
        effective_rate = min(rate, 20.0)

        interest = principal * (effective_rate / 100.0 / 365.0) * days
        total_due = principal + interest

        return {
            "principal": principal,
            "start_date": d_start.strftime("%d/%m/%Y"),
            "end_date": d_end.strftime("%d/%m/%Y"),
            "days_overdue": days,
            "annual_rate": effective_rate,
            "interest_amount": round(interest),
            "total_due": round(total_due),
            "legal_basis": "Điều 357 & Điều 468 Bộ luật Dân sự 2015 (Trần lãi suất 20%/năm, lãi chậm trả cơ sở 10%/năm)"
        }

    @staticmethod
    def calculate_property_tax(property_value: float) -> Dict[str, Any]:
        """
        Tính thuế TNCN (2%) và Lệ phí trước bạ (0.5%) khi chuyển nhượng bất động sản.
        """
        val = float(property_value)
        tax_tncn = val * 0.02       # 2% giá trị chuyển nhượng
        fee_truoc_ba = val * 0.005  # 0.5% lệ phí trước bạ
        total_tax = tax_tncn + fee_truoc_ba

        return {
            "property_value": val,
            "tax_tncn": round(tax_tncn),
            "fee_truoc_ba": round(fee_truoc_ba),
            "total_tax": round(total_tax),
            "tax_rate_tncn": "2%",
            "tax_rate_truoc_ba": "0.5%",
            "legal_basis": "Luật Thuế TNCN (Điều 14) & Nghị định 10/2022/NĐ-CP (Điều 8)"
        }

    @staticmethod
    def calculate_severance_allowance(
        months_worked: float,
        avg_salary_6_months: float,
        months_unemployment_insured: float = 0.0
    ) -> Dict[str, Any]:
        """
        Tính tiền trợ cấp thôi việc theo Điều 46 Bộ luật Lao động 2019.
        Thời gian tính trợ cấp = Tổng thời gian làm việc thực tế - Thời gian đã tham gia BHTN.
        Mỗi năm làm việc được trợ cấp 1/2 tháng tiền lương.
        """
        # Làm tròn theo Khoản 2 Điều 8 Nghị định 145/2020/NĐ-CP:
        # Tháng lẻ từ đủ 01 đến 06 tháng tính 1/2 năm (0.5 năm); trên 06 tháng tính 01 năm làm việc.
        months_eligible = max(0.0, months_worked - months_unemployment_insured)
        full_years = int(months_eligible // 12)
        rem_months = months_eligible % 12

        if rem_months > 6:
            calc_years = full_years + 1.0
        elif rem_months > 0:
            calc_years = full_years + 0.5
        else:
            calc_years = float(full_years)

        allowance = calc_years * 0.5 * avg_salary_6_months

        return {
            "total_months_worked": months_worked,
            "months_unemployment_insured": months_unemployment_insured,
            "calc_years": calc_years,
            "avg_salary_6_months": avg_salary_6_months,
            "allowance_amount": round(allowance),
            "legal_basis": "Điều 46 Bộ luật Lao động 2019 (Trợ cấp thôi việc 1/2 tháng lương/năm làm việc)"
        }

legal_calculator = LegalCalculator()

def calculate_court_fee(amount: float, dispute_type: str = "civil", has_valuation: bool = True) -> Dict[str, Any]:
    case_type = "non_monetary" if not has_valuation else ("commercial" if dispute_type == "commercial" else "civil")
    data = LegalCalculator.calculate_court_fee(amount, case_type=case_type)
    fee_str = f"{data['court_fee']:,} VNĐ"
    adv_str = f"{data['advance_fee']:,} VNĐ"
    summary = f"Án phí sơ thẩm dự tính: {fee_str} (Tạm ứng án phí nộp trước: {adv_str}). Áp dụng khung: {data['bracket_desc']}."
    return {
        "success": True,
        "title": "Dự toán Án phí Tòa án (Nghị quyết 326/2016/UBTVQH14)",
        "result_details": data,
        "legal_basis": data["legal_basis"],
        "summary_text": summary
    }

def calculate_late_interest(principal: float, start_date_str: str, end_date_str: Optional[str] = None, rate_percent_per_year: Optional[float] = None) -> Dict[str, Any]:
    rate = rate_percent_per_year if (rate_percent_per_year is not None and rate_percent_per_year > 0) else 10.0
    data = LegalCalculator.calculate_late_interest(principal, start_date_str, end_date_str, annual_rate=rate)
    interest_str = f"{data['interest_amount']:,} VNĐ"
    total_str = f"{data['total_due']:,} VNĐ"
    summary = f"Tiền lãi chậm trả phát sinh ({data['days_overdue']} ngày, lãi suất {data['annual_rate']}%/năm): {interest_str}. Tổng nghĩa vụ thanh toán: {total_str}."
    return {
        "success": True,
        "title": "Tính Lãi Suất Chậm Trả (Điều 357 & Điều 468 BLDS 2015)",
        "result_details": data,
        "legal_basis": data["legal_basis"],
        "summary_text": summary
    }

def calculate_property_tax(price: float, is_first_home: bool = False) -> Dict[str, Any]:
    data = LegalCalculator.calculate_property_tax(price)
    if is_first_home:
        data["tax_tncn"] = 0
        data["total_tax"] = data["fee_truoc_ba"]
        data["is_first_home_exempt"] = True
        summary = f"Miễn thuế TNCN (nhà ở duy nhất). Tổng lệ phí trước bạ phải nộp: {data['total_tax']:,} VNĐ (0.5%)."
    else:
        summary = f"Tổng thuế & lệ phí chuyển nhượng BĐS: {data['total_tax']:,} VNĐ (Gồm Thuế TNCN 2%: {data['tax_tncn']:,} VNĐ và Lệ phí trước bạ 0.5%: {data['fee_truoc_ba']:,} VNĐ)."
    return {
        "success": True,
        "title": "Tính Thuế TNCN & Lệ Phí Trước Bạ Chuyển Nhượng Bất Động Sản",
        "result_details": data,
        "legal_basis": data["legal_basis"],
        "summary_text": summary
    }

def calculate_severance_allowance(salary: float, working_years: float) -> Dict[str, Any]:
    months_worked = working_years * 12.0
    data = LegalCalculator.calculate_severance_allowance(months_worked=months_worked, avg_salary_6_months=salary)
    allowance_str = f"{data['allowance_amount']:,} VNĐ"
    summary = f"Tiền trợ cấp thôi việc ({data['calc_years']} năm tính trợ cấp, mức lương bình quân {salary:,.0f} VNĐ): {allowance_str}."
    return {
        "success": True,
        "title": "Tính Trợ Cấp Thôi Việc (Điều 46 Bộ luật Lao động 2019)",
        "result_details": data,
        "legal_basis": data["legal_basis"],
        "summary_text": summary
    }

