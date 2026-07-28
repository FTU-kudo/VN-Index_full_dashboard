# Hướng dẫn Deploy lên GitHub

## Bước 1: Tạo repo và push code

```bash
# Trong thư mục VN-Index_full_dashboard/
git init
git add .
git commit -m "feat: initial VN-Index_full_dashboard platform"

# Tạo repo trên GitHub (github.com/new), rồi:
git remote add origin https://github.com/FTU-kudo/VN-Index_full_dashboard.git
git branch -M main
git push -u origin main
```

## Bước 2: Cấu hình GitHub Actions permissions

1. Vào **Settings** → **Actions** → **General**
2. Mục "Workflow permissions" → chọn **"Read and write permissions"**
3. Tick ✅ **"Allow GitHub Actions to create and approve pull requests"**
4. Lưu

## Bước 3: Thêm Secrets

1. Vào **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Thêm:
   - Name: `GOOGLE_API_KEY` | Value: `your_key_here`

## Bước 4: Kích hoạt GitHub Pages

1. Vào **Settings** → **Pages**
2. Source: **"Deploy from a branch"**
3. Branch: **`gh-pages`** | Folder: **`/ (root)`**
4. Save

> `gh-pages` branch sẽ được tạo tự động lần đầu tiên khi workflow chạy.

## Bước 5: Chạy bootstrap workflow lần đầu

1. Vào **Actions** → **"Build Historical Data & Static Files"**
2. Click **"Run workflow"** → tick **"Full rebuild từ 2016"** → Run
3. Chờ ~15 phút (1,600 mã × 2 API calls)
4. Sau khi xong, truy cập: `https://FTU-kudo.github.io/VN-Index_full_dashboard/`

## Bước 6: Verify dashboard

Kiểm tra các URL sau hoạt động:
- `https://FTU-kudo.github.io/VN-Index_full_dashboard/` → Dashboard loads
- `https://FTU-kudo.github.io/VN-Index_full_dashboard/data/universe.json` → JSON array
- `https://FTU-kudo.github.io/VN-Index_full_dashboard/data/history/ACB.json.gz` → Downloadable

## Lịch chạy tự động (sau khi setup)

| Thời gian (ICT) | Ngày | Workflow | Tác vụ |
|-----------------|------|----------|--------|
| 16:10 | T2–T6 | daily_update | Giá EOD + Ratings |
| 16:30 | T2–T6 | daily_ai_technical | AI Kỹ thuật |
| 16:45 | T2–T6 | build_history | History data + Deploy |
| 08:00 | Thứ 7 | weekly_financials | BCTC 8 quý |
| 09:00 | Thứ 7 | weekly_ai_analysis | AI Cơ bản |
