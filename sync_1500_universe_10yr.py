import sys
import argparse
import logging
import time
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
sys.path.append(str(Path(__file__).resolve().parent))

from config.settings import RAW_DIR, PROCESSED_DIR
from src.data.market_data import fetch_all_tickers
from src.data.fundamental import fetch_financial_statements_history, fetch_financial_ratios_history, fetch_financial_ratios_history_yearly
from src.data.history import fetch_ohlcv_history
from src.data.storage import save_to_parquet, load_from_parquet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("QuantDataEngine")

def sync_single_ticker(ticker: str, start_year: int = 2016, force: bool = False):
    ohlcv_path = RAW_DIR / "ohlcv" / f"{ticker}.parquet"
    bctc_path = RAW_DIR / "financials" / f"{ticker}.parquet"
    cstc_path = RAW_DIR / "cstc" / f"{ticker}.parquet"
    cstc_yearly_path = RAW_DIR / "cstc_yearly" / f"{ticker}.parquet"
    
    if not force and ohlcv_path.exists() and bctc_path.exists() and cstc_path.exists() and cstc_yearly_path.exists():
        return ticker, "SKIPPED", 0, 0, 0, 0

    ohlcv_rows, bctc_rows, cstc_rows, cstc_yearly_rows = 0, 0, 0, 0

    # 1. Fetch 10-Year OHLCV Daily Price History
    try:
        if force or not ohlcv_path.exists():
            df_ohlcv = fetch_ohlcv_history(ticker, start_year=start_year)
            if not df_ohlcv.empty:
                save_to_parquet(df_ohlcv, ohlcv_path)
                ohlcv_rows = len(df_ohlcv)
    except Exception as e:
        logger.warning(f"Failed OHLCV for {ticker}: {e}")

    # 2. Fetch 10-Year BCTC Quarterly Financial Statements
    try:
        if force or not bctc_path.exists():
            df_bctc = fetch_financial_statements_history(ticker, start_year=start_year, report_type="BCTT")
            if not df_bctc.empty:
                df_bctc['Ticker'] = ticker
                save_to_parquet(df_bctc, bctc_path)
                bctc_rows = len(df_bctc)
    except Exception as e:
        logger.warning(f"Failed BCTC for {ticker}: {e}")

    # 3. Fetch 10-Year CSTC Quarterly Financial Ratios
    try:
        if force or not cstc_path.exists():
            df_cstc = fetch_financial_ratios_history(ticker, start_year=start_year)
            if not df_cstc.empty:
                df_cstc['Ticker'] = ticker
                save_to_parquet(df_cstc, cstc_path)
                cstc_rows = len(df_cstc)
    except Exception as e:
        logger.warning(f"Failed CSTC for {ticker}: {e}")

    # 4. Fetch 10-Year CSTC Yearly Financial Ratios
    try:
        if force or not cstc_yearly_path.exists():
            df_cstc_y = fetch_financial_ratios_history_yearly(ticker, start_year=start_year)
            if not df_cstc_y.empty:
                df_cstc_y['Ticker'] = ticker
                save_to_parquet(df_cstc_y, cstc_yearly_path)
                cstc_yearly_rows = len(df_cstc_y)
    except Exception as e:
        logger.warning(f"Failed CSTC Yearly for {ticker}: {e}")

    return ticker, "SUCCESS", ohlcv_rows, bctc_rows, cstc_rows, cstc_yearly_rows

