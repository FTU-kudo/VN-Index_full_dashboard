import pandas as pd
from typing import List
import asyncio
import aiohttp
from loguru import logger

from src.data.yuanta_client import yuanta_client, async_yuanta_client
from config.settings import API_CHUNK_SIZE

def _chunked_fetch(endpoint: str, stock_list: List[str], chunk_size: int = API_CHUNK_SIZE) -> pd.DataFrame:
    """Hàm helper để chia nhỏ danh sách mã và gọi API (batching)"""
    all_data = []
    
    for i in range(0, len(stock_list), chunk_size):
        chunk = stock_list[i:i + chunk_size]
        stock_str = ",".join(chunk)
        
        params = {
            "stock_list": stock_str,
            "stock_type": "ST"
        }
        response = yuanta_client.get(endpoint, params=params)
        
        if response:
            if isinstance(response, dict):
                data = response.get('data', [])
                if not data:
                    for k, v in response.items():
                        if isinstance(v, list):
                            data = v
                            break
                if data:
                    all_data.extend(data)
            elif isinstance(response, list):
                all_data.extend(response)
            
    if all_data:
        return pd.DataFrame(all_data)
    return pd.DataFrame()

def fetch_realtime_prices(stock_list: List[str]) -> pd.DataFrame:
    """
    Lấy giá, khối lượng và các chỉ số giao dịch realtime cho danh sách mã.
    API: list_stock_info?stock_list=...&stock_type=ST
    """
    endpoint = "market_data/price_board/stock/list_stock_info"
    return _chunked_fetch(endpoint, stock_list)

def fetch_stock_ratings(stock_list: List[str]) -> pd.DataFrame:
    """
    Lấy đánh giá, chấm điểm và khuyến nghị cho danh sách mã.
    API: list_stock_rating_info?stock_list=...&stock_type=ST
    """
    endpoint = "market_data/price_board/stock/list_stock_rating_info"
    return _chunked_fetch(endpoint, stock_list)

async def _fetch_batch(session: aiohttp.ClientSession, batch: List[str]) -> List[dict]:
    stock_str = ",".join(batch)
    params = {"stock_list": stock_str, "stock_type": "ST"}
    endpoint = "market_data/price_board/stock/list_stock_info"
    response = await async_yuanta_client.get(session, endpoint, params)
    
    if response and isinstance(response, dict):
        if response.get("success"):
            return response.get("response", [])
        
        data = response.get('data', [])
        if not data:
            for k, v in response.items():
                if isinstance(v, list):
                    return v
        return data
    elif response and isinstance(response, list):
        return response
    return []

async def take_snapshot_async(
    tickers: List[str] | None = None,
    concurrency: int = 20,
    batch_size: int = 50,
) -> pd.DataFrame:
    """
    Fetch real-time prices cho tất cả tickers dùng AsyncYuantaClient.
    17 batches × 100 mã = ~17 requests song song → xong trong < 30 giây.
    """
    if not tickers:
        logger.warning("No tickers provided for async snapshot.")
        return pd.DataFrame()
        
    async_yuanta_client.semaphore = asyncio.Semaphore(concurrency)
    
    async with aiohttp.ClientSession(headers=async_yuanta_client.headers) as session:
        tasks = []
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            tasks.append(_fetch_batch(session, batch))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
    all_data = []
    for res in results:
        if isinstance(res, list):
            all_data.extend(res)
        elif isinstance(res, Exception):
            logger.error(f"Error fetching batch: {res}")
            
    if all_data:
        logger.success(f"Successfully fetched async snapshot for {len(all_data)} stocks.")
        return pd.DataFrame(all_data)
        
    return pd.DataFrame()


def compute_market_breadth(df_prices: pd.DataFrame) -> dict:
    """
    Tính breadth indicators từ price snapshot.
    """
    if df_prices.empty:
        return {}
        
    # Safe fallback if columns are missing
    for col in ['RefP', 'CeilingP', 'FloorP', 'LastMP', 'TotalVol', 'FTBuyVal', 'FTSellVal']:
        if col not in df_prices.columns:
            df_prices[col] = 0
            
    # Calculate indicators
    advancing = df_prices[df_prices['LastMP'] > df_prices['RefP']]
    declining = df_prices[df_prices['LastMP'] < df_prices['RefP']]
    
    num_advancing = len(advancing)
    num_declining = len(declining)
    
    advancing_volume = advancing['TotalVol'].sum()
    declining_volume = declining['TotalVol'].sum()
    
    at_ceiling = len(df_prices[df_prices['LastMP'] >= df_prices['CeilingP']])
    at_floor = len(df_prices[(df_prices['LastMP'] <= df_prices['FloorP']) & (df_prices['LastMP'] > 0)])
    
    foreign_net_flow = (df_prices['FTBuyVal'].sum() - df_prices['FTSellVal'].sum()) / 1e9 # Tỷ VND
    
    pct_above_ref = (num_advancing / len(df_prices)) * 100 if len(df_prices) > 0 else 0
    
    return {
        "advance_decline_ratio": round(num_advancing / num_declining, 2) if num_declining > 0 else float('inf'),
        "advancing_volume": advancing_volume,
        "declining_volume": declining_volume,
        "foreign_net_flow_bn_vnd": round(foreign_net_flow, 2),
        "pct_above_ref": round(pct_above_ref, 2),
        "at_ceiling": at_ceiling,
        "at_floor": at_floor,
        "total_stocks": len(df_prices)
    }
