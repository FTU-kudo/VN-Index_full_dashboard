import json
import requests
import re
from pathlib import Path
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
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
    except Exception as e:
        print(f"Error loading universe: {e}")
    return []

def fetch_correlate(stock_code):
    chart_types = [
        'ASSESSMENT_CRITERIAL', 
        'MANAGEMENT_ABILITY', 
        'PERFORMANCE', 
        'GROWTH_RATE', 
        'LIQUIDITY', 
        'PROFITABILITY'
    ]
    url = 'https://ysradarapi.yuanta.com.vn/ysw/api/v3/stock_rating/correlate?lang=vi'
    
    result = {}
    for ctype in chart_types:
        payload = {'stock_code': [stock_code], 'icb_level': 2, 'chart_type': ctype}
        try:
            res = requests.post(url, json=payload, headers=HEADERS, timeout=5)
            if res.status_code == 200:
                data = res.json().get('data')
                if data and 'Data' in data:
                    result[ctype] = data
        except Exception as e:
            pass
            
    if result:
        return stock_code, result
    return stock_code, None

def main():
    base_dir = Path(__file__).resolve().parent
    universe_file = base_dir / 'js' / 'universe_data.js'
    
    tickers = load_universe_tickers(universe_file)
    print(f"Loaded {len(tickers)} tickers from universe_data.js")
    if not tickers:
        print('Failed to get tickers')
        return
    
    all_correlates = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_correlate, t): t for t in tickers}
        for future in as_completed(futures):
            t, data = future.result()
            if data:
                all_correlates[t] = data
            completed += 1
            print(f'[{completed}/{len(tickers)}] {t} correlate fetched.')
            sys.stdout.flush()

    base_dir = Path(__file__).resolve().parent
    out_file = base_dir / 'js' / 'correlate_data.js'
    
    js_content = "// Auto-generated Correlate Data\n"
    js_content += f"window.YUANTA_CORRELATE = {json.dumps(all_correlates, ensure_ascii=False)};\n"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print('Done fetching Correlate data!')

if __name__ == '__main__':
    main()
