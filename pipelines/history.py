"""
pipelines/history.py — Historical Data Pipeline: Download, store, serve.

Chiến lược lưu trữ:
  1. Per-ticker parquet: data/raw/history/{TICKER}.parquet  (incremental, snappy)
  2. Per-ticker JSON:    data/static/history/{TICKER}.json.gz  (cho static dashboard)
  3. Master parquet:     data/processed/price_history.parquet  (tùy chọn, merge tất cả)

Ước tính dung lượng:
  - 1,600 tickers × 2,500 ngày × 22 cột × snappy ≈ 300-600 MB parquet
  - 1,600 tickers × 2,500 ngày × JSON (gzip lv6) ≈ 100-130 MB
  - Cache TTL: 1 ngày (update sau mỗi phiên giao dịch)
"""
from __future__ import annotations

import gzip
import json
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

# Đảm bảo root project nằm trong sys.path khi chạy trực tiếp
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import RAW_DIR, PROCESSED_DIR
from src.data.yuanta_client import YuantaAPIClient
from src.data.history_api import fetch_merged_history
from src.data.storage import save_to_parquet, load_from_parquet
from src.data.market_data import fetch_all_tickers

logger = logging.getLogger(__name__)

# ── Storage paths ──────────────────────────────────────────────────────────────

HISTORY_RAW    = RAW_DIR / "history"           # per-ticker .parquet
HISTORY_STATIC = RAW_DIR.parent / "static" / "history"  # per-ticker .json.gz

