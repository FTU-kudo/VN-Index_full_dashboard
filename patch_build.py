import sys
from pathlib import Path

file_path = Path('scripts/build_static_files.py')
content = file_path.read_text(encoding='utf-8')

new_funcs = '''
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
'''

content = content.replace('def main():', new_funcs + '\n\ndef main():')
call_str = '    build_manifest_json(static_dir, history_dir)\n\n    logger.info("Building financials JSON...")\n    build_financial_json()\n'
content = content.replace('    build_manifest_json(static_dir, history_dir)', call_str)

file_path.write_text(content, encoding='utf-8')
