import pandas as pd
import json

df_fin = pd.read_parquet('data/raw/financials/DTP.parquet')
fields = df_fin['field_name'].unique().tolist()
with open('temp_fields.json', 'w', encoding='utf-8') as f:
    json.dump(fields, f, ensure_ascii=False, indent=2)

df_cstc = pd.read_parquet('data/raw/cstc/DTP.parquet')
with open('temp_cstc_cols.json', 'w', encoding='utf-8') as f:
    json.dump(df_cstc.columns.tolist(), f, ensure_ascii=False, indent=2)
    
df_cstc_sample = df_cstc.head(1).to_dict('records')
with open('temp_cstc_sample.json', 'w', encoding='utf-8') as f:
    json.dump(df_cstc_sample, f, ensure_ascii=False, indent=2)

df_fin_sample = df_fin.head(5).to_dict('records')
with open('temp_fin_sample.json', 'w', encoding='utf-8') as f:
    json.dump(df_fin_sample, f, ensure_ascii=False, indent=2)
