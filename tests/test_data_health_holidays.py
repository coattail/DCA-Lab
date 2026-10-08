"""Regressions for the false freshness failure in Refresh Market Data #154."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import data_health
import localize_scheme_b_data as scheme
import refresh_backtest_data as refresh


class HolidayFreshnessTests(unittest.TestCase):
    def check_both_validators(self, series_id, latest, today, expected_ok, allowance):
        rows = [(latest, 4600)]
        if expected_ok:
            data_health.validate_source_rows(rows, series_id, today)
        else:
            with self.assertRaises(ValueError):
                data_health.validate_source_rows(rows, series_id, today)
        check = refresh.assess_series_health(
            series_id, {"exists": True, "rows": 1, "end": latest}, today
        )
        self.assertEqual(check["ok"], expected_ok)
        self.assertEqual(check["holidayAllowanceDays"], allowance)
        self.assertEqual(check["stalenessDays"], (today - date.fromisoformat(latest)).days)
        return check

    def test_national_day_run_154_accepts_both_hs300_series(self):
        for series_id in ("hs300_price", "hs300_total_return"):
            with self.subTest(series_id=series_id):
                check = self.check_both_validators(series_id, "2026-09-30", date(2026, 10, 8), True, 5)
                self.assertEqual(check["stalenessDays"], 8)
                self.assertEqual(check["baseMaxStalenessDays"], 7)
                self.assertEqual(check["maxStalenessDays"], 12)

    def test_allowance_expires_after_trading_resumes(self):
        for series_id in ("hs300_price", "hs300_total_return"):
            self.check_both_validators(series_id, "2026-09-30", date(2026, 10, 12), True, 5)
            self.check_both_validators(series_id, "2026-09-30", date(2026, 10, 13), False, 5)
            self.check_both_validators(series_id, "2026-09-21", date(2026, 10, 8), False, 6)

    def test_spring_festival_closures_exclude_weekends(self):
        for series_id in ("hs300_price", "hs300_total_return"):
            self.check_both_validators(series_id, "2026-02-13", date(2026, 2, 24), True, 6)

    def test_only_elapsed_closures_after_observation_extend_limit(self):
        self.check_both_validators("hs300_price", "2026-09-30", date(2026, 10, 2), True, 2)
        self.check_both_validators("hs300_price", "2026-10-08", date(2026, 10, 16), False, 0)
        # Oct 10 is a civil make-up workday but a stock-exchange weekend.
        self.check_both_validators("hs300_price", "2026-10-09", date(2026, 10, 12), True, 0)

    def test_other_markets_and_unknown_years_keep_existing_limits(self):
        for series_id in ("sp500_price", "nasdaq100_total_return", "nikkei225_price"):
            self.check_both_validators(series_id, "2026-09-30", date(2026, 10, 8), False, 0)
        self.check_both_validators("usdcny", "2026-09-30", date(2026, 10, 11), False, 0)
        self.check_both_validators("hs300_price", "2027-09-30", date(2027, 10, 8), False, 0)

    def test_official_price_backup_is_accepted_during_national_day(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(scheme, "DATA_DIR", Path(directory)), patch.object(
            scheme, "date", wraps=date
        ) as scheme_date, patch.object(data_health, "date", wraps=date) as health_date, patch.object(
            scheme, "fetch_eastmoney_index", side_effect=ConnectionError("reset")
        ), patch.object(scheme, "fetch_csindex_total_return", return_value=[("2026-09-30", 4600)]), contextlib.redirect_stderr(io.StringIO()):
            scheme_date.today.return_value = health_date.today.return_value = date(2026, 10, 8)
            rows, source = scheme.fetch_hs300_price()
        self.assertEqual(rows[-1][0], "2026-09-30")
        self.assertIn("CSI official", source)

    def test_entire_refresh_accepts_holiday_cache_and_reports_allowance(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            files = {}
            for series_id in refresh.SERIES_FILES:
                latest = "2026-09-30" if series_id.startswith("hs300_") else "2026-10-07"
                files[series_id] = directory / f"{series_id}.csv"
                files[series_id].write_text(f"Date,Close\n{latest},4600\n")
            status = directory / "refresh-meta.json"
            summary = directory / "summary.md"
            responses = [
                (subprocess.CompletedProcess([], 0, "", ""), {}),
                (subprocess.CompletedProcess([], 0, "", ""), {}),
                (subprocess.CompletedProcess([], 0, "", ""), {"cachedSeries": ["hs300_price"]}),
            ]
            with patch.object(refresh, "SERIES_FILES", files), patch.object(refresh, "STATUS_PATH", status), patch.object(
                refresh, "datetime", wraps=datetime
            ) as clock, patch.object(refresh, "run_refresh_command", side_effect=responses) as command, patch.dict(
                refresh.os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}
            ), contextlib.redirect_stdout(io.StringIO()):
                clock.now.return_value = datetime(2026, 10, 8, 2, 48, tzinfo=timezone.utc)
                self.assertEqual(refresh.main(), 0)
            self.assertEqual(command.call_count, 3)
            payload = json.loads(status.read_text())
            self.assertTrue(payload["success"])
            task = payload["tasks"][-1]
            self.assertTrue(task["usedCachedOutputs"])
            self.assertFalse(task["refreshSucceeded"])
            self.assertEqual(task["attemptCount"], 1)
            self.assertIn("| hs300_price | 2026-09-30 | 8 | 12 | 5 | fresh |", summary.read_text())


if __name__ == "__main__":
    unittest.main()
