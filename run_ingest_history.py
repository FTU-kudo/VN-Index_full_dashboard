import sys
from pathlib import Path
import logging
import time
import pandas as pd
import warnings

# Thêm root dự án vào sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from config.settings import PROCESSED_DIR, RAW_DIR
from src.data.market_data import fetch_all_tickers
from src.data.fundamental import fetch_financial_statements_history
from src.data.history import fetch_ohlcv_history
from src.data.storage import save_to_parquet

# Bỏ qua các cảnh báo tương lai của Pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ingestion():
    logger.info("1. Bắt đầu lấy danh sách toàn bộ cổ phiếu (Universe)...")
    tickers = fetch_all_tickers()
    logger.info(f"Đã lấy được {len(tickers)} mã cổ phiếu.")
    
    # 2. Lấy dữ liệu BCTC từ 2016
    logger.info(f"2. Lấy BCTC từ 2016 cho {len(tickers)} mã (có thể mất thời gian)...")
    fs_dfs = []
    
    # Để an toàn về bộ nhớ và tránh mất dữ liệu, có thể chia chunk nhưng hiện tại gộp chung
    for i, t in enumerate(tickers):
        try:
            df_fs = fetch_financial_statements_history(t, start_year=2016)
            if df_fs is not None and not df_fs.empty:
                df_fs['Ticker'] = t
                fs_dfs.append(df_fs)
            
            if i % 50 == 0 and i > 0:
                logger.info(f" Đã tải BCTC (2016-Nay): {i}/{len(tickers)}")
                # Sleep nhỏ để tránh bị block do rate limit
                time.sleep(1)
        except Exception as e:
            logger.error(f"Lỗi khi lấy BCTC mã {t}: {e}")
            
    if fs_dfs:
        df_all_fs = pd.concat(fs_dfs, ignore_index=True)
        save_to_parquet(df_all_fs, RAW_DIR / "financials_all.parquet")
        logger.info(f"Đã lưu Toàn bộ BCTC. (Tổng số dòng: {len(df_all_fs)})")
    
    # 3. Lấy dữ liệu OHLCV từ 2016
    logger.info(f"3. Lấy OHLCV từ 2016 cho {len(tickers)} mã...")
    ohlcv_dfs = []
    
    for i, t in enumerate(tickers):
        try:
            df_ohlcv = fetch_ohlcv_history(t, start_year=2016)
            if df_ohlcv is not None and not df_ohlcv.empty:
                ohlcv_dfs.append(df_ohlcv)
            
            if i % 100 == 0 and i > 0:
                logger.info(f" Đã tải OHLCV (2016-Nay): {i}/{len(tickers)}")
        except Exception as e:
            logger.error(f"Lỗi khi lấy OHLCV mã {t}: {e}")
            
    if ohlcv_dfs:
        df_all_ohlcv = pd.concat(ohlcv_dfs, ignore_index=True)
        save_to_parquet(df_all_ohlcv, RAW_DIR / "ohlcv_all.parquet")
        logger.info(f"Đã lưu Toàn bộ OHLCV. (Tổng số dòng: {len(df_all_ohlcv)})")

    logger.info("🎉 HOÀN TẤT TOÀN BỘ DATA INGESTION LỊCH SỬ!")

if __name__ == "__main__":
    run_ingestion()
