import json
import asyncio
import aiohttp
from pathlib import Path
import time
import re
import argparse
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://ysradar.yuanta.com.vn/'
}

CHART_TYPES = [
    "net_revenue", "net_profit", "valuation", "equity", 
    "structure_asset", "profit_margin", "equity_used_ratio", 
    "accounting_balance", "cash_flow", "asset", "liquidity_ability"
]

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
    return ["ACB", "VIC", "FPT", "HPG", "SSI", "SJF"]

async def fetch_chart(session, semaphore, ticker, chart_type, term_type):
    url = "https://ysradarapi.yuanta.com.vn/api/v3/vietstock/financial_statement/recommend_chart"
    params = {
        "chart_type": chart_type,
        "lang": "vi",
        "report_term_type": str(term_type),
        "stock_code": ticker,
        "unit": "1000000000",
        "year_period": "2016"
    }
    async with semaphore:
        try:
            async with session.get(url, params=params, headers=HEADERS, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        res = data.get("response")
                        if res and res.get("data") and len(res.get("data")) > 0:
                            return f"{chart_type}_{term_type}", res
        except Exception:
            pass
    return f"{chart_type}_{term_type}", None

async def fetch_ticker_all_charts(session, semaphore, ticker):
    tasks = []
    # Fetch both Yearly (1) and Quarterly (2) for all 11 chart types
    for chart_type in CHART_TYPES:
        tasks.append(fetch_chart(session, semaphore, ticker, chart_type, 1))
        tasks.append(fetch_chart(session, semaphore, ticker, chart_type, 2))
    
    results = await asyncio.gather(*tasks)
    
    ticker_data = {}
    for key, data in results:
        if data:
            ticker_data[key] = data
            
    return ticker, ticker_data

async def main_async(tickers, workers):
    semaphore = asyncio.Semaphore(workers)
    all_charts = {}
    total = len(tickers)
    completed = 0
    start_time = time.time()
    
    print(f"Starting async chart sync for {total} tickers with {workers} workers (total {total*22} requests)...")
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_ticker_all_charts(session, semaphore, ticker) for ticker in tickers]
        for coro in asyncio.as_completed(tasks):
            ticker, ticker_data = await coro
            if ticker_data:
                all_charts[ticker] = ticker_data
            
            completed += 1
            if completed % 10 == 0 or completed == total:
                elapsed = time.time() - start_time
                rate = completed / elapsed
                print(f"[{completed}/{total}] {ticker} processed. ({rate:.1f} tickers/sec)")
                sys.stdout.flush()
                
    elapsed_total = time.time() - start_time
    print(f"\nCompleted {completed} tickers in {elapsed_total:.2f} seconds!")
    return all_charts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=30)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    js_dir = base_dir / 'js'
    universe_file = js_dir / 'universe_data.js'
    out_file = js_dir / 'chart_data.js'
    
    tickers = load_universe_tickers(universe_file)
    if args.limit:
        tickers = tickers[:args.limit]
        
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    all_charts = asyncio.run(main_async(tickers, args.workers))
    
    print(f"Writing data to {out_file}...")
    js_content = "// Auto-generated Chart Data from Yuanta APIs\n"
    js_content += f"window.YUANTA_CHART_DATA = {json.dumps(all_charts, ensure_ascii=False)};\n"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Done! Chart data cache size: {out_file.stat().st_size / (1024*1024):.2f} MB.")

if __name__ == '__main__':
    main()
