import sys
import json
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.data.market_data import fetch_tickers_by_exchange, fetch_tickers_by_sector
from src.data.storage import save_to_parquet
from config.settings import RAW_DIR

def build_universe():
    print("Fetching sectors mapping...")
    sector_df = fetch_tickers_by_sector()
    ticker_to_sector = {}
    if not sector_df.empty:
        for idx, row in sector_df.iterrows():
            sec = row.get('Sector', '')
            stocks = row.get('Stocks', '')
            if isinstance(stocks, str):
                for s in stocks.split(','):
                    s_clean = s.strip().upper()
                    if s_clean:
                        ticker_to_sector[s_clean] = sec
            elif isinstance(stocks, list):
                for s in stocks:
                    if isinstance(s, str):
                        ticker_to_sector[s.strip().upper()] = sec
                    elif isinstance(s, dict) and 'StockCode' in s:
                        ticker_to_sector[s['StockCode'].strip().upper()] = sec

    all_stocks = []
    for ex_code, ex_name in [("HSX", "HOSE"), ("HNX", "HNX"), ("UPCOM", "UPCOM")]:
        print(f"Fetching tickers for exchange: {ex_name}...")
        df = fetch_tickers_by_exchange(ex_code)
        if not df.empty and 'StockCode' in df.columns:
            for _, row in df.iterrows():
                code = str(row['StockCode']).strip().upper()
                # Exclude warrants or long bond codes, keep normal stock symbols (3-4 letters)
                if 2 <= len(code) <= 4 and code.isalnum():
                    all_stocks.append({
                        "symbol": code,
                        "exchange": ex_name,
                        "price": float(row.get('LastMP', 0)),
                        "volume": float(row.get('TotalVol', 0)),
                        "sector": ticker_to_sector.get(code, "Đa ngành / Chung")
                    })

    # Sort alphabetically by symbol
    all_stocks = sorted(all_stocks, key=lambda x: x['symbol'])
    print(f"Total compiled stock universe count: {len(all_stocks)}")
    
    # Save to Parquet Data Lake
    df_univ = pd.DataFrame(all_stocks)
    parquet_path = RAW_DIR / "universe" / "vietnam_1500_universe.parquet"
    save_to_parquet(df_univ, parquet_path)
    print(f"Saved master universe dataset to Parquet: {parquet_path}")

    # Save to Web Dashboard cache
    out_js = Path(__file__).resolve().parent / "js" / "universe_data.js"
    with open(out_js, "w", encoding="utf-8") as f:
        f.write("// Master Stock Universe - ~1500 stocks across HOSE, HNX, UPCOM\n")
        f.write("window.STOCK_UNIVERSE = ")
        json.dump(all_stocks, f, indent=1, ensure_ascii=False)
        f.write(";\n")
    print(f"Exported dashboard universe array to: {out_js}")

if __name__ == "__main__":
    build_universe()
