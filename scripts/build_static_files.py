#!/usr/bin/env python3
"""
scripts/build_static_files.py — Tạo tất cả static files cho dashboard.

Chạy sau download_history.py để generate:
  1. data/static/history/{TICKER}.json.gz — per-ticker history (từ parquet đã có)
  2. data/static/universe.json            — danh sách tất cả mã + metadata
  3. data/static/manifest.json            — danh sách mã đã có JSON.gz + thời gian cập nhật

Files này được serve trực tiếp bởi dashboard (file:// hoặc GitHub Pages).
KHÔNG cần serve_dashboard.py sau khi có các static files này.

Hướng dẫn sử dụng:
  # Rebuild JSON.gz từ tất cả parquet đã có (không download lại từ API)
  python scripts/build_static_files.py --rebuild-json

  # Chỉ tạo universe.json và manifest.json
  python scripts/build_static_files.py --meta-only

  # Rebuild JSON.gz cho một số mã cụ thể
  python scripts/build_static_files.py --tickers ACB,VCB
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path

# Root path setup
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Fix Windows CP1252 terminal encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("BuildStaticFiles")


def build_universe_json(static_dir: Path) -> None:
    """
    Tạo universe.json — danh sách mã + metadata cho search/filter trong dashboard.
    ~1,600 entries, mỗi entry nhỏ gọn dạng dict.
    """
    from config.settings import RAW_DIR
    from src.data.storage import load_from_parquet

    univ_path = RAW_DIR / "universe" / "vietnam_1500_universe.parquet"
    if not univ_path.exists():
        logger.warning(f"Universe parquet không tìm thấy: {univ_path}")
        logger.warning("Bỏ qua build universe.json")
        return

    df = load_from_parquet(univ_path)
    if df.empty:
        logger.warning("Universe parquet rỗng, bỏ qua.")
        return

    records = []
    for _, row in df.iterrows():
        records.append({
            "c": str(row.get("symbol", row.get("StockCode", ""))),
            "n": str(row.get("CompanyNameVi", row.get("company_name", ""))),
            "e": str(row.get("Exchange", row.get("exchange", ""))),
            "s": str(row.get("SectorName", row.get("sector_name", ""))),
        })

    # Lọc bỏ entry rỗng
    records = [r for r in records if r["c"]]

    out = {
        "updated_at": date.today().isoformat(),
        "count": len(records),
        "tickers": records,
    }

    out_path = static_dir / "universe.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info(f"universe.json: {len(records)} tickers -> {out_path.stat().st_size / 1024:.0f} KB")


def build_manifest_json(static_dir: Path, history_dir: Path) -> None:
    """
    Tạo manifest.json — danh sách các mã đã có JSON.gz và kích thước file.
    Dashboard dùng file này để biết mã nào đã có dữ liệu offline.
    """
    entries = []
    for gz_path in sorted(history_dir.glob("*.json.gz")):
        entries.append({
            "c": gz_path.stem,           # stock_code
            "kb": round(gz_path.stat().st_size / 1024, 1),
        })

    manifest = {
        "updated_at": date.today().isoformat(),
        "count": len(entries),
        "files": entries,
    }

    out_path = static_dir / "manifest.json"
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info(f"manifest.json: {len(entries)} tickers co JSON.gz -> {out_path.stat().st_size / 1024:.1f} KB")


def rebuild_json_gz(stock_codes: list | None = None) -> None:
    """
    Re-generate JSON.gz từ parquet đã có trên máy.
    Không download lại từ API, chỉ đọc parquet và viết lại JSON.gz.
    """
    from pipelines.history import HISTORY_RAW, rebuild_all_json_gz
    rebuild_all_json_gz(stock_codes)



def build_financial_json(
    stock_codes: list[str] | None = None,
    n_periods:   int = 8,
) -> None:
    """
    Export per-ticker financial data thành JSON nhỏ cho dashboard.
    Thay thế hoàn toàn cstc_data.js (59MB) bằng 1,600 files ~15KB mỗi file.

    Output: data/static/financials/{TICKER}.json
    """
    import json
    import pandas as pd
    from datetime import date
    from pathlib import Path
    from config.settings import DATA_DIR
    from src.data.storage import load_from_parquet

    FINANCIALS_DIR = DATA_DIR / "static" / "financials"
    FINANCIALS_DIR.mkdir(parents=True, exist_ok=True)
    AI_DIR = DATA_DIR / "raw" / "ai_analysis"

    proc_dir = DATA_DIR / "processed"
    
    try:
        master = load_from_parquet(proc_dir / "financial_master.parquet")
    except Exception:
        master = None
        
    try:
        ratings = load_from_parquet(proc_dir / "latest_ratings.parquet")
    except Exception:
        logger.error("latest_ratings not found — run daily_update.py first")
        return

    if ratings.empty:
        logger.error("latest_ratings empty")
        return

    if stock_codes is None:
        stock_codes = ratings["stock_code"].dropna().unique().tolist()

    n_ok = n_err = 0

    for code in stock_codes:
        try:
            payload = _build_financial_payload(
                code, master, ratings, AI_DIR, n_periods
            )
            out_path = FINANCIALS_DIR / f"{code}.json"
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",",":")),
                encoding="utf-8"
            )
            n_ok += 1
        except Exception as exc:
            logger.warning(f"Financial JSON [{code}]: {exc}")
            n_err += 1

    total_mb = sum(p.stat().st_size for p in FINANCIALS_DIR.glob("*.json")) / 1e6
    logger.info(
        f"Financial JSONs: {n_ok} OK / {n_err} errors "
        f"-> {FINANCIALS_DIR} ({total_mb:.1f} MB total)"
    )


def _build_financial_payload(
    stock_code: str,
    master: "pd.DataFrame | None",
    ratings: "pd.DataFrame",
    ai_dir:  "Path",
    n_periods: int,
) -> dict:
    import json
    from datetime import date
    import pandas as pd

    today = date.today().isoformat()

    rat_row = ratings[ratings["stock_code"] == stock_code]
    rat = rat_row.iloc[0].to_dict() if not rat_row.empty else {}

    periods, is_items, bs_items, ratio_items = [], [], [], []

    if master is not None and not master.empty:
        fs = master[master["stock_code"] == stock_code]

        if not fs.empty:
            all_periods = sorted(fs["period"].unique(), reverse=True)
            periods = all_periods[:n_periods]

            def extract_items(section_filter, n_total: int):
                subset = fs[
                    fs["section"].str.contains(section_filter, case=False, na=False) &
                    fs["norm_id"].notna()
                ]
                items_out = []
                for norm_id, group in subset.groupby("norm_id"):
                    period_map = dict(zip(group["period"], group["value"]))
                    values = [
                        _safe_float(period_map.get(p))
                        for p in periods
                    ]
                    if all(v is None for v in values):
                        continue

                    row_sample = group.iloc[0]
                    items_out.append({
                        "norm_id":  int(norm_id),
                        "name_en":  str(row_sample.get("field_name_en", "") or ""),
                        "is_total": bool(row_sample.get("is_total", False)),
                        "unit":     str(row_sample.get("unit", "") or ""),
                        "values":   values,
                    })
                return items_out

            is_items    = extract_items("Income",  n_periods)
            bs_items    = extract_items("Balance", n_periods)
            ratio_items = extract_items("RATIO",   n_periods)

    ai_content = {}
    ai_path = ai_dir / f"{stock_code}_fundamental.json"
    if ai_path.exists():
        try:
            ai_raw = json.loads(ai_path.read_text(encoding="utf-8"))
            if ai_raw.get("success") and ai_raw.get("content"):
                ai_content = ai_raw["content"]
                ai_content["generated_at"] = ai_raw.get("generated_at", "")
                ai_content["model"]        = ai_raw.get("model", "")
        except Exception:
            pass

    quick_ratios = {
        "pe":  [_safe_float(rat.get("pe"))],
        "pb":  [_safe_float(rat.get("pb"))],
        "roe": [_safe_float(rat.get("roe"))],
        "roa": [_safe_float(rat.get("roa"))],
        "eps": [_safe_float(rat.get("eps_trailing"))],
    }

    return {
        "stock_code":    stock_code,
        "updated_at":    today,
        "latest_period": periods[0] if periods else "N/A",
        "periods":       periods,
        "quick_ratios":  quick_ratios,
        "ratios_ts":     {item["name_en"]: item["values"]
                          for item in ratio_items},
        "income_statement": {
            "items": [i for i in is_items if i["is_total"]]
        },
        "balance_sheet": {
            "items": [i for i in bs_items if i["is_total"]]
        },
        "ai_fundamental": ai_content if ai_content else None,
    }

def _safe_float(v) -> float | None:
    try:
        f = float(v)
        return None if (f != f) else round(f, 4)
    except (TypeError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Build static files cho Yuanta Dashboard (khong can serve_dashboard.py).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--rebuild-json",
        action="store_true",
        help="Rebuild tat ca JSON.gz tu parquet da co (khong download API)",
    )
    parser.add_argument(
        "--meta-only",
        action="store_true",
        help="Chi tao universe.json va manifest.json",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Rebuild JSON.gz cho cac ma cu the (VD: ACB,VCB)",
    )
    args = parser.parse_args()

    from config.settings import RAW_DIR

    static_dir   = RAW_DIR.parent / "static"
    history_dir  = static_dir / "history"
    static_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  BUILD STATIC FILES — Yuanta Dashboard")
    print("=" * 60)

    start = time.time()

    if args.rebuild_json and not args.meta_only:
        ticker_list = None
        if args.tickers:
            ticker_list = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        logger.info(f"Rebuilding JSON.gz {'(all)' if not ticker_list else str(ticker_list)}...")
        rebuild_json_gz(ticker_list)

    # Luôn tạo meta files (universe + manifest)
    logger.info("Building universe.json...")
    build_universe_json(static_dir)

    logger.info("Building manifest.json...")
    build_manifest_json(static_dir, history_dir)

    logger.info("Building financials JSON...")
    build_financial_json()


    elapsed = time.time() - start
    n_gz = sum(1 for _ in history_dir.glob("*.json.gz"))
    total_mb = sum(p.stat().st_size for p in history_dir.glob("*.json.gz")) / (1024 * 1024)

    print("=" * 60)
    print(f"  HOAN THANH trong {elapsed:.1f}s")
    print(f"  JSON.gz files: {n_gz} ma ({total_mb:.1f} MB)")
    print(f"  Static dir: {static_dir}")
    print("=" * 60)
    print()
    print("  Tiep theo:")
    print("  -> Mo dashboard/index.html (KHONG can serve_dashboard.py!)")
    print("  -> Hoac push data/static/ len GitHub Pages de deploy")


if __name__ == "__main__":
    main()
