import http.server
import os
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORT = 8080
ROOT = Path(__file__).resolve().parent

class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/dashboard/index.html')
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        if self.path.endswith(".json.gz"):
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def guess_type(self, path):
        if str(path).endswith(".json.gz"):
            return "application/json"
        return super().guess_type(path)

    def log_message(self, format, *args):
        msg = format % args
        if any(x in msg for x in [".json", "index.html", "404", "500"]):
            print(f"  {msg[:100]}")

class _ReuseServer(socketserver.TCPServer):
    allow_reuse_address = True

def main():
    no_browser = "--no-browser" in sys.argv
    os.chdir(ROOT)

    with _ReuseServer(("", PORT), _Handler) as httpd:
        url = f"http://localhost:{PORT}/"
        print("=" * 55)
        print("  YUANTA DASHBOARD - Static Server (Port 8080)")
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
