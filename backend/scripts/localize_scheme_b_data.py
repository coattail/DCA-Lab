#!/usr/bin/env python3

import csv
import math
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests

try:
    import cloudscraper
except ImportError as exc:  # pragma: no cover - CLI helper
    raise SystemExit("Missing dependency: cloudscraper. Install it with `python3 -m pip install cloudscraper`.") from exc

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - CLI helper
    raise SystemExit("Missing dependency: pypdf. Install it with `python3 -m pip install pypdf`.") from exc


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "web" / "data"
CACHE_DIR = ROOT_DIR / "backend" / "cache"
USER_AGENT = "Mozilla/5.0"

CSINDEX_ENDPOINT = "https://www.csindex.com.cn/csindex-home/perf/index-perf"
EASTMONEY_ENDPOINT = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
FRED_ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv"
NIKKEI_DATALOAD_ENDPOINT = "https://indexes.nikkei.co.jp/en/nkave/statistics/dataload"
NIKKEI_NEWSROOM_ENDPOINT = "https://indexes.nikkei.co.jp/en/nkave/newsroom"
NIKKEI_TOTAL_RETURN_DAILY_CSV = "https://indexes.nikkei.co.jp/en/nkave/historical/nikkei_225_total_return_index_daily_en.csv"
NIKKEI_TOTAL_RETURN_MONTHLY_CSV = "https://indexes.nikkei.co.jp/en/nkave/historical/nikkei_225_total_return_index_monthly_en.csv"

NIKKEI_START_YEAR = 1985
NIKKEI_MAX_WORKERS = 12
NIKKEI_REQUEST_TIMEOUT = 45
NIKKEI_INCREMENTAL_LOOKBACK_MONTHS = 4
NIKKEI_MONTHLY_REPORT_START_YEAR = 2012
NIKKEI_MONTHLY_REPORT_END_YEAR = 2015
NIKKEI_MONTHLY_REPORT_CACHE = CACHE_DIR / "nikkei225-total-return-report-anchors.csv"
HS300_TOTAL_RETURN_START = "2005-04-08"

_NIKKEI_THREAD_LOCAL = threading.local()


def make_requests_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    session.trust_env = False
    return session


def make_nikkei_scraper():
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "darwin", "mobile": False})
    scraper.trust_env = False
    return scraper


def get_thread_nikkei_scraper():
    scraper = getattr(_NIKKEI_THREAD_LOCAL, "scraper", None)
    if scraper is None:
        scraper = make_nikkei_scraper()
        _NIKKEI_THREAD_LOCAL.scraper = scraper
    return scraper


def normalize_date_key(value: str) -> str:
    raw = str(value).strip().strip('"')
    if re.fullmatch(r"\d{8}", raw):
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}", raw):
        return datetime.strptime(raw, "%Y/%m/%d").date().isoformat()
    raise ValueError(f"Unsupported date format: {value}")


def parse_nikkei_date(value: str) -> str:
    return datetime.strptime(value, "%b/%d/%Y").date().isoformat()


def month_shift(year: int, month: int, delta: int) -> tuple[int, int]:
    ordinal = year * 12 + (month - 1) + delta
    return ordinal // 12, ordinal % 12 + 1


def read_existing_csv_rows(path: Path) -> list[tuple[str, float]]:
    if not path.exists():
        return []

    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            date_key = normalize_date_key(item["Date"])
            close = float(item["Close"])
            if close > 0:
                rows.append((date_key, close))
    return rows


def read_anchor_cache(path: Path) -> list[tuple[str, float]]:
    if not path.exists():
        return []

    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            rows.append((normalize_date_key(item["Date"]), float(item["Close"])))
    rows.sort(key=lambda item: item[0])
    return rows


