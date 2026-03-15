#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import threading
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
REFRESH_SCRIPT = ROOT_DIR / "backend" / "scripts" / "refresh_backtest_data.py"
STATUS_PATH = WEB_DIR / "data" / "refresh-meta.json"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "4175"))


class RefreshManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status = self._load_status()
        self._thread = None
        self._attempted_refresh_date = None

    def _load_status(self) -> dict:
        if not STATUS_PATH.exists():
            return {}
        try:
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def needs_refresh(self) -> bool:
        status = self._load_status()
        self._status = status
        today = date.today().isoformat()
        if self._attempted_refresh_date == today:
            return False
        return not status.get("success") or status.get("refreshDate") != today

    def _run_refresh(self) -> None:
        self._attempted_refresh_date = date.today().isoformat()
        result = subprocess.run(
            [sys.executable, str(REFRESH_SCRIPT)],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        self._status = self._load_status()
        self._status["serverReturnCode"] = result.returncode
        self._status["serverStdoutTail"] = result.stdout.strip().splitlines()[-20:]
        self._status["serverStderrTail"] = result.stderr.strip().splitlines()[-20:]

    def ensure_fresh(self, force: bool = False, wait: bool = False) -> dict:
        with self._lock:
            if not force and not self.needs_refresh() and not (self._thread and self._thread.is_alive()):
                return self._status

            if self._thread and self._thread.is_alive():
                return self.status

            if wait:
                self._run_refresh()
                return self.status

            self._thread = threading.Thread(target=self._run_refresh, daemon=True)
            self._thread.start()
            return self.status

    @property
    def status(self) -> dict:
        self._status = self._load_status()
        self._status["refreshInProgress"] = bool(self._thread and self._thread.is_alive())
        return self._status


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in {"/", "/index.html"}:
            self.server.refresh_manager.ensure_fresh()

        if parsed.path == "/api/refresh-status":
            payload = self.server.refresh_manager.status
            return self._json_response(payload, status=200)

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            payload = self.server.refresh_manager.ensure_fresh(force=True)
            return self._json_response(payload, status=200)
        self.send_error(404)

    def _json_response(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # pragma: no cover - local server log helper
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


class PreviewServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.refresh_manager = RefreshManager()


def main() -> int:
    refresh_manager = RefreshManager()
    refresh_manager.ensure_fresh(wait=False)

    server = PreviewServer((HOST, PORT), PreviewHandler)
    server.refresh_manager = refresh_manager
    print(f"Backtest preview server: http://{HOST}:{PORT}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
