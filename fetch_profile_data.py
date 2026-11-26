import json
import requests
from pathlib import Path
import time
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://ysradar.yuanta.com.vn/'
}

def load_universe_tickers(js_file_path):
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'window\.STOCK_UNIVERSE\s*=\s*(\[.*?\]);', content, re.DOTALL)
            if match:
                universe = json.loads(match.group(1))
                return [item['symbol'] for item in universe]
            else:
                print("Could not parse window.STOCK_UNIVERSE from the JS file.")
    except Exception as e:
        print(f"Error loading universe: {e}")
    
    return ["ACB", "VCB", "VIC", "VHM", "FPT", "MWG", "HPG", "SSI", "VNZ"]

def fetch_ticker_profile(ticker):
    result = {}
    urls = {
        "rating_info": f"https://ysradarapi.yuanta.com.vn/api/v3/stock_rating/info/{ticker}?lang=vi",
        "price_board": f"https://ysradarapi.yuanta.com.vn/api/v3/market_data/price_board/stock/list_stock_info?stock_list={ticker}&stock_type=ST",
        "rating_scores": f"https://ysradarapi.yuanta.com.vn/api/v3/market_data/price_board/stock/list_stock_rating_info?stock_list={ticker}&stock_type=ST",
        "shareholder": f"https://ysradarapi.yuanta.com.vn/ysw/api/v3/market_data/profile/shareholder?stock_code={ticker}",
        "profile_info": f"https://ysradarapi.yuanta.com.vn/ysw/api/v3/market_data/profile/info?stock_code={ticker}",
        "peers": f"https://ysradarapi.yuanta.com.vn/ysw/api/v3/market_data/profile/peers/{ticker}?num_peers=10"
    }
    
    session = requests.Session()
    for key, url in urls.items():
        try:
            resp = session.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if key in ["rating_info", "price_board", "rating_scores"]:
                    result[key] = data.get("response")
                else:
                    result[key] = data.get("data")
            else:
                result[key] = None
        except Exception:
            result[key] = None
            
    return ticker, result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=20)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    js_dir = base_dir / 'js'
    universe_file = js_dir / 'universe_data.js'
    out_file = js_dir / 'profile_data.js'
    
    tickers = load_universe_tickers(universe_file)
    print(f"Loaded {len(tickers)} tickers from universe_data.js")
    sys.stdout.flush()
    
    if args.limit:
        tickers = tickers[:args.limit]
        
    print(f"Starting multi-threaded profile sync for {len(tickers)} tickers using {args.workers} workers...")
    sys.stdout.flush()
    
    all_profiles = {}
    completed = 0
    total = len(tickers)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch_ticker_profile, t): t for t in tickers}
        
        for future in as_completed(futures):
            ticker = futures[future]
            completed += 1
            try:
                t, profile_data = future.result()
                all_profiles[t] = profile_data
                
                if completed % 50 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    print(f"[{completed}/{total}] {ticker} synced. ({rate:.1f} tickers/sec)")
                    sys.stdout.flush()
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                sys.stdout.flush()
                
    elapsed_total = time.time() - start_time
    print(f"\nAll {len(all_profiles)} profiles downloaded in {elapsed_total:.2f} seconds!")
    sys.stdout.flush()
    
    js_content = "// Auto-generated from Yuanta Free APIs (Full Market 1500+ Stocks)\n"
    js_content += f"window.YUANTA_PROFILE_DATA = {json.dumps(all_profiles, ensure_ascii=False)};\n"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Done! Profile data cache is now {out_file.stat().st_size / (1024*1024):.2f} MB.")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