def merge_data_lake():
    logger.info("Merging partitioned Parquet datasets into Master Institutional Data Lake...")
    
    # Merge OHLCV
    ohlcv_files = list((RAW_DIR / "ohlcv").glob("*.parquet"))
    if ohlcv_files:
        logger.info(f"Combining {len(ohlcv_files)} OHLCV parquet files...")
        dfs = [load_from_parquet(p) for p in ohlcv_files]
        dfs = [df for df in dfs if not df.empty]
        if dfs:
            df_master_ohlcv = pd.concat(dfs, ignore_index=True)
            save_to_parquet(df_master_ohlcv, PROCESSED_DIR / "ohlcv_master_10yr.parquet")
            logger.info(f"Saved master OHLCV dataset: {len(df_master_ohlcv)} total rows.")

    # Merge Financials
    bctc_files = list((RAW_DIR / "financials").glob("*.parquet"))
    if bctc_files:
        logger.info(f"Combining {len(bctc_files)} BCTC financial parquet files...")
        dfs = [load_from_parquet(p) for p in bctc_files]
        dfs = [df for df in dfs if not df.empty]
        if dfs:
            df_master_bctc = pd.concat(dfs, ignore_index=True)
            save_to_parquet(df_master_bctc, PROCESSED_DIR / "financials_master_10yr.parquet")
            logger.info(f"Saved master BCTC financial dataset: {len(df_master_bctc)} total rows.")

    # Merge CSTC Ratios
    cstc_files = list((RAW_DIR / "cstc").glob("*.parquet"))
    if cstc_files:
        logger.info(f"Combining {len(cstc_files)} CSTC financial ratio parquet files...")
        dfs = [load_from_parquet(p) for p in cstc_files]
        dfs = [df for df in dfs if not df.empty]
        if dfs:
            df_master_cstc = pd.concat(dfs, ignore_index=True)
            save_to_parquet(df_master_cstc, PROCESSED_DIR / "cstc_master_10yr.parquet")
            logger.info(f"Saved master CSTC financial ratio dataset: {len(df_master_cstc)} total rows.")

    # Merge CSTC Yearly Ratios
    cstc_y_files = list((RAW_DIR / "cstc_yearly").glob("*.parquet"))
    if cstc_y_files:
        logger.info(f"Combining {len(cstc_y_files)} CSTC Yearly parquet files...")
        dfs = [load_from_parquet(p) for p in cstc_y_files]
        dfs = [df for df in dfs if not df.empty]
        if dfs:
            df_master_cstc_y = pd.concat(dfs, ignore_index=True)
            save_to_parquet(df_master_cstc_y, PROCESSED_DIR / "cstc_yearly_master_10yr.parquet")
            logger.info(f"Saved master CSTC Yearly dataset: {len(df_master_cstc_y)} total rows.")

def run_pipeline(args):
    logger.info(f"=== QUANT DATA ENGINE: 1,500 STOCK UNIVERSE & 10-YEAR DEPTH SYNC ===")
    
    # Load Universe
    univ_path = RAW_DIR / "universe" / "vietnam_1500_universe.parquet"
    if univ_path.exists():
        df_univ = load_from_parquet(univ_path)
        tickers = df_univ['symbol'].tolist()
        logger.info(f"Loaded master universe dataset from Parquet: {len(tickers)} symbols across HOSE, HNX, UPCOM.")
    else:
        logger.info("Master universe Parquet not found. Fetching live from APIs...")
        tickers = fetch_all_tickers()
        logger.info(f"Fetched {len(tickers)} symbols dynamically.")

    if args.limit and args.limit > 0:
        tickers = tickers[:args.limit]
        logger.info(f"Restricted sync to first {len(tickers)} symbols as per limit argument.")

    start_time = time.time()
    completed = 0
    skipped = 0

    logger.info(f"Starting Multi-Threaded Ingestion (Workers: {args.workers}, Start Year: {args.start_year})...")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(sync_single_ticker, t, args.start_year, args.force): t for t in tickers}
        
        for future in as_completed(futures):
            t = futures[future]
            completed += 1
            try:
                ticker, status, o_rows, b_rows, c_rows, cy_rows = future.result()
                if status == "SKIPPED":
                    skipped += 1
                else:
                    logger.info(f"[{completed}/{len(tickers)}] {ticker} | Status: {status} | OHLCV: {o_rows} | BCTC: {b_rows} | CSTC: {c_rows} | CSTC-Y: {cy_rows}")
            except Exception as exc:
                logger.error(f"[{completed}/{len(tickers)}] {t} threw exception: {exc}")

            if completed % 50 == 0:
                elapsed = time.time() - start_time
                logger.info(f"--> Progress: {completed}/{len(tickers)} ({completed*100/len(tickers):.1f}%) in {elapsed:.1f}s (Skipped: {skipped})")

    elapsed_total = time.time() - start_time
    logger.info(f"🎉 INGESTION COMPLETED for {len(tickers)} tickers in {elapsed_total:.2f}s (Successfully fetched: {completed-skipped}, Cached/Skipped: {skipped}).")
    
    if args.merge:
        merge_data_lake()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vietnam 1,500 Stocks 10-Year Quant Data Lake Sync")
    parser.add_argument("--limit", type=int, default=15, help="Number of tickers to process (0 or default 15 for demonstration, pass 1500 for full production run)")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent worker threads")
    parser.add_argument("--start-year", type=int, default=2016, help="Starting year for depth history")
    parser.add_argument("--force", action="store_true", help="Force resync even if local Parquet exists")
    parser.add_argument("--merge", action="store_true", help="Merge partitioned Parquet files into unified master datasets at completion")
    
    args = parser.parse_args()
    run_pipeline(args)
