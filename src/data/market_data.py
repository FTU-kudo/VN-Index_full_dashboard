import pandas as pd
from typing import List

from src.data.yuanta_client import yuanta_client

def fetch_tickers_by_exchange(exchange: str) -> pd.DataFrame:
    """
    Lấy danh sách cổ phiếu theo sàn.
    exchange: HSX, HNX, UPCOM
    """
    endpoint = "market_data/price_board/stock/list_stock_info"
    params = {"exchange": exchange.upper()}
    
    response = yuanta_client.get(endpoint, params=params)
    if response:
        if isinstance(response, dict):
            # Lấy list từ key 'data' hoặc key đầu tiên chứa list
            data = response.get('data', [])
            if not data:
                for k, v in response.items():
                    if isinstance(v, list):
                        data = v
                        break
            if data:
                return pd.DataFrame(data)
        elif isinstance(response, list):
            return pd.DataFrame(response)
    return pd.DataFrame()

def fetch_all_tickers() -> List[str]:
    """
    Lấy toàn bộ mã cổ phiếu trên 3 sàn và trả về danh sách mã.
    """
    all_dfs = []
    for ex in ["HSX", "HNX", "UPCOM"]:
        df = fetch_tickers_by_exchange(ex)
        if not df.empty and 'StockCode' in df.columns:
            all_dfs.append(df)
            
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        # Loại bỏ các chứng quyền (CW) nếu cần, ở đây chỉ lấy mã cổ phiếu (thường là 3 chữ cái)
        tickers = combined['StockCode'].astype(str).unique().tolist()
        tickers = [t for t in tickers if len(t) == 3]
        return tickers
    return []

def fetch_tickers_by_sector() -> pd.DataFrame:
    """
    Lấy danh sách cổ phiếu theo nhóm ngành.
    API: list_stock_by_sector
    """
    endpoint = "market_data/price_board/stock/list_stock_by_sector"
    response = yuanta_client.get(endpoint)
    if response:
        if isinstance(response, dict):
            data = response.get('data', [])
            if not data:
                for k, v in response.items():
                    if isinstance(v, list):
                        data = v
                        break
            if data:
                return pd.DataFrame(data)
        elif isinstance(response, list):
            return pd.DataFrame(response)
    return pd.DataFrame()
