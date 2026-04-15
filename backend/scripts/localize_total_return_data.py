#!/usr/bin/env python3

import csv
import json
import subprocess
import sys
import time
import urllib.parse
from datetime import UTC, date, datetime, time as dt_time, timedelta
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "web" / "data"
USER_AGENT = "Mozilla/5.0"

NASDAQ_HISTORY_ENDPOINT = "https://indexes.nasdaq.com/Index/HistoryChartData"
NASDAQ_START_DATE = date(1999, 3, 10)
SP500_TOTAL_RETURN_START_DATE = date(1988, 1, 4)
TOTAL_RETURN_LOOKBACK_DAYS = 90
YAHOO_CHART_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def fetch_json_with_retry(send_request, *, attempts: int = 3) -> dict | list:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return send_request()
        except (requests.RequestException, subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt == attempts:
                raise
            time.sleep(attempt)
    raise RuntimeError("JSON request failed without raising an exception") from last_error


def fetch_json_via_curl(url: str, *, data: dict[str, str] | None = None) -> dict | list:
    command = [
        "curl",
        "--noproxy",
        "*",
        "--silent",
        "--show-error",
        "--location",
        "--fail",
        "--http1.1",
        "--connect-timeout",
        "15",
        "--max-time",
        "90",
        "--retry",
        "3",
        "--retry-delay",
        "1",
        "--retry-all-errors",
        "-H",
        f"User-Agent: {USER_AGENT}",
        "-H",
        "Accept: application/json,text/plain,*/*",
    ]
    if data is not None:
        command.extend(
            [
                "-X",
                "POST",
                "-H",
                "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
                "--data",
                urllib.parse.urlencode(data),
            ]
        )
    command.append(url)
    output = subprocess.run(command, capture_output=True, check=True, text=True).stdout
    return json.loads(output)


def read_existing_csv_rows(path: Path) -> list[tuple[str, float]]:
    if not path.exists():
        return []

    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            rows.append((item["Date"], float(item["Close"])))
    return rows


def merge_close_rows(
    existing_rows: list[tuple[str, float]],
    fresh_rows: list[tuple[str, float]],
) -> list[tuple[str, float]]:
    merged = {date_key: close for date_key, close in existing_rows}
    for date_key, close in fresh_rows:
        merged[date_key] = close
    return [(date_key, merged[date_key]) for date_key in sorted(merged)]


def resolve_refresh_start(existing_rows: list[tuple[str, float]], minimum_date: date) -> date:
    if not existing_rows:
        return minimum_date

    latest_date = datetime.strptime(existing_rows[-1][0], "%Y-%m-%d").date()
    rewind_start = latest_date - timedelta(days=TOTAL_RETURN_LOOKBACK_DAYS)
    return max(minimum_date, rewind_start)


def fetch_nasdaq100_total_return(start_date: date, end_date: date) -> list[tuple[str, float]]:
    payload = fetch_json_with_retry(
        lambda: fetch_json_via_curl(
            NASDAQ_HISTORY_ENDPOINT,
            data={
                "id": "XNDX",
                "startDate": f"{start_date.isoformat()}T00:00:00",
                "endDate": f"{end_date.isoformat()}T00:00:00",
            },
        )
    )

    rows = []
    for item in payload:
        timestamp_ms = int(item["x"])
        close = float(item["y"])
        day = datetime.fromtimestamp(timestamp_ms / 1000, UTC).date()
        rows.append((day.isoformat(), close))

    return rows


def fetch_yahoo_total_return(symbol: str, start_date: date) -> list[tuple[str, float]]:
    period1 = int(datetime.combine(start_date, dt_time.min, tzinfo=UTC).timestamp())
    url = (
        YAHOO_CHART_ENDPOINT.format(symbol=urllib.parse.quote(symbol))
        + f"?period1={period1}&period2={int(time.time())}&interval=1d&includePrePost=false&events=div%2Csplits"
    )
    payload = fetch_json_with_retry(lambda: fetch_json_via_curl(url))

    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]

    rows = []
    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(int(timestamp), UTC).date()
        rows.append((day.isoformat(), float(close)))

    return rows


def write_csv(path: Path, rows: list[tuple[str, float]]) -> None:
    unique_rows = []
    seen_dates = set()
    for date_key, close in reversed(rows):
        if date_key in seen_dates:
            continue
        if close <= 0:
            continue
        seen_dates.add(date_key)
        unique_rows.append((date_key, close))
    unique_rows.reverse()

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Date", "Close"])
        for date_key, close in unique_rows:
            writer.writerow([date_key, f"{close:.8f}"])
    temp_path.replace(path)


def main() -> int:
    end_date = date.today()
    sp500_target = DATA_DIR / "sp500-total-return.csv"
    nasdaq_target = DATA_DIR / "nasdaq100-total-return.csv"
    existing_sp500_rows = read_existing_csv_rows(sp500_target)
    existing_nasdaq_rows = read_existing_csv_rows(nasdaq_target)

    try:
        sp500_rows = merge_close_rows(
            existing_sp500_rows,
            fetch_yahoo_total_return(
                "^SP500TR",
                start_date=resolve_refresh_start(existing_sp500_rows, minimum_date=SP500_TOTAL_RETURN_START_DATE),
            ),
        )
        nasdaq_rows = merge_close_rows(
            existing_nasdaq_rows,
            fetch_nasdaq100_total_return(
                start_date=resolve_refresh_start(existing_nasdaq_rows, minimum_date=NASDAQ_START_DATE),
                end_date=end_date,
            ),
        )
    except Exception as exc:  # pragma: no cover - simple CLI script
        print(f"Failed to fetch total return data: {exc}", file=sys.stderr)
        return 1

    write_csv(sp500_target, sp500_rows)
    write_csv(nasdaq_target, nasdaq_rows)

    print(f"Wrote {len(sp500_rows)} rows to {sp500_target}")
    print(f"Wrote {len(nasdaq_rows)} rows to {nasdaq_target}")
    print("S&P 500 total return source: Yahoo Finance ^SP500TR (official S&P 500 TR concept maps to SPXT)")
    print("Nasdaq-100 total return source: https://indexes.nasdaq.com/Index/History/XNDX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
