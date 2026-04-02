#!/usr/bin/env python3

import csv
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "web" / "data"
USER_AGENT = "Mozilla/5.0"
YAHOO_CHART_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

SERIES = [
    {
        "label": "S&P 500 (^SPX) daily close data",
        "stooq_url": "https://stooq.com/q/d/l/?s=%5Espx&i=d",
        "yahoo_symbol": "^GSPC",
        "target": DATA_DIR / "sp500.csv",
    },
    {
        "label": "Nasdaq 100 (^NDX) daily close data",
        "stooq_url": "https://stooq.com/q/d/l/?s=%5Endx&i=d",
        "yahoo_symbol": "^NDX",
        "target": DATA_DIR / "nasdaq100.csv",
    },
]


def read_existing_price_rows(path: Path) -> list[tuple[str, str, str, str, str, str]]:
    if not path.exists():
        return []

    rows: list[tuple[str, str, str, str, str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            rows.append(
                (
                    item["Date"],
                    item["Open"],
                    item["High"],
                    item["Low"],
                    item["Close"],
                    item["Volume"],
                )
            )
    return rows


def write_price_csv(path: Path, rows: list[tuple[str, str, str, str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
        writer.writerows(rows)
    temp_path.replace(path)


def parse_stooq_csv(text: str) -> list[tuple[str, str, str, str, str, str]]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Empty Stooq response")

    reader = csv.reader(stripped.splitlines())
    header = next(reader, None)
    if header != ["Date", "Open", "High", "Low", "Close", "Volume"]:
        raise ValueError(f"Unexpected Stooq header: {header}")

    rows = [tuple(fields[:6]) for fields in reader if len(fields) >= 6]
    if len(rows) < 100:
        raise ValueError(f"Stooq response too short: {len(rows)} rows")
    return rows


def format_price(value: float) -> str:
    return f"{value:.2f}"


def build_yahoo_price_rows(payload: dict) -> list[tuple[str, str, str, str, str, str]]:
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]

    rows: list[tuple[str, str, str, str, str, str]] = []
    for timestamp, open_, high, low, close, volume in zip(
        result["timestamp"],
        quote["open"],
        quote["high"],
        quote["low"],
        quote["close"],
        quote["volume"],
    ):
        if None in (open_, high, low, close):
            continue

        day = datetime.fromtimestamp(int(timestamp), UTC).date().isoformat()
        volume_value = 0 if volume is None else int(volume)
        rows.append(
            (
                day,
                format_price(float(open_)),
                format_price(float(high)),
                format_price(float(low)),
                format_price(float(close)),
                str(volume_value),
            )
        )

    if len(rows) < 100:
        raise ValueError(f"Yahoo response too short: {len(rows)} rows")
    return rows


def merge_price_rows(
    existing_rows: list[tuple[str, str, str, str, str, str]],
    fresh_rows: list[tuple[str, str, str, str, str, str]],
) -> list[tuple[str, str, str, str, str, str]]:
    merged = {row[0]: row for row in existing_rows}
    for row in fresh_rows:
        merged[row[0]] = row
    return [merged[date_key] for date_key in sorted(merged)]


def load_market_rows(
    *,
    existing_rows: list[tuple[str, str, str, str, str, str]],
    stooq_fetcher,
    yahoo_fetcher,
) -> tuple[list[tuple[str, str, str, str, str, str]], str]:
    try:
        return parse_stooq_csv(stooq_fetcher()), "stooq"
    except Exception:
        try:
            yahoo_rows = build_yahoo_price_rows(yahoo_fetcher())
            return merge_price_rows(existing_rows, yahoo_rows), "yahoo"
        except Exception:
            if existing_rows:
                return existing_rows, "cache"
            raise


def fetch_text(url: str) -> str:
    result = subprocess.run(
        [
            "curl",
            "--noproxy",
            "*",
            "--silent",
            "--show-error",
            "--location",
            "--connect-timeout",
            "15",
            "--max-time",
            "90",
            "-H",
            f"User-Agent: {USER_AGENT}",
            url,
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout


def fetch_yahoo_payload(symbol: str) -> dict:
    url = (
        YAHOO_CHART_ENDPOINT.format(symbol=symbol.replace("^", "%5E"))
        + f"?period1=0&period2={int(time.time())}&interval=1d&includePrePost=false&events=div%2Csplits"
    )
    return json.loads(fetch_text(url))


def main() -> int:
    for series in SERIES:
        existing_rows = read_existing_price_rows(series["target"])
        rows, source = load_market_rows(
            existing_rows=existing_rows,
            stooq_fetcher=lambda url=series["stooq_url"]: fetch_text(url),
            yahoo_fetcher=lambda symbol=series["yahoo_symbol"]: fetch_yahoo_payload(symbol),
        )
        write_price_csv(series["target"], rows)
        if source == "cache":
            print(
                f"Both primary and fallback price sources were unavailable for {series['label']}; reusing cached data.",
                file=sys.stderr,
            )
        print(
            f"Wrote {len(rows)} rows to {series['target']} via "
            f"{'Stooq' if source == 'stooq' else 'Yahoo Finance fallback' if source == 'yahoo' else 'cached data'}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
