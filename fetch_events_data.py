import requests
import json
from pathlib import Path
from collections import defaultdict
import datetime

def main():
    url = "https://ysradarapi.yuanta.com.vn/ysw/api/v3/market_data/event"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://ysradar.yuanta.com.vn/'
    }
    
    events_by_ticker = defaultdict(list)
    page = 1
    page_size = 1000
    total_fetched = 0
    total_records = None
    
    current_year = datetime.datetime.now().year
    
    print("Fetching Yuanta Events Data...")
    
    while True:
        params = {
            "from": "2025-01-01",
            "to": f"{current_year+1}-12-31",
            "lang": "vi",
            "right_type": "annual_meeting,stock_dividend,stock_bonus,cash_dividend,rights_issue",
            "page": page,
            "page_size": page_size
        }
        
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code != 200:
                print(f"Error fetching page {page}: Status code {res.status_code}")
                break
                
            data = res.json()
            if not data.get('success'):
                break
                
            if total_records is None:
                total_records = data.get('totalRecords', 0)
                print(f"Total events available: {total_records}")
                
            items = data.get('data', [])
            if not items:
                break
                
            for item in items:
                ticker = item.get('StockCode')
                if ticker:
                    # Clean up the item before saving
                    clean_item = {
                        "Type": item.get("Type"),
                        "Content": item.get("Content"),
                        "ExRightDate": item.get("ExRightDate"),
                        "RecordDate": item.get("RecordDate"),
                        "EffectiveDate": item.get("EffectiveDate")
                    }
                    events_by_ticker[ticker].append(clean_item)
            
            total_fetched += len(items)
            print(f"Fetched page {page}... ({total_fetched}/{total_records})")
            
            if total_fetched >= total_records:
                break
                
            page += 1
            
        except Exception as e:
            print(f"Exception on page {page}: {e}")
            break
            
    # Save to file
    base_dir = Path(__file__).resolve().parent
    out_file = base_dir / 'js' / 'events_data.js'
    
    print(f"\nProcessing complete. Found events for {len(events_by_ticker)} tickers.")
    
    js_content = "// Auto-generated Events Data from Yuanta APIs\n"
    js_content += f"window.YUANTA_EVENTS_DATA = {json.dumps(events_by_ticker, ensure_ascii=False)};\n"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Wrote to {out_file} ({out_file.stat().st_size / 1024:.2f} KB)")

if __name__ == "__main__":
    main()
