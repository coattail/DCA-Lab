import contextlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend' / 'scripts'))
import data_health
import localize_scheme_b_data as scheme
import refresh_backtest_data as refresh


class SourceFailoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = pathlib.Path(self.temp.name)
        self.enterContext(patch.object(scheme, 'DATA_DIR', self.directory))
        self.enterContext(patch.object(scheme, 'date')).today.return_value = date(2026, 9, 9)
        self.enterContext(patch.object(data_health, 'date', wraps=date)).today.return_value = date(2026, 9, 9)
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))
        for name in ('usdcny', 'usdjpy', 'hs300'):
            (self.directory / f'{name}.csv').write_text('Date,Close\n1981-01-02,2\n2026-08-28,7\n')

    def test_hs300_disconnect_uses_official_price_index_preserving_history(self):
        with patch.object(scheme, 'fetch_eastmoney_index', side_effect=ConnectionError('reset')), patch.object(
            scheme, 'fetch_csindex_total_return', return_value=[('2026-09-08', 4600)]
        ) as official:
            rows, source = scheme.fetch_hs300_price()
        official.assert_called_once_with('000300', '2005-01-04', '2026-09-09')
        self.assertEqual(rows[0], ('1981-01-02', 2))
        self.assertEqual(rows[-1], ('2026-09-08', 4600))
        self.assertIn('000300', source)

    def test_hs300_empty_stale_and_invalid_200_responses_try_backup(self):
        for primary in ([], [('2026-08-28', 4500)], [('2026-09-08', float('nan'))]):
            with self.subTest(primary=primary), patch.object(scheme, 'fetch_eastmoney_index', return_value=primary), patch.object(
                scheme, 'fetch_csindex_total_return', return_value=[('2026-09-08', 4600)]
            ) as backup:
                rows, _ = scheme.fetch_hs300_price()
                self.assertEqual(rows[-1][0], '2026-09-08')
                backup.assert_called_once()

    def test_hs300_both_sources_fail_uses_cache_and_reports_it(self):
        with patch.object(scheme, 'fetch_eastmoney_index', side_effect=RuntimeError('down')), patch.object(
            scheme, 'fetch_csindex_total_return', side_effect=RuntimeError('down')
        ):
            rows, cached = scheme.fetch_with_cache_fallback('HS300', self.directory / 'hs300.csv', lambda: scheme.fetch_hs300_price()[0])
        self.assertTrue(cached)
        self.assertEqual(rows[-1][0], '2026-08-28')

    def test_stale_fred_200_triggers_ecb_without_rewriting_history(self):
        # Same response age as run #131: Aug 28 -> Sep 8 = 11 days.
        with patch.object(scheme, 'fetch_fred_series', return_value=[('2026-08-28', 6.7)]), patch.object(
            scheme, 'fetch_ecb_usd_cross_rates', return_value=(
                [('2026-08-28', 99), ('2026-09-08', 6.8)],
                [('2026-08-28', 999), ('2026-09-08', 150)],
            )
        ) as backup:
            cny, jpy, source, cached = scheme.fetch_fx_history()
        backup.assert_called_once()
        self.assertFalse(cached)
        self.assertIn('ECB', source)
        self.assertEqual(cny, [('1981-01-02', 2), ('2026-08-28', 6.7), ('2026-09-08', 6.8)])
        self.assertEqual(jpy[-1], ('2026-09-08', 150))

    def test_fresh_fred_does_not_call_ecb(self):
        with patch.object(scheme, 'fetch_fred_series', return_value=[('2026-09-04', 6.7)]), patch.object(
            scheme, 'fetch_ecb_usd_cross_rates'
        ) as backup:
            cny, _, source, cached = scheme.fetch_fx_history()
        backup.assert_not_called()
        self.assertFalse(cached)
        self.assertIn('FRED', source)
        self.assertEqual(cny[0][0], '1981-01-02')

    def test_one_fred_pair_failure_retains_other_fresh_pair(self):
        with patch.object(scheme, 'fetch_fred_series', side_effect=[[('2026-09-08', 6.7)], RuntimeError('down')]), patch.object(
            scheme, 'fetch_ecb_usd_cross_rates', return_value=([('2026-09-08', 9)], [('2026-09-08', 150)])
        ):
            cny, jpy, _, cached = scheme.fetch_fx_history()
        self.assertFalse(cached)
        self.assertEqual(cny[-1], ('2026-09-08', 6.7))
        self.assertEqual(jpy[-1], ('2026-09-08', 150))

    def test_stale_backup_is_not_reported_as_live_success(self):
        with patch.object(scheme, 'fetch_fred_series', return_value=[]), patch.object(
            scheme, 'fetch_ecb_usd_cross_rates', return_value=([('2026-08-28', 8)], [('2026-08-28', 150)])
        ):
            cny, _, _, cached = scheme.fetch_fx_history()
        self.assertTrue(cached)
        self.assertEqual(cny[-1], ('2026-08-28', 7))

    def test_all_sources_unavailable_without_cache_fails(self):
        for target in self.directory.glob('*.csv'):
            target.unlink()
        with patch.object(scheme, 'fetch_fred_series', return_value=[]), patch.object(
            scheme, 'fetch_ecb_usd_cross_rates', side_effect=RuntimeError('down')
        ), self.assertRaises(RuntimeError):
            scheme.fetch_fx_history()


