import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "scripts" / "localize_scheme_b_data.py"
SPEC = importlib.util.spec_from_file_location("localize_scheme_b_data", MODULE_PATH)
localize_scheme_b_data = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(localize_scheme_b_data)


class LocalizeSchemeBDataTests(unittest.TestCase):
    def test_parse_ecb_cross_rates_builds_usd_pairs(self) -> None:
        csv_text = """KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE
EXR.D.CNY.EUR.SP00.A,D,CNY,EUR,SP00,A,2026-03-31,7.9341
EXR.D.JPY.EUR.SP00.A,D,JPY,EUR,SP00,A,2026-03-31,183.39
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-03-31,1.1498
EXR.D.CNY.EUR.SP00.A,D,CNY,EUR,SP00,A,2026-04-01,7.9771
EXR.D.JPY.EUR.SP00.A,D,JPY,EUR,SP00,A,2026-04-01,183.73
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-04-01,1.1605
"""

        usdcny, usdjpy = localize_scheme_b_data.parse_ecb_usd_cross_rates(csv_text)

        self.assertEqual(
            usdcny,
            [
                ("2026-03-31", round(7.9341 / 1.1498, 8)),
                ("2026-04-01", round(7.9771 / 1.1605, 8)),
            ],
        )
        self.assertEqual(
            usdjpy,
            [
                ("2026-03-31", round(183.39 / 1.1498, 8)),
                ("2026-04-01", round(183.73 / 1.1605, 8)),
            ],
        )

    def test_merge_close_rows_preserves_history_and_overwrites_overlap(self) -> None:
        existing_rows = [
            ("1981-01-02", 1.5),
            ("1998-12-31", 8.3),
            ("2026-03-20", 6.88),
        ]
        fresh_rows = [
            ("2026-03-20", 6.90),
            ("2026-03-31", 6.91),
            ("2026-04-01", 6.87),
        ]

        merged = localize_scheme_b_data.merge_close_rows(existing_rows, fresh_rows)

        self.assertEqual(
            merged,
            [
                ("1981-01-02", 1.5),
                ("1998-12-31", 8.3),
                ("2026-03-20", 6.9),
                ("2026-03-31", 6.91),
                ("2026-04-01", 6.87),
            ],
        )


if __name__ == "__main__":
    unittest.main()
