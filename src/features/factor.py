# FILE: src/features/factor.py
from __future__ import annotations
import pandas as pd
from loguru import logger
import numpy as np

def extract_precomputed_ratios(df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Trích xuất EPS/BVPS/PE/PB/ROE/ROA đã được Yuanta tính sẵn
    từ section 'RATIOS' (norm_id 53,54,55,57,45,47).
    
    Parameters
    ----------
    df_master : pd.DataFrame
        DataFrame chứa dữ liệu raw từ API (long format hoặc pivot)
        Cần có cột 'norm_id', 'value', 'stock_code', 'period'.
        
    Returns
    -------
    pd.DataFrame
        DataFrame long format: (stock_code, period, ratio_name, value)
    """
    # Mapping norm_id to factor names based on Yuanta schema
    # 53: Trailing EPS, 54: BVPS, 55: P/E, 57: P/B, 45: ROE, 47: ROA
    ratio_mapping = {
        53: "Trailing_EPS",
        54: "BVPS",
        55: "PE",
        57: "PB",
        45: "ROE",
        47: "ROA"
    }
    
    if 'norm_id' in df_master.columns:
        df_ratios = df_master[df_master['norm_id'].isin(ratio_mapping.keys())].copy()
        df_ratios['ratio_name'] = df_ratios['norm_id'].map(ratio_mapping)
    else:
        logger.warning("norm_id not found in df_master, falling back to field_name matching.")
        # Fallback mapping based on field_name
        field_mapping = {
            "Trailing EPS": "Trailing_EPS",
            "EPS": "Trailing_EPS",
            "BVPS": "BVPS",
            "Giá trị sổ sách/CP (BVPS)": "BVPS",
            "P/E": "PE",
            "P/B": "PB",
            "ROE": "ROE",
            "ROA": "ROA"
        }
        mask = df_master['field_name'].isin(field_mapping.keys())
        df_ratios = df_master[mask].copy()
        df_ratios['ratio_name'] = df_ratios['field_name'].map(field_mapping)

    if df_ratios.empty:
        return pd.DataFrame(columns=['stock_code', 'period', 'ratio_name', 'value'])

    # Select only required columns if they exist
    req_cols = ['stock_code', 'period', 'ratio_name', 'value']
    available_cols = [c for c in req_cols if c in df_ratios.columns]
    
    return df_ratios[available_cols]


def build_factor_panel(
    df_master: pd.DataFrame,
    latest_only: bool = True
) -> pd.DataFrame:
    """
    Pipeline hoàn chỉnh: raw BCTC → factor panel.
    1. extract_precomputed_ratios() — lấy từ Yuanta
    2. compute_ratios() — tính thêm các ratio chưa có sẵn (FCF, accruals, growth)
    3. Merge, deduplicate (precomputed wins), winsorize, z-score
    4. Return: wide DataFrame (stock_code × factor_name = z-score)
    """
    logger.info("Extracting precomputed ratios from master data")
    df_precomputed = extract_precomputed_ratios(df_master)
    
    df_factors = df_precomputed.copy()
    
    if df_factors.empty:
        logger.warning("No factor data extracted.")
        return pd.DataFrame()

    if latest_only and 'period' in df_factors.columns:
        latest_periods = df_factors.groupby('stock_code')['period'].max().reset_index()
        df_factors = df_factors.merge(latest_periods, on=['stock_code', 'period'])

    # Pivot to wide format
    if 'stock_code' in df_factors.columns and 'ratio_name' in df_factors.columns and 'value' in df_factors.columns:
        df_wide = df_factors.pivot_table(
            index='stock_code', 
            columns='ratio_name', 
            values='value',
            aggfunc='last'
        ).reset_index()
    else:
        # If schema is different, just return raw
        return df_factors

    # Winsorize and Z-score (Cross-sectional normalization)
    numeric_cols = df_wide.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Simple winsorization at 1% and 99%
        lower, upper = df_wide[col].quantile([0.01, 0.99])
        df_wide[col] = np.clip(df_wide[col], lower, upper)
        
        # Z-score standard normalization
        mean = df_wide[col].mean()
        std = df_wide[col].std()
        if std > 0:
            df_wide[col] = (df_wide[col] - mean) / std
        else:
            df_wide[col] = 0

    logger.success(f"Built factor panel for {len(df_wide)} stocks.")
    return df_wide
