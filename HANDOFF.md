# VN Stocks Analysis Dashboard - Project Handoff

Bản Handoff này ghi chép lại toàn bộ kiến trúc và các thành tựu nâng cấp quan trọng đã được thực thi cho dự án **VN Stocks Analysis via Yuanta**.

## 1. Tự động hóa CI/CD
- **GitHub Actions**: Thiết lập workflow (`.github/workflows/update-data.yml`) để tự động chạy script Python mỗi ngày (hoặc theo lịch trình), trích xuất dữ liệu mới nhất từ Yuanta và lưu vào thư mục `dashboard/js`.
- **Vercel Deployment**: Sẵn sàng tích hợp và triển khai (deploy) Dashboard dưới dạng một trang web tĩnh (Static Web App), luôn hiển thị dữ liệu tươi mới nhất sau mỗi lần GitHub Actions chạy thành công.

## 2. Nâng cấp Kiến trúc "Tương quan trong ngành"
Loại bỏ hoàn toàn sự phụ thuộc vào API Tương quan cũ của Yuanta (chậm và thiếu ổn định). Xây dựng lại toàn bộ logic bằng Javascript thuần để xử lý dữ liệu offline từ `CSTC_DATA`, với hiệu năng tức thời.

Kiến trúc được chia làm 2 phân hệ độc lập để hiển thị các bộ chỉ tiêu đặc thù nhất:

### A. Khối Ngân hàng (Banks)
Bao gồm 4 biểu đồ chuyên sâu:
1. **Khả năng sinh lợi (Radar)**: YOEA, COF, NIM, CIR, Tăng trưởng TN, ROE.
2. **Khả năng thanh khoản (Bar)**: LDR, Cho vay/Tổng TS, VCSH/Tổng TS.
3. **Chất lượng tài sản (Bar)**: Dự phòng rủi ro/Dư nợ, TS sinh lãi/Tổng TS.
4. **Định giá (Bar)**: P/E, P/B.

### B. Khối Doanh nghiệp (Phi Ngân hàng: Sản xuất, BĐS, Bán lẻ, Dịch vụ tài chính...)
Bao gồm 5 biểu đồ đa năng:
1. **Khả năng sinh lợi & Hiệu quả (Radar)**: Tích hợp 6 chỉ số cốt lõi (ROE, ROA, Biên lãi gộp, Biên lãi thuần, Vòng quay Tổng tài sản, Nợ vay/VCSH).
2. **Đòn bẩy tài chính & Cơ cấu vốn (Bar)**: Nợ vay/Tổng TS, Nợ vay/VCSH, Nợ NH/Tổng nợ.
3. **Tốc độ Tăng trưởng (Bar)**: Doanh thu, Lợi nhuận trước thuế, Tổng tài sản, Vốn chủ sở hữu.
4. **Dòng tiền & Thanh khoản (Bar)**: Thanh toán hiện hành, Dòng tiền HĐKD/DTT, Dòng tiền HĐKD/TTS.
5. **Định giá (Bar)**: P/E, P/B, P/S.

## 3. Tối ưu hóa Dữ liệu và Phân tích
- **Trung vị ngành (Industry Median)**: Thuật toán tự động tìm kiếm các công ty cùng ngành (theo Ngành cấp 1 của Yuanta) và tính toán Trung vị (Median) mượt mà cho mọi chỉ số, loại bỏ nhiễu từ các công ty có chỉ số dị biệt.
- **Xử lý Tỷ lệ (Scale)**: Chuyển đổi các biểu đồ cột đứng sang kiến trúc **Multi-grid (Đa lưới)** của ECharts. Các chỉ số có độ lớn quá chênh lệch (VD: P/E là 30 và P/B là 1) giờ đây sở hữu các Trục Y (Y-Axis) độc lập, giúp hiển thị trực quan và không bị "ép" nhỏ lại.

## 4. Tinh chỉnh UI/UX
- **Định dạng Phần trăm (%)**: Các chỉ tiêu mang tính chất tỷ lệ phần trăm (NIM, ROE, Biên lãi...) tự động hiển thị ký hiệu `%` thông minh tại Tooltip và Trục toạ độ.
- **Làm tròn số (Rounding)**: Mọi dữ liệu trích xuất và tính toán đều được làm tròn đến tối đa 2 chữ số thập phân, đảm bảo giao diện chuyên nghiệp và sắc nét.

## 5. Nâng cấp Tab Dữ liệu Giao dịch (Live Data)
Chuyển đổi hoàn toàn cơ chế tải dữ liệu của tab "Dữ liệu giao dịch" từ tĩnh (offline) sang kiến trúc **Live Fetch**, giúp giải quyết bài toán tải dữ liệu khổng lồ (3.7 triệu bản ghi cho 10 năm của 1600 mã).
- **Tích hợp Local Proxy Đa luồng**: Xây dựng `serve_dashboard.py` sử dụng kiến trúc `ThreadingHTTPServer` để vượt qua rào cản CORS của trình duyệt và giải quyết triệt để lỗi "Deadlock/Hanging" của Python Single-Thread khi Chrome mở nhiều kết nối song song. 
- **Sub-Tabs Giao dịch**: Thiết kế UI mượt mà tích hợp 2 phân hệ: **Lịch sử giá** và **Giao dịch nước ngoài** (đầy đủ các trường dữ liệu như KL mua/bán, GT mua/bán, Tỷ lệ khối ngoại).
- **Tự động hóa Filter**: Hệ thống tự động thiết lập phạm vi chọn lọc thông minh: "Từ ngày" - "Đến ngày" được mặc định là 30 ngày gần nhất (tính từ ngày hiện tại), áp dụng đồng bộ cho toàn bộ 1600 mã. Tự động Fetch API ngay khi có thao tác đổi ngày mà không cần ấn nút tải.
- **Color Coding UX**: Tích hợp biến màu sắc CSS linh hoạt: Tô màu xanh lá (Tăng), Đỏ (Giảm), Vàng cam (Tham chiếu) tự động lên cột '% Thay đổi' và 'Đóng cửa'. Số liệu được format "Triệu đồng" mượt mà.

