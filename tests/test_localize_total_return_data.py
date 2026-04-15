import importlib.util
import pathlib
import subprocess
import unittest
from datetime import date
from unittest import mock

import requests


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "scripts" / "localize_total_return_data.py"
SPEC = importlib.util.spec_from_file_location("localize_total_return_data", MODULE_PATH)
localize_total_return_data = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(localize_total_return_data)


class LocalizeTotalReturnDataTests(unittest.TestCase):
    def test_merge_close_rows_preserves_history_and_overwrites_overlap(self) -> None:
        existing_rows = [
            ("1988-01-04", 256.01998901),
            ("2026-03-28", 14000.0),
            ("2026-03-30", 14147.30957031),
        ]
        fresh_rows = [
            ("2026-03-30", 14150.0),
            ("2026-03-31", 14220.0),
            ("2026-04-01", 14310.0),
        ]

        merged = localize_total_return_data.merge_close_rows(existing_rows, fresh_rows)

        self.assertEqual(
            merged,
            [
                ("1988-01-04", 256.01998901),
                ("2026-03-28", 14000.0),
                ("2026-03-30", 14150.0),
                ("2026-03-31", 14220.0),
                ("2026-04-01", 14310.0),
            ],
        )

    def test_resolve_refresh_start_rewinds_from_last_known_date(self) -> None:
        existing_rows = [
            ("1988-01-04", 256.01998901),
            ("2026-03-28", 14000.0),
            ("2026-03-30", 14147.30957031),
        ]

        refresh_start = localize_total_return_data.resolve_refresh_start(
            existing_rows,
            minimum_date=date(1988, 1, 4),
        )

        self.assertEqual(refresh_start, date(2025, 12, 30))

    def test_fetch_json_with_retry_retries_transient_request_failures(self) -> None:
        send_request = mock.Mock(
            side_effect=[
                requests.ConnectionError("upstream reset"),
                {"ok": True},
            ]
        )

        payload = localize_total_return_data.fetch_json_with_retry(send_request, attempts=3)

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(send_request.call_count, 2)

    def test_fetch_json_with_retry_retries_subprocess_failures(self) -> None:
        send_request = mock.Mock(
            side_effect=[
                subprocess.CalledProcessError(56, ["curl"]),
                {"ok": True},
            ]
        )

        payload = localize_total_return_data.fetch_json_with_retry(send_request, attempts=3)

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(send_request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