def write_anchor_cache(path: Path, rows: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Date", "Close"])
        for date_key, close in rows:
            writer.writerow([date_key, f"{close:.8f}"])
    temp_path.replace(path)


def fetch_csindex_total_return(index_code: str, start_date: str, end_date: str) -> list[tuple[str, float]]:
    session = make_requests_session()
    response = session.get(
        CSINDEX_ENDPOINT,
        params={"indexCode": index_code, "startDate": start_date, "endDate": end_date, "cycle": "day"},
        headers={"Referer": f"https://www.csindex.com.cn/zh-CN/indices/index-detail/{index_code}"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != "200":
        raise RuntimeError(f"CSI total return request failed for {index_code}: {payload}")

    rows = []
    for item in payload.get("data") or []:
        close = item.get("close")
        if close in (None, ""):
            continue
        rows.append((normalize_date_key(item["tradeDate"]), float(close)))
    return rows


def fetch_eastmoney_index(index_code: str, market: str) -> list[tuple[str, float]]:
    session = make_requests_session()
    response = session.get(
        EASTMONEY_ENDPOINT,
        params={
            "secid": f"{market}.{index_code}",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56",
            "klt": "101",
            "fqt": "0",
            "beg": "19800101",
            "end": "20500101",
        },
        headers={"Referer": "https://quote.eastmoney.com/"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    klines = ((payload.get("data") or {}).get("klines")) or []
    rows = []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        rows.append((normalize_date_key(parts[0]), float(parts[2])))
    return rows


def fetch_nikkei_price_history() -> list[tuple[str, float]]:
    today = date.today()
    existing_rows = read_existing_csv_rows(DATA_DIR / "nikkei225.csv")

    preserved_rows: list[tuple[str, float]] = []
    if existing_rows:
        latest_date = datetime.strptime(existing_rows[-1][0], "%Y-%m-%d").date()
        start_year, start_month = month_shift(latest_date.year, latest_date.month, -(NIKKEI_INCREMENTAL_LOOKBACK_MONTHS - 1))
        refetch_start = date(start_year, start_month, 1)
        preserved_rows = [row for row in existing_rows if row[0] < refetch_start.isoformat()]
    else:
        start_year, start_month = NIKKEI_START_YEAR, 1

    tasks: list[tuple[int, int]] = []
    for year in range(start_year, today.year + 1):
        month_from = start_month if year == start_year else 1
        month_to = today.month if year == today.year else 12
        for month in range(month_from, month_to + 1):
            tasks.append((year, month))

    rows = preserved_rows[:]
    with ThreadPoolExecutor(max_workers=NIKKEI_MAX_WORKERS) as executor:
        for month_rows in executor.map(fetch_nikkei_month_history, tasks):
            rows.extend(month_rows)

    rows.sort(key=lambda item: item[0])
    return rows


def fetch_nikkei_month_history(task: tuple[int, int]) -> list[tuple[str, float]]:
    year, month = task
    scraper = get_thread_nikkei_scraper()

    last_error: Optional[Exception] = None
    for _attempt in range(3):
        try:
            response = scraper.get(
                NIKKEI_DATALOAD_ENDPOINT,
                params={"list": "daily", "year": str(year), "month": str(month)},
                timeout=NIKKEI_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return parse_nikkei_dataload(response.text)
        except Exception as exc:  # pragma: no cover - network retry helper
            last_error = exc

    raise RuntimeError(f"Failed to fetch Nikkei month {year}-{month:02d}") from last_error


def parse_nikkei_dataload(html: str) -> list[tuple[str, float]]:
    pattern = re.compile(
        r"<tr>\s*<td>([^<]+)</td>\s*<td>[^<]*</td>\s*<td>[^<]*</td>\s*<td>[^<]*</td>\s*<td>([^<]+)</td>",
        re.S,
    )
    rows = []
    for raw_date, raw_close in pattern.findall(html):
        close_text = raw_close.replace(",", "").strip()
        if not close_text:
            continue
        rows.append((parse_nikkei_date(raw_date.strip()), float(close_text)))
    return rows


def parse_nikkei_tr_csv(text: str, close_index: int) -> list[tuple[str, float]]:
    rows = []
    reader = csv.reader(text.splitlines())
    next(reader, None)
    for fields in reader:
        if len(fields) <= close_index:
            continue
        raw_date = fields[0].strip().strip('"')
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", raw_date):
            continue
        close_text = fields[close_index].strip().strip('"').replace(",", "")
        if not close_text:
            continue
        rows.append((normalize_date_key(raw_date), float(close_text)))
    return rows


def fetch_nikkei_total_return_daily_history() -> list[tuple[str, float]]:
    scraper = make_nikkei_scraper()
    response = scraper.get(NIKKEI_TOTAL_RETURN_DAILY_CSV, timeout=60)
    response.raise_for_status()
    return parse_nikkei_tr_csv(response.text, close_index=1)


def fetch_nikkei_total_return_monthly_history() -> list[tuple[str, float]]:
    scraper = make_nikkei_scraper()
    response = scraper.get(NIKKEI_TOTAL_RETURN_MONTHLY_CSV, timeout=60)
    response.raise_for_status()
    return parse_nikkei_tr_csv(response.text, close_index=1)


def build_month_end_map(rows: list[tuple[str, float]]) -> dict[tuple[int, int], tuple[str, float]]:
    mapping: dict[tuple[int, int], tuple[str, float]] = {}
    for date_key, close in rows:
        current = datetime.strptime(date_key, "%Y-%m-%d").date()
        mapping[(current.year, current.month)] = (date_key, close)
    return mapping


def fetch_nikkei_monthly_report_anchors(price_rows: list[tuple[str, float]]) -> list[tuple[str, float]]:
    cached_rows = read_anchor_cache(NIKKEI_MONTHLY_REPORT_CACHE)
    if cached_rows:
        return cached_rows

    month_end_map = build_month_end_map(price_rows)
    scraper = make_nikkei_scraper()
    report_urls = []
    for year in range(NIKKEI_MONTHLY_REPORT_START_YEAR, NIKKEI_MONTHLY_REPORT_END_YEAR + 1):
        response = scraper.get(
            NIKKEI_NEWSROOM_ENDPOINT,
            params={"evt": "10021", "idxtag": "", "year": str(year)},
            timeout=60,
        )
        response.raise_for_status()
        for href in re.findall(r'href="([^"]+\.pdf)"', response.text):
            if "/archives/news/" in href and href not in report_urls:
                report_urls.append(href)

    anchors = []
    for href in sorted(report_urls):
        anchor = extract_nikkei_monthly_report_anchor(scraper, href, month_end_map)
        if anchor is not None:
            anchors.append(anchor)

    unique = []
    seen = set()
    for date_key, close in sorted(anchors, key=lambda item: item[0]):
        if date_key in seen:
            continue
        seen.add(date_key)
        unique.append((date_key, close))

    write_anchor_cache(NIKKEI_MONTHLY_REPORT_CACHE, unique)
    return unique


def extract_nikkei_monthly_report_anchor(
    scraper,
    href: str,
    month_end_map: dict[tuple[int, int], tuple[str, float]],
) -> Optional[tuple[str, float]]:
    response = scraper.get(f"https://indexes.nikkei.co.jp{href}", timeout=60)
    response.raise_for_status()
    text = "\n".join((page.extract_text() or "") for page in PdfReader(BytesIO(response.content)).pages)
    if "Nikkei Indexes Monthly Report" not in text:
        return None

    if "began calculating and publishing the Nikkei 225 Total Return Index" in text:
        match = re.search(r"index value on the day was\s+([0-9,]+\.\d+)", text, re.I)
        if match:
            return ("2012-12-03", float(match.group(1).replace(",", "")))

    match = re.search(r"Nikkei 225 TR\s+([0-9,]+\.\d+)", text)
    if not match:
        return None

    filename_match = re.search(r"(\d{8})E_", href)
    if not filename_match:
        return None

    report_date = datetime.strptime(filename_match.group(1), "%Y%m%d").date()
    anchor_year, anchor_month = month_shift(report_date.year, report_date.month, -1)
    month_end = month_end_map.get((anchor_year, anchor_month))
    if not month_end:
        return None

    return (month_end[0], float(match.group(1).replace(",", "")))


def map_monthly_tr_rows_to_trading_days(
    monthly_rows: list[tuple[str, float]],
    month_end_map: dict[tuple[int, int], tuple[str, float]],
) -> list[tuple[str, float]]:
    anchors = []
    for month_key, close in monthly_rows:
        current = datetime.strptime(month_key, "%Y-%m-%d").date()
        month_end = month_end_map.get((current.year, current.month))
        if not month_end:
            continue
        anchors.append((month_end[0], close))
    return anchors


def build_nikkei_total_return_history(price_rows: list[tuple[str, float]]) -> list[tuple[str, float]]:
    daily_rows = fetch_nikkei_total_return_daily_history()
    monthly_rows = fetch_nikkei_total_return_monthly_history()
    report_anchors = fetch_nikkei_monthly_report_anchors(price_rows)
    month_end_map = build_month_end_map(price_rows)
    monthly_anchors = map_monthly_tr_rows_to_trading_days(monthly_rows, month_end_map)

    daily_start = daily_rows[0][0]
    price_map = {date_key: close for date_key, close in price_rows}
    anchor_rows = report_anchors + [row for row in monthly_anchors if row[0] < daily_start] + [daily_rows[0]]
    anchor_rows.sort(key=lambda item: item[0])

    synthesized = []
    for index in range(len(anchor_rows) - 1):
        start_date, start_value = anchor_rows[index]
        end_date, end_value = anchor_rows[index + 1]
        segment = [row for row in price_rows if start_date <= row[0] <= end_date]
        if not segment:
            continue

        start_price = price_map.get(start_date)
        end_price = price_map.get(end_date)
        if not start_price or not end_price:
            continue

        start_ratio = start_value / start_price
        end_ratio = end_value / end_price
        steps = max(1, len(segment) - 1)

        for offset, (date_key, price_close) in enumerate(segment):
            if index > 0 and offset == 0:
                continue
            if offset == steps:
                ratio = end_ratio
            else:
                fraction = offset / steps
                ratio = math.exp(math.log(start_ratio) + (math.log(end_ratio) - math.log(start_ratio)) * fraction)
            synthesized.append((date_key, price_close * ratio))

    return synthesized + daily_rows


def fetch_fred_series(series_id: str) -> list[tuple[str, float]]:
    try:
        output = subprocess.run(
            ["curl", "--noproxy", "*", "-L", "--fail", "--max-time", "120", f"{FRED_ENDPOINT}?id={series_id}"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
    except subprocess.CalledProcessError as exc:  # pragma: no cover - CLI network helper
        raise RuntimeError(f"Failed to fetch FRED series {series_id}") from exc

    rows = []
    reader = csv.reader(output.splitlines())
    next(reader, None)
    for fields in reader:
        if len(fields) < 2:
            continue
        date_key, close = fields[0].strip(), fields[1].strip()
        if not date_key or not close or close == ".":
            continue
        rows.append((date_key, float(close)))
    return rows


def write_csv(path: Path, rows: list[tuple[str, float]]) -> None:
    unique_rows = []
    seen_dates = set()
    for date_key, close in reversed(rows):
        if date_key in seen_dates:
            continue
        if not date_key or close <= 0:
            continue
        seen_dates.add(date_key)
        unique_rows.append((date_key, close))
    unique_rows.reverse()
    unique_rows.sort(key=lambda item: item[0])

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Date", "Close"])
        for date_key, close in unique_rows:
            writer.writerow([date_key, f"{close:.8f}"])
    temp_path.replace(path)


def main() -> int:
    end_date = date.today().isoformat()

    try:
        hs300_price = fetch_eastmoney_index("000300", market="1")
        hs300_total_return = fetch_csindex_total_return("H00300", HS300_TOTAL_RETURN_START, end_date)
        usdcny = fetch_fred_series("DEXCHUS")
        usdjpy = fetch_fred_series("DEXJPUS")
        nikkei_price = fetch_nikkei_price_history()
        nikkei_total_return = build_nikkei_total_return_history(nikkei_price)
    except Exception as exc:  # pragma: no cover - simple CLI script
        print(f"Failed to localize scheme-B data: {exc}", file=sys.stderr)
        return 1

    targets = {
        "hs300.csv": hs300_price,
        "hs300-total-return.csv": hs300_total_return,
        "nikkei225.csv": nikkei_price,
        "nikkei225-total-return.csv": nikkei_total_return,
        "usdcny.csv": usdcny,
        "usdjpy.csv": usdjpy,
    }

    for filename, rows in targets.items():
        target = DATA_DIR / filename
        write_csv(target, rows)
        print(f"Wrote {len(rows)} raw rows to {target}")

    print("HS300 price source: Eastmoney historical kline for 000300")
    print("HS300 total return source: CSI official H00300 history")
    print("Nikkei 225 price source: Nikkei official historical data page")
    print("Nikkei 225 total return source: Nikkei official daily CSV + monthly CSV + official monthly report anchors")
    print("FX sources: FRED DEXCHUS and DEXJPUS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
