import json
import requests
import os
import re
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://ysradarapi.yuanta.com.vn/api/v3/vietstock/financial_statement/report"

def load_universe_tickers(js_file_path):
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'window\.STOCK_UNIVERSE\s*=\s*(\[.*?\]);', content, re.DOTALL)
            if match:
                universe = json.loads(match.group(1))
                return [item['symbol'] for item in universe]
    except Exception as e:
        print(f"Error loading universe: {e}")
    return ["ACB", "VCB", "VIC", "VHM", "FPT", "MWG", "HPG", "SSI", "VNZ"]

def fetch_cstc_for_ticker(ticker, term="Q2", year=2026, pages=7):
    merged_data = None
    try:
        for page in range(1, pages + 1):
            params = {
                "lang": "vi",
                "page_index": page,
                "page_size": 6,  # Yuanta forces 6 per page for CSTC
                "report_term_type": 2, # 2 = Quý, 1 = Năm
                "report_type": "CSTC",
                "stock_code": ticker,
                "term_code": term,
                "unit": 1000000,
                "year_period": year
            }
            r = requests.get(BASE_URL, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and "response" in data:
                    page_resp = data["response"]
                    if not merged_data:
                        merged_data = page_resp
                    else:
                        # Merge title data
                        if "title" in page_resp and "data" in page_resp["title"]:
                            merged_data["title"]["data"].extend(page_resp["title"]["data"])
                        # Merge detail data
                        if "detail" in page_resp and "detail" in merged_data:
                            for g1, g2 in zip(merged_data["detail"], page_resp["detail"]):
                                if "data" in g1 and "data" in g2:
                                    for item1, item2 in zip(g1["data"], g2["data"]):
                                        if item1.get("field_name") == item2.get("field_name") and "value" in item1 and "value" in item2:
                                            item1["value"].extend(item2["value"])
            else:
                break # Stop if API fails
        
        if merged_data:
            return ticker, merged_data
    except Exception as e:
        print(f"Error fetching CSTC for {ticker}: {e}")
    return ticker, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=10)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    js_dir = os.path.join(os.path.dirname(__file__), "js")
    universe_file = os.path.join(js_dir, 'universe_data.js')
    tickers = load_universe_tickers(universe_file)
    
    if args.limit:
        tickers = tickers[:args.limit]
        
    print(f"Starting multi-threaded CSTC sync for {len(tickers)} tickers using {args.workers} workers...")
    
    cstc_db = {}
    completed = 0
    total = len(tickers)
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch_cstc_for_ticker, t): t for t in tickers}
        for future in as_completed(futures):
            ticker, res = future.result()
            completed += 1
            if res:
                cstc_db[ticker] = res
                
            if completed % 50 == 0 or completed == total:
                elapsed = time.time() - start_time
                rate = completed / elapsed
                print(f"[{completed}/{total}] {ticker} CSTC synced. ({rate:.1f} tickers/sec)")
            
    out_path = os.path.join(js_dir, "cstc_data.js")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("// Yuanta Research - Chỉ số tài chính (CSTC) Realtime API Cache\n")
        f.write("window.YUANTA_CSTC_DATA = ")
        json.dump(cstc_db, f, ensure_ascii=False)
        f.write(";\n")
        
    print(f"Successfully exported CSTC data for {len(cstc_db)} tickers to {out_path} in {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    main()
