import pandas as pd
from typing import Optional

from src.data.yuanta_client import yuanta_client

def fetch_financial_statements(ticker: str, term: str, year: int, report_type: str = "BCTT", page_size: int = 10) -> pd.DataFrame:
    """
    Lấy báo cáo tài chính hoặc các biểu mẫu báo cáo từ Yuanta theo Quý hoặc Năm.
    Ví dụ: term="Q2", year=2026, report_type="BCTT" (Báo cáo thường niên/tóm tắt), "CSTC" (Chỉ số tài chính), 
    "KQKD" (Kết quả kinh doanh), "CDKT" (Cân đối kế toán), "LCTT" (Lưu chuyển tiền tệ), hoặc "BCTC" (Đầy đủ).
    """
    endpoint = "vietstock/financial_statement/report"
    
    # Suy luận từ params cung cấp: 2 = Quý, 1 = Năm
    report_term_type = 2 if str(term).upper().startswith("Q") else 1
    
    params = {
        "lang": "vi",
        "page_index": 1,
        "page_size": page_size,
        "report_term_type": report_term_type,
        "report_type": report_type,
        "stock_code": ticker,
        "term_code": term,
        "unit": 1000000,
        "year_period": year
    }
    
    response = yuanta_client.get(endpoint, params=params)
    
    if response and isinstance(response, dict):
        if response.get("success") and "response" in response:
            res_data = response["response"]
            if "detail" in res_data and "title" in res_data and "data" in res_data["title"]:
                details = res_data["detail"]
                periods = res_data["title"]["data"]
                
                rows = []
                for comp in details:
                    for item in comp.get("data", []):
                        row = {
                            "report_component": comp.get("report_component_name"),
                            "field_name": item.get("field_name"),
                            "unit": item.get("unit")
                        }
                        for i, val in enumerate(item.get("value", [])):
                            if i < len(periods):
                                p = periods[i]
                                col = f"{p['term_code']}/{p['year_period']}"
                                row[col] = val
                        rows.append(row)
                if rows:
                    return pd.DataFrame(rows)
        # Fallback if structure is different
        data = response.get('data', [])
        if not data:
            for key, val in response.items():
                if isinstance(val, list):
                    data = val
                    break
        if data:
            return pd.DataFrame(data)
            
    elif response and isinstance(response, list):
        return pd.DataFrame(response)
        
    return pd.DataFrame()

def fetch_financial_ratios(ticker: str, term: str = "Q2", year: int = 2026, page_size: int = 5) -> pd.DataFrame:
    """
    Tích hợp trực tiếp API Chỉ số tài chính (CSTC) từ Yuanta:
    https://ysradarapi.yuanta.com.vn/api/v3/vietstock/financial_statement/report?lang=vi&page_index=1&page_size=5&report_term_type=2&report_type=CSTC&stock_code=ACB&term_code=Q2&unit=1000000&year_period=2026
    Trả về DataFrame chi tiết các nhóm: Nhóm chỉ số Định giá, Sinh lợi, Tăng trưởng...
    """
    return fetch_financial_statements(ticker=ticker, term=term, year=year, report_type="CSTC", page_size=page_size)

def fetch_stock_info_basic(ticker: str) -> pd.DataFrame:
    """
    Lấy thông tin cơ bản của cổ phiếu.
    API: stock_rating/info/{ticker}?lang=vi
    """
    endpoint = f"stock_rating/info/{ticker}"
    params = {"lang": "vi"}
    
    response = yuanta_client.get(endpoint, params=params)
    if response and isinstance(response, dict):
        # Flatten dictionary or wrap in list for DataFrame
        return pd.DataFrame([response])
    elif response and isinstance(response, list):
        return pd.DataFrame(response)
        
    return pd.DataFrame()

def fetch_financial_statements_history(ticker: str, start_year: int = 2016, report_type: str = "BCTT", report_term_type: int = 2) -> pd.DataFrame:
    """
    Lấy chuỗi lịch sử báo cáo tài chính của mã cổ phiếu theo Quý hoặc Năm từ hiện tại lùi về start_year (mặc định từ 2016).
    report_type: BCTT, CSTC, BCTC, KQKD, CDKT, LCTT
    """
    import datetime
    current_year = datetime.datetime.now().year
    
    all_rows = []
    page_index = 1
    
    while True:
        endpoint = "vietstock/financial_statement/report"
        params = {
            "lang": "vi",
            "page_index": page_index,
            "page_size": 10,
            "report_term_type": report_term_type,
            "report_type": report_type,
            "stock_code": ticker,
            "term_code": "N" if report_term_type == 1 else "Q4",
            "unit": 1000000,
            "year_period": current_year
        }
        
        response = yuanta_client.get(endpoint, params=params)
        
        if response and isinstance(response, dict):
            if response.get("success") and "response" in response:
                res_data = response["response"]
                if "detail" in res_data and "title" in res_data and "data" in res_data["title"]:
                    details = res_data["detail"]
                    periods = res_data["title"]["data"]
                    
                    if not periods:
                        break # Hết dữ liệu
                        
                    oldest_year = min([p['year_period'] for p in periods])
                    
                    for comp in details:
                        for item in comp.get("data", []):
                            row = {
                                "report_component": comp.get("report_component_name"),
                                "field_name": item.get("field_name")
                            }
                            for i, val in enumerate(item.get("value", [])):
                                if i < len(periods):
                                    p = periods[i]
                                    if p['year_period'] >= start_year:
                                        col = f"{p['year_period']}_{p['term_code']}"
                                        row[col] = val
                            all_rows.append(row)
                    
                    if oldest_year < start_year or page_index >= 10: # Safety cap at 10 pages (~100 quarters = 25 years)
                        break
                    page_index += 1
                else:
                    break
            else:
                break
        else:
            break

    if all_rows:
        # Group by component and field_name and merge dicts
        merged = {}
        for row in all_rows:
            key = (row["report_component"], row["field_name"])
            if key not in merged:
                merged[key] = row
            else:
                merged[key].update(row)
        
        return pd.DataFrame(list(merged.values()))
        
    return pd.DataFrame()

def fetch_financial_ratios_history(ticker: str, start_year: int = 2016) -> pd.DataFrame:
    """
    Lấy trọn bộ lịch sử 10 năm (từ 2016) của các Chỉ số tài chính (CSTC) - Định giá, Sinh lời, Tăng trưởng (Theo Quý).
    """
    return fetch_financial_statements_history(ticker=ticker, start_year=start_year, report_type="CSTC", report_term_type=2)

def fetch_financial_ratios_history_yearly(ticker: str, start_year: int = 2016) -> pd.DataFrame:
    """
    Lấy trọn bộ lịch sử 10 năm (từ 2016) của các Chỉ số tài chính (CSTC) (Theo Năm).
    """
    return fetch_financial_statements_history(ticker=ticker, start_year=start_year, report_type="CSTC", report_term_type=1)