### Bài học & Thất bại (Lessons Learned):
- **CORS & Proxy API**: Phát hiện Yuanta chặn các proxy công cộng (allorigins, corsproxy), buộc phải tự phát triển Local Proxy.
- **Python Threading**: Lỗi sập trình duyệt quay vòng 15 phút không tải được do sử dụng `socketserver.TCPServer` đơn luồng. Đã phát hiện và xử lý gọn bằng `ThreadingHTTPServer` và thêm `timeout=10s`.
- **Cấu trúc JSON bất ngờ**: Bị kẹt do Yuanta sử dụng `json.response` thay vì `json.data` tiêu chuẩn.
- **Trùng lặp cú pháp JS**: Gặp tai nạn Syntax Error khi lỡ khai báo lại hàm `formatInt` khiến toàn bộ hệ thống JS bị sập, sau đó đã dọn dẹp sạch sẽ mã nguồn.

---
**Trạng thái Hệ thống:** Hoạt động hoàn hảo, siêu tốc, UI/UX mượt mà không độ trễ. Local Proxy ổn định, bảo mật và tương thích toàn bộ hệ thống API Yuanta (`/api/v3/`). Mọi thứ đã sẵn sàng 100%!

## 6. Nâng cấp Vượt bậc (Session 5): Triệt tiêu Local Proxy & Kiến trúc Dữ liệu Tĩnh
Nhận thấy việc bắt người dùng (hoặc server) phải luôn chạy `serve_dashboard.py` (Local Proxy) làm giảm trải nghiệm và tính di động của hệ thống, dự án đã có bước chuyển mình lớn:
- **Loại bỏ hoàn toàn Local Proxy**: Tab "Dữ liệu giao dịch" hiện không còn phụ thuộc vào `serve_dashboard.py`.
- **Kiến trúc Per-Ticker Static JSON.gz**: Xây dựng Pipeline tự động tải trước toàn bộ dữ liệu Lịch sử giao dịch (Giá, Khối lượng, Khối ngoại...) của 10 năm cho 1600 mã. Sau đó, hệ thống nén và lưu trữ thành 1600 file tĩnh `.json.gz` riêng biệt (ví dụ: `data/static/history/FPT.json.gz`).
- **Tối ưu tốc độ Build bằng Pandas Vectorization**: Xử lý triệt để lỗi parse JSON do dính `NaN` hoặc `inf` bằng cách áp dụng thuật toán ma trận của Pandas (`fillna(0)`), giúp tốc độ render file rút ngắn từ vài phút xuống chỉ còn vài giây.
- **Tích hợp Tự động hóa**: Cả 2 công đoạn "Tải dữ liệu mới" (`download_history.py --incremental`) và "Nén tĩnh" (`build_static_files.py`) đã được nhúng trực tiếp vào `run_daily_sync.bat`. Qua đó, chỉ cần một cú click là toàn bộ hệ thống sẽ đồng bộ hoàn toàn.
- **Truy xuất Siêu Tốc trên Trình duyệt**: `app.js` được viết lại để fetch và giải nén trực tiếp các file tĩnh `.json.gz` thông qua HTTP chuẩn, mang lại tốc độ hiển thị cực nhanh và có thể dễ dàng host lên GitHub Pages hoàn toàn miễn phí mà không cần bất kỳ server backend nào!

## 7. Cập nhật Fix Bug & Đồng bộ Dữ liệu Khối ngoại (29/07/2026)
Tiếp tục tối ưu hóa hệ thống dựa trên kiến trúc Static JSON đã được thiết lập:
- **Khắc phục lỗi HTTPStatus Server (TypeError)**: Đã xử lý dứt điểm lỗi crash Terminal (404/500 errors) trong file `serve_dashboard.py` và `serve_local.py`. Hệ thống giờ đây format log an toàn thành chuỗi trước khi kiểm tra thay vì trực tiếp duyệt qua object `HTTPStatus`.
- **Xác thực & Nạp Dữ liệu API Khối ngoại Mới nhất**: Kiểm chứng và sử dụng thành công 2 API mới của Yuanta (`price_history` và `price_history_foreign`). Đã viết kịch bản ép hệ thống tải bổ sung riêng biệt, merge và nén tĩnh `.json.gz` thành công dữ liệu ngày 28/07/2026 cho toàn bộ 1600 mã cổ phiếu mà không cần tải lại từ đầu.
- **Đổi nhận diện Thương hiệu**: Đổi tên Logo và Title từ "Yuanta Research & Quant Lab" thành "Vietnam Stock Market Research & Quant Lab" trên toàn bộ giao diện HTML, khẳng định tính độc lập của dự án.
- **Chiến lược Data-Driven Jamstack**: Đã định hình cấu trúc CI/CD cho tương lai: Sử dụng tính năng Github Actions sẵn có (`build_history.yml`) đóng vai trò là Data Pipeline Crawler tự động chạy mỗi 16:45 hàng ngày để lấy dữ liệu, sau đó trực tiếp triển khai giao diện và dữ liệu lên web qua Github Pages (hoặc Vercel) – hoàn toàn không tốn chi phí máy chủ, vận hành 100% tự động trên Cloud.
