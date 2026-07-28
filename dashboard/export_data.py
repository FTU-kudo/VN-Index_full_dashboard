import pandas as pd
import json
from pathlib import Path
import os
import math

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data/processed/financials_master_10yr.parquet"
OUTPUT_DIR = BASE_DIR / "dashboard/js"
OUTPUT_FILE = OUTPUT_DIR / "data.js"

def export_data():
    if not DATA_FILE.exists():
        print(f"File {DATA_FILE} not found!")
        return
        
    print("Reading Parquet...")
    df = pd.read_parquet(DATA_FILE, engine='fastparquet')
    
    print(f"Size: {df.shape}")
    
    df = df.where(pd.notnull(df), None)
    
    print("Processing data (Grouping)...")
    
    period_columns = [col for col in df.columns if col not in ['report_component', 'field_name', 'Ticker']]
    period_columns = sorted(period_columns, reverse=True)
    
    result = {}
    
    for _, row in df.iterrows():
        ticker = row['Ticker']
        if not ticker: continue
        
        comp = row['report_component']
        if not comp: continue
        
        if ticker not in result:
            result[ticker] = {}
            
        if comp not in result[ticker]:
            result[ticker][comp] = []
            
        field_data = { "field": row['field_name'] }
        
        for p in period_columns:
            val = row[p]
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                field_data[p] = val
                
        result[ticker][comp].append(field_data)
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Writing data.js...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("window.PERIODS = " + json.dumps(period_columns) + ";\n")
        f.write("window.BCTC_DATA = ")
        json.dump(result, f, ensure_ascii=False)
        f.write(";\n")
        
    print(f"Done! Size: {os.path.getsize(OUTPUT_FILE) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    export_data()
