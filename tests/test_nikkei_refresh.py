import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
import data_health
import localize_scheme_b_data as scheme


class NikkeiRefreshTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.directory = pathlib.Path(directory)
        self.enterContext(patch.object(scheme, "DATA_DIR", self.directory))
        self.enterContext(patch.object(scheme, "date", wraps=date)).today.return_value = date(2026, 11, 3)
        self.enterContext(patch.object(data_health, "date", wraps=date)).today.return_value = date(2026, 11, 3)
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))
        self.target = self.directory / "nikkei225.csv"
        self.target.write_text("Date,Close\n1979-12-28,6569.47\n2026-07-01,50000\n2026-10-19,60000\n")
        self.fresh = [("2026-11-02", 63081.86)]

    def test_official_daily_csv_preserves_old_history_and_skips_html(self):
        with patch.object(scheme, "fetch_nikkei_price_daily_history", return_value=self.fresh), patch.object(
            scheme, "fetch_nikkei_price_history"
        ) as historical, patch.object(scheme, "fetch_nikkei_yahoo_price_history") as yahoo:
            rows, source = scheme.fetch_nikkei_price()
        self.assertEqual(rows[0], ("1979-12-28", 6569.47))
        self.assertEqual(rows[-1], self.fresh[0])
        self.assertIn("official daily", source)
        historical.assert_not_called()
        yahoo.assert_not_called()

    def test_unhealthy_csv_tries_historical_source_before_yahoo(self):
        for primary in ([], [("2026-10-19", 60000)], [("2026-11-02", float("nan"))], [("2026-11-04", 1)]):
            with self.subTest(primary=primary), patch.object(
                scheme, "fetch_nikkei_price_daily_history", return_value=primary
            ), patch.object(scheme, "fetch_nikkei_price_history", return_value=self.fresh) as historical, patch.object(
                scheme, "fetch_nikkei_yahoo_price_history"
            ) as yahoo:
                rows, source = scheme.fetch_nikkei_price()
                self.assertEqual(rows[-1], self.fresh[0])
                self.assertIn("historical", source)
                historical.assert_called_once()
                yahoo.assert_not_called()

    def test_official_sources_blocked_use_yahoo_price_and_preserve_history(self):
        with patch.object(scheme, "fetch_nikkei_price_daily_history", side_effect=RuntimeError("403")), patch.object(
            scheme, "fetch_nikkei_price_history", side_effect=RuntimeError("challenge")
        ), patch.object(scheme, "fetch_nikkei_yahoo_price_history", return_value=self.fresh):
            rows, source = scheme.fetch_nikkei_price()
        self.assertEqual(rows[0], ("1979-12-28", 6569.47))
        self.assertEqual(rows[-1], self.fresh[0])
        self.assertIn("^N225", source)

    def test_all_unhealthy_sources_use_cache_and_remain_stale(self):
        with patch.object(scheme, "fetch_nikkei_price_daily_history", return_value=[]), patch.object(
            scheme, "fetch_nikkei_price_history", side_effect=RuntimeError("down")
        ), patch.object(scheme, "fetch_nikkei_yahoo_price_history", return_value=[("2026-10-19", 60000)]):
            rows, cached = scheme.fetch_with_cache_fallback("Nikkei price", self.target, lambda: scheme.fetch_nikkei_price()[0])
            self.assertTrue(cached)
            with self.assertRaisesRegex(ValueError, "age=15"):
                data_health.validate_source_rows(rows, "nikkei225_price")
            self.target.unlink()
            with self.assertRaises(RuntimeError):
                scheme.fetch_with_cache_fallback("Nikkei price", self.target, lambda: scheme.fetch_nikkei_price()[0])

    def test_csv_uses_close_column_and_ignores_footer(self):
        scraper = Mock()
        scraper.get.return_value.text = ('\ufeffDate of Data,Close,Open,High,Low\n'
                                        '"2026/11/02","63081.86","62972.02","63615.32","62712.91"\n'
                                        '"Copyright footer"\n')
        with patch.object(scheme, "make_nikkei_scraper", return_value=scraper):
            self.assertEqual(scheme.fetch_nikkei_price_daily_history(), self.fresh)
            scraper.get.return_value.text = "<html>Just a moment...</html>"
            with self.assertRaisesRegex(ValueError, "header"):
                scheme.fetch_nikkei_price_daily_history()

    def test_yahoo_requests_price_symbol_and_close_column(self):
        # ^N225 is the price index; its Close is distinct from Adjusted Close.
        with patch.object(scheme, "fetch_yahoo_payload", return_value={}) as fetch, patch.object(
            scheme, "build_yahoo_price_rows", return_value=[("2026-11-02", "1", "2", "3", "63081.86", "4")]
        ):
            self.assertEqual(scheme.fetch_nikkei_yahoo_price_history(), self.fresh)
        fetch.assert_called_once_with("^N225")

    def test_failed_cached_month_does_not_discard_successful_recent_months(self):
        def fetch_month(task):
            if task == (2026, 7):
                raise RuntimeError("403 challenge")
            return [(f"{task[0]}-{task[1]:02d}-02", 63081.86)]

        with patch.object(scheme, "fetch_nikkei_month_history", side_effect=fetch_month):
            rows = scheme.fetch_nikkei_price_history()
        self.assertIn(("2026-07-01", 50000), rows)
        self.assertIn(("2026-10-19", 60000), rows)
        self.assertEqual(rows[-1], self.fresh[0])
        self.assertEqual(len(rows), len(dict(rows)))

    def test_uncovered_month_failure_is_not_silently_accepted(self):
        def fetch_month(task):
            if task == (2026, 8):
                raise RuntimeError("down")
            return [(f"{task[0]}-{task[1]:02d}-02", 63081.86)]

        with patch.object(scheme, "fetch_nikkei_month_history", side_effect=fetch_month):
            with self.assertRaisesRegex(RuntimeError, "uncovered months: 2026-08"):
                scheme.fetch_nikkei_price_history()

    def test_empty_month_response_retries_and_keeps_cause(self):
        scraper = Mock()
        scraper.get.return_value.text = "<html>Just a moment...</html>"
        with patch.object(scheme, "get_thread_nikkei_scraper", return_value=scraper):
            with self.assertRaisesRegex(RuntimeError, "2026-07: Empty Nikkei historical table"):
                scheme.fetch_nikkei_month_history((2026, 7))
        self.assertEqual(scraper.get.call_count, 3)


if __name__ == "__main__":
    unittest.main()
