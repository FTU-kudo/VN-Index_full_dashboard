import pandas as pd

try:
    df_fin = pd.read_parquet('data/raw/financials_all.parquet')
    print('=== Financials ===')
    print(f'Shape: {df_fin.shape}')
    if 'Ticker' in df_fin.columns:
        print(f"Unique Tickers: {df_fin['Ticker'].nunique()}")
    else:
        print("No Ticker column")
    
    cols = list(df_fin.columns)
    print(f"Columns sample: {cols[:5]} ... {cols[-5:]}")
except Exception as e:
    print(f"Error reading financials_all.parquet: {e}")

try:
    df_ohlcv = pd.read_parquet('data/raw/ohlcv_all.parquet')
    print('\n=== OHLCV ===')
    print(f'Shape: {df_ohlcv.shape}')
    if 'Ticker' in df_ohlcv.columns:
        print(f"Unique Tickers: {df_ohlcv['Ticker'].nunique()}")
    elif 'ticker' in df_ohlcv.columns:
        print(f"Unique Tickers: {df_ohlcv['ticker'].nunique()}")
    else:
        print("No Ticker column")
    
    if 'Date' in df_ohlcv.columns:
        print(f"Min Date: {df_ohlcv['Date'].min()}")
        print(f"Max Date: {df_ohlcv['Date'].max()}")
    elif 'time' in df_ohlcv.columns:
        print(f"Min Date: {df_ohlcv['time'].min()}")
        print(f"Max Date: {df_ohlcv['time'].max()}")
except Exception as e:
    print(f"Error reading ohlcv_all.parquet: {e}")
