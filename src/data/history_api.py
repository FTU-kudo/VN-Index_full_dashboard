"""
src/data/history_api.py — Historical OHLCV + Foreign Flow API wrappers.

Hai endpoint mới xác nhận 27/07/2026:
  GET /api/v3/market_data/market_watch/price_history/{code}
      ?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD
  GET /api/v3/market_data/market_watch/price_history_foreign/{code}
      ?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD

Đặc điểm:
  - Trả về toàn bộ lịch sử trong 1 request (không paginate) cho range ~10 năm
  - ForeignVolumeBuy/Sell có trong cả 2 endpoint nhưng BuyVal/SellVal chỉ ở endpoint 11
  - TradingDate là string "YYYY-MM-DD", cần parse sang date object
  - Merge 2 endpoint theo TradingDate để có record đầy đủ nhất
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from src.data.yuanta_client import YuantaAPIClient

logger = logging.getLogger(__name__)

# Default date range: từ 2016-01-01 đến hôm nay
DEFAULT_FROM = "2016-01-01"

# Các cột OHLCV raw từ Endpoint 10
OHLCV_FIELDS_RAW = [
    "TradingDate", "PerChange", "Close", "Open", "Highest", "Lowest",
    "Average", "Volume", "Value", "ForeignVolumeBuy", "ForeignVolumeSell",
    "PutThroughVolume", "PutThroughValue",
]

# Các cột Foreign raw từ Endpoint 11
FOREIGN_FIELDS_RAW = [
    "TradingDate", "RemainRoom", "BuyVol", "BuyVal", "SellVol", "SellVal",
    "NetVol", "NetVal", "ForeignValRate", "ForeignOwnedRate",
]

# Map sang snake_case
OHLCV_RENAME = {
    "TradingDate":       "trading_date",
    "PerChange":         "per_change",
    "Close":             "close",
    "Open":              "open_price",
    "Highest":           "high",
    "Lowest":            "low",
    "Average":           "average",
    "Volume":            "volume",
    "Value":             "value",
    "ForeignVolumeBuy":  "ft_buy_vol",
    "ForeignVolumeSell": "ft_sell_vol",
    "PutThroughVolume":  "put_through_vol",
    "PutThroughValue":   "put_through_val",
}

FOREIGN_RENAME = {
    "TradingDate":       "trading_date",
    "RemainRoom":        "remain_room",
    "BuyVol":            "ft_buy_vol",
    "BuyVal":            "ft_buy_val",
    "SellVol":           "ft_sell_vol",
    "SellVal":           "ft_sell_val",
    "NetVol":            "ft_net_vol",
    "NetVal":            "ft_net_val",
    "ForeignValRate":    "ft_val_rate",
    "ForeignOwnedRate":  "ft_owned_rate",
}


def _today() -> str:
    return date.today().isoformat()


def _extract_response(raw) -> list[dict]:
    """Trích xuất list records từ response Yuanta (key = 'response')."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        resp = raw.get("response", [])
        return resp if isinstance(resp, list) else []
    return []


def _parse_date_col(df: pd.DataFrame) -> pd.DataFrame:
    """Parse cột trading_date từ string YYYY-MM-DD sang Python date."""
    if "trading_date" in df.columns:
        df["trading_date"] = pd.to_datetime(df["trading_date"]).dt.date
    return df


# ── OHLCV ─────────────────────────────────────────────────────────────────────

def fetch_ohlcv_history_yuanta(
    ticker: str,
    from_date: str = DEFAULT_FROM,
    to_date: Optional[str] = None,
    client: Optional[YuantaAPIClient] = None,
) -> pd.DataFrame:
    """
    Lịch sử giá OHLCV + Foreign Volume từ Endpoint 10 (price_history).

    Returns DataFrame với columns snake_case, sort theo trading_date tăng dần.
    Khoảng ~2,500 rows cho 10 năm (toàn bộ trả về trong 1 request).

    Parameters
    ----------
    ticker    : Mã cổ phiếu (VD: "ACB")
    from_date : Ngày bắt đầu, mặc định 2016-01-01
    to_date   : Ngày kết thúc, mặc định hôm nay
    client    : YuantaAPIClient instance, tạo mới nếu None
    """
    to_date = to_date or _today()
    _client = client or YuantaAPIClient()
    ticker = ticker.upper()

    logger.debug(f"[OHLCV] Fetch {ticker}: {from_date} → {to_date}")

    try:
        raw = _client.get(
            f"market_data/market_watch/price_history/{ticker}",
            params={"from_date": from_date, "to_date": to_date},
        )
    except Exception as exc:
        logger.error(f"[OHLCV] {ticker}: request failed — {exc}")
        return pd.DataFrame()

    rows = _extract_response(raw)
    if not rows:
        logger.warning(f"[OHLCV] {ticker}: empty response")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Giữ chỉ các cột đã xác nhận + rename
    existing = [c for c in OHLCV_FIELDS_RAW if c in df.columns]
    df = df[existing].rename(columns={k: v for k, v in OHLCV_RENAME.items() if k in existing})
    df["stock_code"] = ticker
    df = _parse_date_col(df)

    # Đảm bảo các cột optional tồn tại với giá trị mặc định
    for col, default in [("ft_buy_vol", 0.0), ("ft_sell_vol", 0.0),
                         ("put_through_vol", 0.0), ("put_through_val", 0.0)]:
        if col not in df.columns:
            df[col] = default

    # Derived: ft_net_vol
    df["ft_net_vol"] = df.get("ft_buy_vol", 0) - df.get("ft_sell_vol", 0)

    # Numeric coercion
    numeric_cols = [c for c in df.columns if c not in ("trading_date", "stock_code")]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    df = df.sort_values("trading_date").reset_index(drop=True)
    logger.debug(f"[OHLCV] {ticker}: {len(df)} rows ({df['trading_date'].min()} → {df['trading_date'].max()})")
    return df


