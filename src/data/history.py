import requests
import pandas as pd
import datetime
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def fetch_ohlcv_history(ticker: str, start_year: int = 2016) -> pd.DataFrame:
    """
    Lấy dữ liệu giá lịch sử (OHLCV) từ DNSE API (tương tự vnstock).
    """
    start_date = datetime.datetime(start_year, 1, 1)
    end_date = datetime.datetime.now()
    
    start_ts = int(time.mktime(start_date.timetuple()))
    end_ts = int(time.mktime(end_date.timetuple()))
    
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={start_ts}&to={end_ts}&symbol={ticker}&resolution=1D"
    
    try:
        # User-Agent để tránh bị block
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        if 't' in data and data['t']:
            df = pd.DataFrame({
                'Time': pd.to_datetime(data['t'], unit='s'),
                'Open': data['o'],
                'High': data['h'],
                'Low': data['l'],
                'Close': data['c'],
                'Volume': data['v']
            })
            df['Ticker'] = ticker
            return df
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {ticker}: {e}")
        
    return pd.DataFrame()
