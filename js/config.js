// dashboard/js/config.js
// ════════════════════════════════════════════════════════════════
// CẤU HÌNH DEPLOYMENT — Chỉnh sửa file này khi deploy
// ════════════════════════════════════════════════════════════════

const APP_CONFIG = {
  // GitHub Pages URL
  STATIC_BASE_URL: "https://FTU-kudo.github.io/VN-Index_full_dashboard/data",

  // Fallback cho local development (chạy serve_dashboard.py hoặc live-server)
  LOCAL_BASE_URL: "http://localhost:8080/data/static",

  // Tự động detect môi trường
  get BASE_URL() {
    if (window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1") {
      return this.LOCAL_BASE_URL;
    }
    return this.STATIC_BASE_URL;
  },

  // Cache control
  UNIVERSE_CACHE_TTL_MS:      3600 * 1000,    // 1 giờ
  MARKET_SUMMARY_CACHE_TTL_MS: 300 * 1000,   // 5 phút
};