# ── Foreign Flow ───────────────────────────────────────────────────────────────

def fetch_foreign_history_yuanta(
    ticker: str,
    from_date: str = DEFAULT_FROM,
    to_date: Optional[str] = None,
    client: Optional[YuantaAPIClient] = None,
) -> pd.DataFrame:
    """
    Lịch sử giao dịch + sở hữu nước ngoài từ Endpoint 11 (price_history_foreign).

    Thêm so với OHLCV endpoint:
      - BuyVal, SellVal (VND)
      - NetVol, NetVal (VND) — âm khi bán ròng
      - ForeignValRate (% GT NN / Tổng phiên)
      - ForeignOwnedRate (% sở hữu thực tế)
      - RemainRoom (CP NN có thể mua thêm)
    """
    to_date = to_date or _today()
    _client = client or YuantaAPIClient()
    ticker = ticker.upper()

    logger.debug(f"[Foreign] Fetch {ticker}: {from_date} → {to_date}")

    try:
        raw = _client.get(
            f"market_data/market_watch/price_history_foreign/{ticker}",
            params={"from_date": from_date, "to_date": to_date},
        )
    except Exception as exc:
        logger.error(f"[Foreign] {ticker}: request failed — {exc}")
        return pd.DataFrame()

    rows = _extract_response(raw)
    if not rows:
        logger.warning(f"[Foreign] {ticker}: empty response")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    existing = [c for c in FOREIGN_FIELDS_RAW if c in df.columns]
    df = df[existing].rename(columns={k: v for k, v in FOREIGN_RENAME.items() if k in existing})
    df["stock_code"] = ticker
    df = _parse_date_col(df)

    numeric_cols = [c for c in df.columns if c not in ("trading_date", "stock_code")]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    df = df.sort_values("trading_date").reset_index(drop=True)
    logger.debug(f"[Foreign] {ticker}: {len(df)} rows")
    return df


# ── Merge OHLCV + Foreign → MergedDaily ───────────────────────────────────────

def fetch_merged_history(
    ticker: str,
    from_date: str = DEFAULT_FROM,
    to_date: Optional[str] = None,
    client: Optional[YuantaAPIClient] = None,
) -> pd.DataFrame:
    """
    Gop OHLCV va Foreign endpoint thanh 1 DataFrame hoan chinh.
    Join theo trading_date (left join tu OHLCV -> Foreign).

    Luu y quan trong ve Foreign endpoint:
      - API Yuanta chi tra ve Foreign data tu khoang 2025 tro di
      - Khi from_date qua xa (VD: 2016) -> response empty
      - Giai phap: Foreign luon fetch tu (to_date - 2 nam) de dam bao co data
      - OHLCV van fetch full tu from_date goc
    """
    _client = client or YuantaAPIClient()
    today_str = _today()
    to_date = to_date or today_str

    df_ohlcv = fetch_ohlcv_history_yuanta(ticker, from_date, to_date, _client)
    if df_ohlcv.empty:
        logger.warning(f"[Merged] {ticker}: OHLCV empty, aborting merge")
        return pd.DataFrame()

    # Foreign endpoint chi co data tu ~2025 (khoang 1-1.5 nam gan nhat)
    # Neu from_date qua xa (VD: 2016) -> response empty
    # Giai phap: foreign luon fetch tu (to_date - 13 thang) de dam bao co data
    try:
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        # 13 thang de cover ca truong hop dau nam
        import calendar
        month = to_dt.month
        year  = to_dt.year - 1
        day   = min(to_dt.day, calendar.monthrange(year, month)[1])
        foreign_from = f"{year}-{month:02d}-{day:02d}"
    except (ValueError, OverflowError):
        foreign_from = from_date

    df_foreign = fetch_foreign_history_yuanta(ticker, foreign_from, to_date, _client)

    # Base columns từ OHLCV
    ohlcv_base_cols = [
        "stock_code", "trading_date", "open_price", "high", "low",
        "close", "average", "volume", "value", "per_change",
        "put_through_vol", "put_through_val",
    ]
    base_cols = [c for c in ohlcv_base_cols if c in df_ohlcv.columns]
    df = df_ohlcv[base_cols].copy()

    if not df_foreign.empty:
        foreign_merge_cols = ["trading_date"]
        # Cột foreign ưu tiên (đầy đủ hơn ft_buy/sell chỉ là vol)
        for col in ["ft_buy_vol", "ft_buy_val", "ft_sell_vol", "ft_sell_val",
                    "ft_net_vol", "ft_net_val", "ft_val_rate", "ft_owned_rate", "remain_room"]:
            if col in df_foreign.columns:
                foreign_merge_cols.append(col)
        df = df.merge(df_foreign[foreign_merge_cols], on="trading_date", how="left")
    else:
        logger.warning(f"[Merged] {ticker}: Foreign data empty, filling zeros")

    # Đảm bảo đủ cột với 0.0 cho foreign nếu thiếu
    foreign_zero_cols = [
        "ft_buy_vol", "ft_buy_val", "ft_sell_vol", "ft_sell_val",
        "ft_net_vol", "ft_net_val", "ft_val_rate", "ft_owned_rate", "remain_room",
    ]
    for col in foreign_zero_cols:
        if col not in df.columns:
            df[col] = 0.0

    # Fill NaN từ left join
    df[foreign_zero_cols] = df[foreign_zero_cols].fillna(0.0)

    df = df.sort_values("trading_date").reset_index(drop=True)
    logger.info(
        f"[Merged] {ticker}: {len(df)} days "
        f"({df['trading_date'].min()} → {df['trading_date'].max()})"
    )
    return df
