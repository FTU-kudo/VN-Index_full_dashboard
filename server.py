"""Serve the dashboard and proxy its free Yuanta CSTC endpoint locally.

Run from the repository root:
    .\\.venv\\Scripts\\python.exe dashboard\\server.py
Then open http://127.0.0.1:8765.
"""

from __future__ import annotations

import json
import re
import argparse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests


HOST = "127.0.0.1"
PORT = 8765
YUANTA_CSTC_URL = "https://ysradarapi.yuanta.com.vn/api/v3/vietstock/financial_statement/report"
TICKER_PATTERN = re.compile(r"^[A-Z0-9]{1,10}$")
TERM_PATTERN = re.compile(r"^(Q[1-4]|Năm)$")


class DashboardHandler(SimpleHTTPRequestHandler):
    """Static dashboard host with a narrowly scoped server-side Yuanta proxy."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).resolve().parent), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - standard library hook name
        parsed = urlparse(self.path)
        if parsed.path == "/api/yuanta/cstc":
            self._proxy_cstc(parsed.query)
            return
        super().do_GET()

    def _proxy_cstc(self, query_string: str) -> None:
        query = parse_qs(query_string)
        ticker = query.get("stock_code", [""])[0].upper()
        term = query.get("term_code", ["Q2"])[0]
        year = query.get("year_period", [""])[0]

        if not TICKER_PATTERN.fullmatch(ticker) or not TERM_PATTERN.fullmatch(term) or not year.isdigit():
            self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "message": "Tham số yêu cầu không hợp lệ."})
            return

        params = {
            "lang": "vi",
            "page_index": 1,
            "page_size": 6,
            "report_term_type": 2,
            "report_type": "CSTC",
            "stock_code": ticker,
            "term_code": term,
            "unit": 1_000_000,
            "year_period": year,
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://ysradar.yuanta.com.vn/",
            "Origin": "https://ysradar.yuanta.com.vn",
        }

        try:
            response = requests.get(YUANTA_CSTC_URL, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            self._send_json(
                HTTPStatus.BAD_GATEWAY,
                {"success": False, "message": f"Không thể lấy dữ liệu từ Yuanta: {exc}"},
            )
            return

        self._send_json(HTTPStatus.OK, payload)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve the Yuanta dashboard locally.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    print(f"Dashboard: http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), DashboardHandler).serve_forever()
