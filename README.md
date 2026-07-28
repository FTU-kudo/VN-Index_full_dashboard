# 🦅 Yuanta VN Data — Vietnam Equity Research Platform

> Production-grade data pipeline + AI analysis + interactive dashboard
> cho ~1,600 cổ phiếu Việt Nam trên cả 3 sàn HOSE · HNX · UPCOM.

[![Daily Update](https://github.com/FTU-kudo/VN-Index_full_dashboard/actions/workflows/daily_update.yml/badge.svg)](https://github.com/FTU-kudo/VN-Index_full_dashboard/actions/workflows/daily_update.yml)
[![Weekly Financials](https://github.com/FTU-kudo/VN-Index_full_dashboard/actions/workflows/weekly_financials.yml/badge.svg)](https://github.com/FTU-kudo/VN-Index_full_dashboard/actions/workflows/weekly_financials.yml)
[![AI Analysis](https://github.com/FTU-kudo/VN-Index_full_dashboard/actions/workflows/weekly_ai_analysis.yml/badge.svg)](https://github.com/FTU-kudo/VN-Index_full_dashboard/actions/workflows/weekly_ai_analysis.yml)

**🌐 Live Dashboard:** [https://FTU-kudo.github.io/VN-Index_full_dashboard/](https://FTU-kudo.github.io/VN-Index_full_dashboard/)

---

## ✨ Tính năng

| Module | Mô tả | Tần suất |
|--------|--------|----------|
| **Real-time Prices** | Bid/ask 3 bậc, nước ngoài, ATO/ATC cho 1,600 mã | Hàng ngày |
| **Financial Statements** | IS + BS + CF + Pre-computed Ratios (8 quý) | Hàng tuần |
| **AI Fundamental Analysis** | Phân tích cơ bản bằng Gemini 2.0 Flash | Hàng tuần |
| **AI Technical Analysis** | OHLCV + Foreign Flow → Gemini interpretation | Hàng ngày |
| **Historical Data** | 10 năm OHLCV + giao dịch nước ngoài (2016–nay) | Hàng ngày |
| **Interactive Dashboard** | Stock lookup, charts, peer comparison | Static, GitHub Pages |

---

## 🚀 Cài đặt nhanh

```bash
git clone https://github.com/FTU-kudo/VN-Index_full_dashboard.git
cd VN-Index_full_dashboard
pip install -r requirements.txt
cp .env.example .env
# Điền GOOGLE_API_KEY vào .env

# Lần đầu: Bootstrap toàn bộ database (~11 phút)
python scripts/bootstrap.py
python scripts/download_history.py
python scripts/build_static_files.py

# Hàng ngày:
python scripts/daily_update.py
python scripts/run_ai_analysis.py --type technical
```

## 📊 Sử dụng Python API

```python
from yuanta import YuantaClient
from yuanta.api import MarketAPI, FinancialAPI, HistoryAPI, UniverseAPI

with YuantaClient() as client:
    market = MarketAPI(client)
    hist   = HistoryAPI(client)

    # Giá real-time + rating cho nhiều mã (batch)
    df_prices  = market.get_prices(["ACB", "VNM", "HPG", "MWG"])
    df_ratings = market.get_ratings(["ACB", "VNM", "HPG", "MWG"])
    df_board   = market.get_all_ratings_leaderboard(exchange="HSX")

    # Lịch sử 10 năm OHLCV + foreign flow (1 request)
    df_hist = hist.get_merged("ACB", from_date="2016-01-01")

    # Phân tích cơ bản AI
    from pipelines.ai_analysis import run_ai_analysis
    df_analysis = run_ai_analysis(["ACB", "VNM"], model="gemini-2.0-flash")
```

## 🗂️ Cấu trúc dự án

```
VN-Index_full_dashboard/
├── yuanta/              # Core Python package
│   ├── api/             # 11 API endpoints đã xác nhận
│   ├── models/          # Pydantic v2 schemas
│   └── utils/           # Cache, rate limiter
├── pipelines/           # Batch data pipelines
├── analysis/            # AI analysis (Gemini integration)
├── scripts/             # CLI entry points
├── dashboard/           # Static web dashboard
│   ├── index.html
│   └── js/
│       ├── config.js    # URL configuration
│       └── app.js       # Main app logic
├── .github/workflows/   # 5 GitHub Actions workflows
│   ├── daily_update.yml         # 16:10 ICT T2-T6
│   ├── daily_ai_technical.yml   # 16:30 ICT T2-T6
│   ├── build_history.yml        # 16:45 ICT T2-T6
│   ├── weekly_financials.yml    # Thứ Bảy 08:00 ICT
│   └── weekly_ai_analysis.yml   # Thứ Bảy 09:00 ICT
├── data/
│   └── summary/         # ✅ Committed: small CSV snapshots
└── API_CATALOG.md       # 11 Yuanta API endpoints đã xác nhận
```

## 🔑 Yuanta API Endpoints (11 confirmed)

| # | Endpoint | Mô tả |
|---|----------|--------|
| 1 | `list_stock_info?exchange=HSX` | Universe theo sàn |
| 2 | `list_stock_by_sector` | Mapping ngành ICB |
| 3 | `list_stock_info?stock_list=...` | Giá real-time (batch) |
| 4 | `list_stock_rating_info?stock_list=...` | Rating board (batch) |
| 5 | `stock_rating/info/{code}` | Company profile |
| 6 | `financial_statement/report?...` | IS + BS + Ratios |
| 7 | `stock_rating/event?from=...` | Corporate events |
| 8 | `stock_rating/list_stock_rating` (POST) | Leaderboard |
| 9 | `stock_rating/correlate` (POST) | Peer benchmarking |
| 10 | `price_history/{code}?from_date=...` | OHLCV history |
| 11 | `price_history_foreign/{code}?from_date=...` | Foreign flow history |

## ⚙️ GitHub Secrets cần thiết

| Secret | Mô tả |
|--------|--------|
| `GOOGLE_API_KEY` | Google AI Studio API key (Gemini) |
| `GITHUB_TOKEN` | Tự động có — không cần tạo |

## 📋 Disclaimer

> Dữ liệu từ Yuanta Securities Vietnam (YSVN). Phân tích AI chỉ mang tính tham khảo,
> không phải khuyến nghị đầu tư chính thức. Người dùng tự chịu trách nhiệm với quyết định đầu tư.
