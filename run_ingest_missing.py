import sys
from pathlib import Path
import logging
import time
import pandas as pd

# Thêm root dự án vào sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from config.settings import PROCESSED_DIR, RAW_DIR
from src.data.market_data import fetch_all_tickers
from src.data.fundamental import fetch_financial_statements
from src.data.storage import save_to_parquet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ingestion():
    logger.info("1. Bắt đầu lấy danh sách toàn bộ cổ phiếu (Universe)...")
    tickers = fetch_all_tickers()
    logger.info(f"Đã lấy được {len(tickers)} mã cổ phiếu.")
    
    # Chỉ tải dữ liệu Báo cáo tài chính còn thiếu
    logger.info(f"2. Lấy Báo cáo tài chính (Q2/2023) cho {len(tickers)} mã...")
    fs_dfs = []
    
    for i, t in enumerate(tickers):
        try:
            df_fs = fetch_financial_statements(t, term="Q2", year=2023)
            if df_fs is not None and not df_fs.empty:
                df_fs['Ticker'] = t
                fs_dfs.append(df_fs)
            if i % 50 == 0 and i > 0:
                logger.info(f" Đã tải BCTC: {i}/{len(tickers)}")
        except Exception as e:
            logger.error(f"Lỗi khi lấy BCTC mã {t}: {e}")
            
    if fs_dfs:
        df_all_fs = pd.concat(fs_dfs, ignore_index=True)
        save_to_parquet(df_all_fs, RAW_DIR / "financials_Q2_2023.parquet")
        logger.info(f"Đã lưu Toàn bộ Báo cáo tài chính. (Tổng số dòng: {len(df_all_fs)})")
    else:
        logger.warning("Không có dữ liệu BCTC nào được tải!")
        
    logger.info("🎉 HOÀN TẤT DATA INGESTION CHO DỮ LIỆU CÒN THIẾU!")

if __name__ == "__main__":
    run_ingestion()
