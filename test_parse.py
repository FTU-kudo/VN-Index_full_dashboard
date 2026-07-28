import json
import pandas as pd

with open('temp.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

details = data['response']['detail']
periods = data['response']['title']['data']

rows = []
for comp in details:
    for item in comp['data']:
        row = {
            'report_component': comp['report_component_name'],
            'field_name': item['field_name']
        }
        for i, val in enumerate(item['value']):
            if i < len(periods):
                p = periods[i]
                col = f"{p['year_period']}_{p['term_code']}"
                row[col] = val
        rows.append(row)

df = pd.DataFrame(rows)
print(df.head())
print(df.shape)