for _d in (HISTORY_RAW, HISTORY_STATIC):
    _d.mkdir(parents=True, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ticker_parquet(stock_code: str) -> Path:
    return HISTORY_RAW / f"{stock_code.upper()}.parquet"


def _ticker_json_gz(stock_code: str) -> Path:
    return HISTORY_STATIC / f"{stock_code.upper()}.json.gz"


def _last_cached_date(stock_code: str) -> Optional[str]:
    """Trả về ngày cuối cùng có trong cache (YYYY-MM-DD), None nếu chưa có."""
    p = _ticker_parquet(stock_code)
    if not p.exists():
        return None
    try:
        df = pd.read_parquet(p, columns=["trading_date"])
        if df.empty:
            return None
        last = df["trading_date"].max()
        return str(last)
    except Exception as exc:
        logger.warning(f"[{stock_code}] Cannot read cached date: {exc}")
        return None


# ── JSON.gz writer ─────────────────────────────────────────────────────────────

def write_json_gz(stock_code: str, df: pd.DataFrame) -> None:
    """
    Export DataFrame → gzip JSON cho static dashboard.

    Format tối ưu (array-of-arrays thay vì array-of-objects → giảm ~60% size):
    {
      "stock_code": "ACB",
      "updated_at": "2026-07-28",
      "fields_ohlcv":    ["date","open","high","low","close","volume","value_m","pct_change"],
      "fields_foreign":  ["date","ft_buy_vol","ft_sell_vol","ft_net_vol",
                          "ft_net_val_ty","ft_val_rate","ft_owned_rate"],
      "ohlcv":   [[...], ...],
      "foreign": [[...], ...]
    }

    Đơn vị trong JSON:
      - value      → triệu VND (chia 1e6)
      - ft_net_val → tỷ VND   (chia 1e9)
    """
    ohlcv_cols   = ["trading_date", "open_price", "high", "low", "close",
                    "average", "volume", "value", "per_change",
                    "ft_buy_vol", "ft_sell_vol", "put_through_vol", "put_through_val"]
    foreign_cols = ["trading_date", "remain_room", "ft_buy_vol", "ft_buy_val",
                    "ft_sell_vol", "ft_sell_val", "ft_net_vol", "ft_net_val",
                    "ft_val_rate", "ft_owned_rate"]

    def to_arrays(df_: pd.DataFrame, cols: list) -> list:
        available = [c for c in cols if c in df_.columns]
        if not available:
            return []
        
        temp_df = df_[available].copy()
        
        for c in available:
            if c == "trading_date":
                temp_df[c] = temp_df[c].astype(str)
            elif c in ["ft_net_val", "ft_buy_val", "ft_sell_val"]:
                temp_df[c] = (temp_df[c].astype(float) / 1e9).round(3)
            elif c in ["value", "put_through_val"]:
                temp_df[c] = (temp_df[c].astype(float) / 1e6).round(0)
            elif temp_df[c].dtype == float:
                temp_df[c] = temp_df[c].round(2)
            else:
                temp_df[c] = pd.to_numeric(temp_df[c], errors='coerce').fillna(0).astype(int)
                
        # Fill NaN -> 0
        temp_df = temp_df.fillna(0)
        # Chuyển null string thành ""
        temp_df = temp_df.replace({pd.NA: "", "nan": ""})
        
        # Convert to native Python types (int/float) to avoid json serialization issues
        # and tolist() returns standard python list of lists
        return temp_df.values.tolist()

    payload = {
        "stock_code":     stock_code.upper(),
        "updated_at":     date.today().isoformat(),
        "fields_ohlcv":   ["date", "open", "high", "low", "close",
                           "average", "volume", "value_m", "pct_change",
                           "ft_buy_vol", "ft_sell_vol", "pt_vol", "pt_val_m"],
        "fields_foreign": ["date", "remain_room", "ft_buy_vol", "ft_buy_val_ty",
                           "ft_sell_vol", "ft_sell_val_ty", "ft_net_vol",
                           "ft_net_val_ty", "ft_val_rate", "ft_owned_rate"],
        "ohlcv":          to_arrays(df, ohlcv_cols),
        "foreign":        to_arrays(df, foreign_cols),
    }

    out_path = _ticker_json_gz(stock_code)
    with gzip.open(out_path, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    logger.debug(f"[{stock_code}] JSON.gz: {size_kb:.1f} KB → {out_path.name}")


# ── Per-ticker download ────────────────────────────────────────────────────────

def download_ticker(
    stock_code: str,
    from_date: str = "2016-01-01",
    force: bool = False,
    client: Optional[YuantaAPIClient] = None,
) -> pd.DataFrame:
    """
    Download history cho 1 ticker với incremental update.

    Strategy:
      1. Check last cached date
      2. If cached và không force → chỉ fetch từ (last_date + 1) đến hôm nay
      3. If not cached hoặc force → fetch full từ from_date
      4. Append vào parquet hiện có (dedup by trading_date)
      5. Save parquet + JSON.gz

    Returns DataFrame hoàn chỉnh (bao gồm cả data cũ đã cache).
    """
    today_str = date.today().isoformat()
    last_dt   = _last_cached_date(stock_code) if not force else None

    # Đã up-to-date, không cần fetch
    if last_dt and last_dt >= today_str:
        logger.debug(f"[{stock_code}] Already up-to-date ({last_dt})")
        existing = _ticker_parquet(stock_code)
        return pd.read_parquet(existing) if existing.exists() else pd.DataFrame()

    # Tính fetch range
    if last_dt and not force:
        try:
            fetch_from = (datetime.strptime(last_dt, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        except ValueError:
            fetch_from = from_date
        if fetch_from > today_str:
            existing = _ticker_parquet(stock_code)
            return pd.read_parquet(existing) if existing.exists() else pd.DataFrame()
    else:
        fetch_from = from_date

    logger.info(f"[{stock_code}] Fetching {fetch_from} → {today_str}")
    _client = client or YuantaAPIClient()
    df_new = fetch_merged_history(stock_code, from_date=fetch_from, to_date=today_str, client=_client)

    if df_new.empty:
        logger.warning(f"[{stock_code}] No new data fetched")
        existing = _ticker_parquet(stock_code)
        return pd.read_parquet(existing) if existing.exists() else pd.DataFrame()

    # Load existing và merge
    p = _ticker_parquet(stock_code)
    if p.exists() and not force:
        df_old = load_from_parquet(p)
        if not df_old.empty:
            df_all = (
                pd.concat([df_old, df_new], ignore_index=True)
                .drop_duplicates(subset=["trading_date"])
                .sort_values("trading_date")
                .reset_index(drop=True)
            )
        else:
            df_all = df_new.sort_values("trading_date").reset_index(drop=True)
    else:
        df_all = df_new.sort_values("trading_date").reset_index(drop=True)

    # Save parquet
    save_to_parquet(df_all, p)

    # Generate JSON.gz
    write_json_gz(stock_code, df_all)

    logger.info(f"[{stock_code}] ✓ Saved {len(df_all)} days → {p.name}")
    return df_all


# ── Batch download pipeline ────────────────────────────────────────────────────

def run_history_pipeline(
    stock_codes: Optional[list] = None,
    from_date: str = "2016-01-01",
    force: bool = False,
) -> None:
    """
    Download history cho toàn bộ universe (incremental theo mặc định).

    Parameters
    ----------
    stock_codes : None = tất cả từ API (fetch_all_tickers)
    from_date   : Ngày bắt đầu lịch sử (default 2016-01-01)
    force       : Re-download toàn bộ ngay cả khi đã có cache
    """
    today = date.today().isoformat()

    if stock_codes is None:
        logger.info("Fetching live universe from Yuanta API...")
        stock_codes = fetch_all_tickers()
        logger.info(f"Universe: {len(stock_codes)} symbols")

    # Bỏ qua mã đã có data hôm nay
    to_download = [c for c in stock_codes if force or (_last_cached_date(c) or "") < today]
    n_skip = len(stock_codes) - len(to_download)

    logger.info(
        f"History pipeline: {len(to_download)}/{len(stock_codes)} cần download "
        f"(đã skip {n_skip} mã up-to-date)"
    )

    n_ok = n_err = 0
    # Dùng 1 client session cho toàn bộ batch
    client = YuantaAPIClient()

    for i, code in enumerate(to_download, 1):
        try:
            download_ticker(code, from_date=from_date, force=force, client=client)
            n_ok += 1
        except Exception as exc:
            logger.error(f"[{i}/{len(to_download)}] {code}: {exc}")
            n_err += 1

        if i % 100 == 0:
            logger.info(f"Progress: {i}/{len(to_download)} — OK:{n_ok} ERR:{n_err}")

    # Tổng kết
    n_json = sum(1 for _ in HISTORY_STATIC.glob("*.json.gz"))
    logger.info(
        f"History pipeline done: {n_ok} OK / {n_err} errors "
        f"→ {HISTORY_STATIC.name}/ ({n_json} JSON.gz files)"
    )


# ── Load helpers ───────────────────────────────────────────────────────────────

def load_ticker_history(stock_code: str) -> pd.DataFrame:
    """Load full history cho 1 mã từ parquet cache cục bộ."""
    p = _ticker_parquet(stock_code)
    if not p.exists():
        raise FileNotFoundError(
            f"No history cache for {stock_code}. "
            f"Run: python scripts/download_history.py --tickers {stock_code}"
        )
    return load_from_parquet(p)


def load_history_panel(
    stock_codes: Optional[list] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load long-format panel cho nhiều mã từ per-ticker parquets.
    Hiệu quả hơn đọc 1 file lớn: chỉ đọc mã cần thiết.
    """
    codes = stock_codes or [p.stem for p in HISTORY_RAW.glob("*.parquet")]
    frames = []
    for code in codes:
        try:
            df = load_ticker_history(code)
            if from_date:
                df = df[df["trading_date"].astype(str) >= from_date]
            if to_date:
                df = df[df["trading_date"].astype(str) <= to_date]
            if not df.empty:
                frames.append(df)
        except FileNotFoundError:
            pass

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def rebuild_all_json_gz(stock_codes: Optional[list] = None) -> None:
    """
    Re-generate tất cả per-ticker JSON.gz từ parquet đã có trên máy.
    Hữu ích khi thay đổi format JSON mà không cần re-download từ API.
    """
    codes = stock_codes or [p.stem for p in HISTORY_RAW.glob("*.parquet")]
    logger.info(f"Rebuilding JSON.gz for {len(codes)} tickers...")

    n_ok = n_err = 0
    for code in codes:
        try:
            df = load_ticker_history(code)
            write_json_gz(code, df)
            n_ok += 1
        except Exception as exc:
            logger.warning(f"[{code}]: {exc}")
            n_err += 1

    logger.info(f"Rebuild done: {n_ok} OK / {n_err} errors")
