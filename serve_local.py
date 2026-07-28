#!/usr/bin/env python3
"""
serve_local.py — Minimal static file server cho Dashboard (thay serve_dashboard.py).

Muc dich: Phuc vu file tinh (HTML, JS, JSON.gz) cho dashboard.
         Khong can proxy, khong can CORS workaround phuc tap.

Cach dung:
  python serve_local.py
  -> Mo browser: http://localhost:8888

Auto-mo browser sau 1 giay (co the tat bang --no-browser).
"""
import http.server
import os
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORT = 8888
# Root la thu muc goc du an (chua ca 'dashboard/' va 'data/')
ROOT = Path(__file__).resolve().parent


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Serve files tu ROOT, tu dong giai nen .gz neu browser ho tro."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        # Cho phep browser tu giai nen .json.gz
        if self.path.endswith(".json.gz"):
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Type", "application/json")
        # CORS header de tranh loi (du dung file:// hay http://)
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def guess_type(self, path):
        # Override MIME type cho .gz -> application/json (browser tu decode)
        if str(path).endswith(".json.gz"):
            return "application/json"
        return super().guess_type(path)

    def log_message(self, format, *args):
        # Chi hien thi request quan trong (bo qua .js, .css)
        msg = format % args
        if any(x in msg for x in [".json", "index.html", "404", "500"]):
            print(f"  {msg[:100]}")


class _ReuseServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    no_browser = "--no-browser" in sys.argv

    os.chdir(ROOT)

    with _ReuseServer(("", PORT), _Handler) as httpd:
        url = f"http://localhost:{PORT}/dashboard/index.html"
        print("=" * 55)
        print("  YUANTA DASHBOARD - Local Static Server")
        print("=" * 55)
        print(f"  URL    : {url}")
        print(f"  Root   : {ROOT}")
        print(f"  Ctrl+C : Thoat server")
        print("=" * 55)

        if not no_browser:
            def _open():
                time.sleep(1.2)
                webbrowser.open(url)
                print(f"  Browser da tu dong mo: {url}")
            threading.Thread(target=_open, daemon=True).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server da dung.")


if __name__ == "__main__":
    main()
