#!/usr/bin/env python3

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "web" / "data"
USER_AGENT = "Mozilla/5.0"

NASDAQ_HISTORY_ENDPOINT = "https://indexes.nasdaq.com/Index/HistoryChartData"
NASDAQ_START_DATE = "1999-03-10T00:00:00"
YAHOO_CHART_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def fetch_nasdaq100_total_return(end_date: date) -> list[tuple[str, float]]:
    payload = urllib.parse.urlencode(
        {
            "id": "XNDX",
            "startDate": NASDAQ_START_DATE,
            "endDate": f"{end_date.isoformat()}T00:00:00",
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        NASDAQ_HISTORY_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)

    rows = []
    for item in payload:
        timestamp_ms = int(item["x"])
        close = float(item["y"])
        day = datetime.utcfromtimestamp(timestamp_ms / 1000).date()
        rows.append((day.isoformat(), close))

    return rows


def fetch_yahoo_total_return(symbol: str, period1: int) -> list[tuple[str, float]]:
    url = (
        YAHOO_CHART_ENDPOINT.format(symbol=urllib.parse.quote(symbol))
        + f"?period1={period1}&period2={int(time.time())}&interval=1d&includePrePost=false&events=div%2Csplits"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)

    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]

    rows = []
    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.utcfromtimestamp(int(timestamp)).date()
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

    try:
        sp500_rows = fetch_yahoo_total_return("^SP500TR", period1=568305000)
        nasdaq_rows = fetch_nasdaq100_total_return(end_date)
    except Exception as exc:  # pragma: no cover - simple CLI script
        print(f"Failed to fetch total return data: {exc}", file=sys.stderr)
        return 1

    sp500_target = DATA_DIR / "sp500-total-return.csv"
    nasdaq_target = DATA_DIR / "nasdaq100-total-return.csv"

    write_csv(sp500_target, sp500_rows)
    write_csv(nasdaq_target, nasdaq_rows)

    print(f"Wrote {len(sp500_rows)} rows to {sp500_target}")
    print(f"Wrote {len(nasdaq_rows)} rows to {nasdaq_target}")
    print("S&P 500 total return source: Yahoo Finance ^SP500TR (official S&P 500 TR concept maps to SPXT)")
    print("Nasdaq-100 total return source: https://indexes.nasdaq.com/Index/History/XNDX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
