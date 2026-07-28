@echo off
echo ========================================================
echo YUANTA DATA ENGINE - DAILY SYNC (16:00 PM)
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/8] Dang dong bo du lieu 10 nam (OHLCV, BCTC, CSTC)...
.\.venv\Scripts\python.exe sync_1500_universe_10yr.py --limit 1600 --workers 20 --start-year 2016 --merge

echo [2/8] Dang xuat du lieu BCTC ra file data.js...
.\.venv\Scripts\python.exe dashboard/export_data.py

echo [3/8] Dang xuat du lieu CSTC ra file cstc_data.js...
.\.venv\Scripts\python.exe dashboard/export_cstc.py

echo [4/8] Dang dong bo Ho so doanh nghiep, Co cau co dong, Dinh gia (Peers)...
.\.venv\Scripts\python.exe dashboard/fetch_profile_data.py

echo [5/8] Dang dong bo Tin tuc ^& Su kien...
.\.venv\Scripts\python.exe dashboard/fetch_events_data.py

echo [6/8] Dang dong bo Tuong quan nganh (Radar Chart)...
.\.venv\Scripts\python.exe dashboard/fetch_correlate.py

echo [7/8] Cap nhat lich su gia + giao dich nuoc ngoai (Incremental - Static JSON.gz)...
.\.venv\Scripts\python.exe scripts/download_history.py --incremental

echo [8/8] Build static files cho Dashboard (khong can serve_dashboard.py)...
.\.venv\Scripts\python.exe scripts/build_static_files.py --rebuild-json

echo.
echo ========================================================
echo HOAN TAT DONG BO DU LIEU! Tab "Du lieu giao dich" da san sang.
echo ========================================================
