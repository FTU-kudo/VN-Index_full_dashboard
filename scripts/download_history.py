#!/usr/bin/env python3
"""
scripts/download_history.py — Download toàn bộ lịch sử giá và giao dịch nước ngoài.

Sử dụng:
  # Full download tất cả ~1,600 mã từ 2016 (lần đầu, chạy 1 lần duy nhất)
  python scripts/download_history.py

  # Chỉ cập nhật incremental (chạy hàng ngày sau 16:00)
  python scripts/download_history.py --incremental

  # Test với 1 hoặc vài mã
  python scripts/download_history.py --tickers ACB,VCB,HPG

  # Re-download toàn bộ từ đầu (dùng khi thay đổi schema)
  python scripts/download_history.py --force

  # Chỉ lấy mã trên sàn HOSE
  python scripts/download_history.py --exchange HSX

  # Giới hạn số lượng mã (test)
  python scripts/download_history.py --limit 10

Ước tính thời gian:
  Full download 1,600 mã:
    - 2 API requests/mã × 0.3s/request = ~16 phút (sequential)
    - Mỗi request trả về toàn bộ ~2,500 records trong 1 lần call
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
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
logger = logging.getLogger("DownloadHistory")


def main():
    parser = argparse.ArgumentParser(
        description="Download lịch sử OHLCV + Foreign Flow cho tất cả cổ phiếu VN.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Danh sách mã cách nhau bởi dấu phẩy, VD: ACB,VCB,HPG (mặc định: tất cả)",
    )
    parser.add_argument(
        "--from-date",
        default="2016-01-01",
        help="Ngày bắt đầu lịch sử (mặc định: 2016-01-01)",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Chỉ download từ ngày cuối cùng đã cache (bỏ qua mã đã up-to-date hôm nay)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download toàn bộ, bỏ qua cache hiện có",
    )
    parser.add_argument(
        "--exchange",
        default=None,
        choices=["HSX", "HNX", "UPCOM"],
        help="Chỉ download mã thuộc sàn (HSX | HNX | UPCOM)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số mã tải (dùng để test)",
    )
    args = parser.parse_args()

    from pipelines.history import run_history_pipeline
    from src.data.market_data import fetch_all_tickers, fetch_tickers_by_exchange

    # Resolve ticker list
    if args.tickers:
        ticker_list = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        logger.info(f"Mode: Specific tickers -> {ticker_list}")
    elif args.exchange:
        logger.info(f"Mode: Exchange filter -> {args.exchange}")
        from src.data.market_data import fetch_tickers_by_exchange
        df_ex = fetch_tickers_by_exchange(args.exchange)
        if df_ex.empty or "StockCode" not in df_ex.columns:
            logger.error(f"Khong lay duoc danh sach ma tu san {args.exchange}")
            sys.exit(1)
        ticker_list = df_ex["StockCode"].astype(str).unique().tolist()
        ticker_list = [t for t in ticker_list if len(t) == 3]
        logger.info(f"  -> {len(ticker_list)} ma tren {args.exchange}")
    else:
        logger.info("Mode: Full universe (tat ca ma tren 3 san)")
        ticker_list = fetch_all_tickers()
        logger.info(f"  -> {len(ticker_list)} ma")

    if args.limit:
        ticker_list = ticker_list[: args.limit]
        logger.info(f"  Limit test: {args.limit} ma dau tien")

    if not ticker_list:
        logger.error("Danh sach ma rong. Thoat.")
        sys.exit(1)

    # Uoc tinh
    if not args.incremental:
        from_year = int(args.from_date[:4])
        years = 2026 - from_year + 1
        est_days = years * 250
        est_min = len(ticker_list) * 2 * 0.3 / 60
        logger.info(
            f"Uoc tinh: {est_days:,} ngay/ma x {len(ticker_list)} ma = "
            f"{est_days * len(ticker_list) / 1e6:.1f}M records"
        )
        logger.info(f"Thoi gian uoc tinh: ~{est_min:.0f} phut (2 API call/ma x 0.3s/call)")

    print("=" * 60)
    print(f"  YUANTA HISTORY DOWNLOAD PIPELINE")
    print(f"  Tickers : {len(ticker_list)}")
    print(f"  From    : {args.from_date}")
    print(f"  Force   : {args.force}")
    print(f"  Mode    : {'Incremental' if args.incremental else 'Full/Force' if args.force else 'Full with skip up-to-date'}")
    print("=" * 60)

    start = time.time()
    run_history_pipeline(
        stock_codes=ticker_list,
        from_date=args.from_date,
        force=args.force,
    )
    elapsed = time.time() - start

    print("=" * 60)
    print(f"  HOAN THANH trong {elapsed:.1f}s ({elapsed/60:.1f} phut)")
    print("=" * 60)


if __name__ == "__main__":
    main()