class RefreshHealthTests(unittest.TestCase):
    def test_limits_are_shared_and_boundary_is_inclusive(self):
        rows = [('2026-08-28', 6.7)]
        data_health.validate_source_rows(rows, 'usdcny', date(2026, 9, 7))
        with self.assertRaisesRegex(ValueError, 'age=11'):
            data_health.validate_source_rows(rows, 'usdcny', date(2026, 9, 8))
        self.assertIs(refresh.SERIES_MAX_STALENESS_DAYS, data_health.SERIES_MAX_STALENESS_DAYS)

    def test_invalid_and_future_observations_rejected(self):
        for rows in ([], [('2026-09-10', 7)], [('bad-date', 7)], [('2026-09-08', 0)], [('2026-09-08', float('inf'))]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                data_health.validate_source_rows(rows, 'usdcny', date(2026, 9, 9))

    def run_refresh(self, end, report):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'usdcny.csv'
            target.write_text(f'Date,Close\n{end},6.7\n')
            status = pathlib.Path(directory) / 'refresh-meta.json'
            summary = pathlib.Path(directory) / 'summary.md'
            with patch.object(refresh, 'SERIES_FILES', {'usdcny': target}), patch.object(refresh, 'STATUS_PATH', status), patch.object(
                refresh, 'TASKS', [{'id': 'fx', 'label': 'FX', 'command': ['test'], 'series_ids': ['usdcny']}]
            ), patch.object(refresh, 'MAX_TASK_ATTEMPTS', 1), patch.object(
                refresh, 'run_refresh_command', return_value=(subprocess.CompletedProcess(['test'], 0, '', ''), report)
            ), patch.dict(refresh.os.environ, {'GITHUB_STEP_SUMMARY': str(summary)}), contextlib.redirect_stdout(io.StringIO()) as output:
                code = refresh.main()
            return code, json.loads(status.read_text()), summary.read_text(), output.getvalue()

    def test_stale_successful_command_blocks_publication_with_diagnostics(self):
        code, status, summary, output = self.run_refresh('2000-01-01', {})
        self.assertNotEqual(code, 0)
        self.assertFalse(status['success'])
        self.assertIn('usdcny: stale', output)
        self.assertIn('latest=2000-01-01', output)
        self.assertIn('2000-01-01', summary)

    def test_cached_outputs_are_not_labelled_successfully_refreshed(self):
        code, status, _, output = self.run_refresh(date.today().isoformat(), {'cachedSeries': ['usdcny']})
        self.assertEqual(code, 0)
        self.assertTrue(status['success'])
        self.assertFalse(status['tasks'][0]['refreshSucceeded'])
        self.assertTrue(status['tasks'][0]['usedCachedOutputs'])
        self.assertIn('::warning::', output)

    def test_fresh_outputs_are_reported_successfully_refreshed(self):
        code, status, _, _ = self.run_refresh(date.today().isoformat(), {})
        self.assertEqual(code, 0)
        self.assertTrue(status['tasks'][0]['refreshSucceeded'])
        self.assertFalse(status['tasks'][0]['usedCachedOutputs'])

    def test_bad_coverage_date_is_reported_instead_of_crashing(self):
        for end in ('bad-date', '2099-01-01'):
            check = refresh.assess_series_health('usdcny', {'exists': True, 'rows': 1, 'end': end}, date(2026, 9, 9))
            self.assertEqual(check['reason'], 'invalid-date')
            self.assertFalse(check['ok'])


if __name__ == '__main__':
    unittest.main()
