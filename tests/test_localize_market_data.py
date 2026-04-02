import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "backend" / "scripts" / "localize_market_data.py"
SPEC = importlib.util.spec_from_file_location("localize_market_data", MODULE_PATH)
localize_market_data = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(localize_market_data)


class LocalizeMarketDataTests(unittest.TestCase):
    def test_load_market_rows_falls_back_to_yahoo_when_stooq_payload_is_invalid(self) -> None:
        existing_rows = [
            ("1790-01-01", "1", "1", "1", "1", "100"),
            ("2026-03-27", "6453.89", "6453.89", "6356.08", "6368.85", "1954498355"),
        ]
        timestamps = [1774915200 + 86400 * offset for offset in range(101)]
        yahoo_payload = {
            "chart": {
                "result": [
                    {
                        "timestamp": timestamps,
                        "indicators": {
                            "quote": [
                                {
                                    "open": [6400.0 + offset for offset in range(101)],
                                    "high": [6420.0 + offset for offset in range(101)],
                                    "low": [6390.0 + offset for offset in range(101)],
                                    "close": [6415.0 + offset for offset in range(101)],
                                    "volume": [123 + offset for offset in range(101)],
                                }
                            ]
                        },
                    }
                ]
            }
        }

        rows, source = localize_market_data.load_market_rows(
            existing_rows=existing_rows,
            stooq_fetcher=lambda: "",
            yahoo_fetcher=lambda: yahoo_payload,
        )

        self.assertEqual(source, "yahoo")
        self.assertEqual(rows[0], existing_rows[0])
        self.assertEqual(rows[1], existing_rows[1])
        self.assertEqual(
            rows[2:4],
            [
                ("2026-03-31", "6400.00", "6420.00", "6390.00", "6415.00", "123"),
                ("2026-04-01", "6401.00", "6421.00", "6391.00", "6416.00", "124"),
            ],
        )

    def test_parse_stooq_csv_rejects_empty_payload(self) -> None:
        with self.assertRaises(ValueError):
            localize_market_data.parse_stooq_csv("")


if __name__ == "__main__":
    unittest.main()
