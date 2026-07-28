import pandas as pd
import json
import math
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_Q_FILE = BASE_DIR / "data/processed/cstc_master_10yr.parquet"
DATA_Y_FILE = BASE_DIR / "data/processed/cstc_yearly_master_10yr.parquet"
OUTPUT_DIR = BASE_DIR / "dashboard/js"
OUTPUT_FILE = OUTPUT_DIR / "cstc_data.js"

def export_cstc():
    if not DATA_Q_FILE.exists():
        print(f"File {DATA_Q_FILE} not found!")
        return
        
    print("Reading CSTC Parquet (Quarterly)...")
    df_q = pd.read_parquet(DATA_Q_FILE, engine='fastparquet')
    
    print("Reading CSTC Parquet (Yearly)...")
    if DATA_Y_FILE.exists():
        df_y = pd.read_parquet(DATA_Y_FILE, engine='fastparquet')
    else:
        df_y = pd.DataFrame(columns=['Ticker', 'report_component', 'field_name'])
        
    print(f"Size Q: {df_q.shape}, Y: {df_y.shape}")
    
    # Merge on keys
    df = pd.merge(df_q, df_y, on=['Ticker', 'report_component', 'field_name'], how='outer')
    df = df.where(pd.notnull(df), None)
    
    period_columns_q = sorted([c for c in df_q.columns if c not in ['report_component', 'field_name', 'Ticker']], reverse=True)
    period_columns_y = sorted([c for c in df_y.columns if c not in ['report_component', 'field_name', 'Ticker']], reverse=True)
    
    title_data = []
    for p in period_columns_q:
        year, term = p.split('_')
        q = int(term.replace('Q', ''))
        title_data.append({
            "year_period": int(year),
            "term_code": term,
            "period_begin": int(f"{year}{(q - 1) * 3 + 1:02d}"),
            "period_end": int(f"{year}{q * 3:02d}"),
            "united": "Hợp nhất",
            "audited_status": "Chưa kiểm toán"
        })
        
    for p in period_columns_y:
        year, term = p.split('_')
        title_data.append({
            "year_period": int(year),
            "term_code": "Năm",
            "period_begin": int(f"{year}01"),
            "period_end": int(f"{year}12"),
            "united": "Hợp nhất",
            "audited_status": "Kiểm toán"
        })
    
    print("Processing data (Grouping)...")
    
    result = {}
    
    for _, row in df.iterrows():
        ticker = row['Ticker']
        comp = row['report_component']
        if not ticker or not comp: continue
        
        if ticker not in result:
            result[ticker] = {
                "title": { "data": title_data },
                "detail": []
            }
            
        comp_idx = next((i for i, c in enumerate(result[ticker]["detail"]) if c.get("report_component_name") == comp), -1)
                
        if comp_idx == -1:
            result[ticker]["detail"].append({
                "report_component_name": comp,
                "data": []
            })
            comp_idx = len(result[ticker]["detail"]) - 1
            
        field_data = {
            "field_name": row['field_name'],
            "value": []
        }
        
        all_periods = period_columns_q + period_columns_y
        for p in all_periods:
            val = row.get(p)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                field_data["value"].append(None)
            else:
                field_data["value"].append(val)
                
        result[ticker]["detail"][comp_idx]["data"].append(field_data)
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Writing cstc_data.js...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("// Yuanta Research - Chỉ số tài chính (CSTC) Offline Cache\n")
        f.write("window.YUANTA_CSTC_DATA = ")
        json.dump(result, f, ensure_ascii=False)
        f.write(";\n")
        
    print(f"Done! Size: {os.path.getsize(OUTPUT_FILE) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    export_cstc()
