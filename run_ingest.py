import sys
from pathlib import Path
import logging
import time
import pandas as pd

# Thêm root dự án vào sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from config.settings import PROCESSED_DIR, RAW_DIR
from src.data.market_data import fetch_all_tickers, fetch_tickers_by_sector
from src.data.realtime import fetch_realtime_prices, fetch_stock_ratings
from src.data.fundamental import fetch_financial_statements, fetch_stock_info_basic
from src.data.storage import save_to_parquet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ingestion():
    logger.info("1. Bắt đầu lấy danh sách toàn bộ cổ phiếu (Universe)...")
    tickers = fetch_all_tickers()
    logger.info(f"Đã lấy được {len(tickers)} mã cổ phiếu.")
    
    # 6. Lấy danh sách cổ phiếu theo nhóm ngành
    logger.info("2. Lấy danh sách cổ phiếu theo nhóm ngành...")
    df_sectors = fetch_tickers_by_sector()
    save_to_parquet(df_sectors, PROCESSED_DIR / "sectors.parquet")
    logger.info(f"Đã lưu danh sách nhóm ngành ({len(df_sectors)} bản ghi).")
    
    # 3 & 4. Lấy Realtime Prices & Ratings (Sử dụng Chunking nên rất nhanh cho 1700 mã)
    logger.info("3. Lấy Realtime Prices cho toàn bộ mã...")
    df_prices = fetch_realtime_prices(tickers)
    save_to_parquet(df_prices, PROCESSED_DIR / "realtime_prices.parquet")
    logger.info(f"Đã lưu Realtime Prices ({len(df_prices)} bản ghi).")
    
    logger.info("4. Lấy Stock Ratings cho toàn bộ mã...")
    df_ratings = fetch_stock_ratings(tickers)
    save_to_parquet(df_ratings, PROCESSED_DIR / "stock_ratings.parquet")
    logger.info(f"Đã lưu Stock Ratings ({len(df_ratings)} bản ghi).")

    # 2. Lấy Thông tin cơ bản (Phải lặp qua từng mã)
    logger.info(f"5. Lấy Thông tin cơ bản cho {len(tickers)} mã...")
    info_dfs = []
    for i, t in enumerate(tickers):
        df_info = fetch_stock_info_basic(t)
        if not df_info.empty:
            info_dfs.append(df_info)
        if i % 100 == 0 and i > 0:
            logger.info(f" Đã tải thông tin cơ bản: {i}/{len(tickers)}")
    if info_dfs:
        df_all_info = pd.concat(info_dfs, ignore_index=True)
        save_to_parquet(df_all_info, PROCESSED_DIR / "stock_info.parquet")
        logger.info("Đã lưu Toàn bộ Thông tin cơ bản.")

    # 1. Lấy Báo cáo tài chính (Q2/2023 - Lấy mẫu 1 quý gần đây cho toàn bộ mã)
    logger.info(f"6. Lấy Báo cáo tài chính (Q2/2023) cho {len(tickers)} mã...")
    fs_dfs = []
    for i, t in enumerate(tickers):
        df_fs = fetch_financial_statements(t, term="Q2", year=2023)
        if not df_fs.empty:
            df_fs['Ticker'] = t
            fs_dfs.append(df_fs)
        if i % 100 == 0 and i > 0:
            logger.info(f" Đã tải BCTC: {i}/{len(tickers)}")
    if fs_dfs:
        df_all_fs = pd.concat(fs_dfs, ignore_index=True)
        save_to_parquet(df_all_fs, RAW_DIR / "financials_Q2_2023.parquet")
        logger.info("Đã lưu Toàn bộ Báo cáo tài chính.")
        
    logger.info("🎉 HOÀN TẤT DATA INGESTION!")

if __name__ == "__main__":
    run_ingestion()
