"""Shared freshness policy for source selection and final publication checks."""

import math
from datetime import date, timedelta


SERIES_MAX_STALENESS_DAYS = {
    "sp500_price": 7,
    "sp500_total_return": 7,
    "nasdaq100_price": 7,
    "nasdaq100_total_return": 7,
    "hs300_price": 7,
    "hs300_total_return": 7,
    "nikkei225_price": 7,
    "nikkei225_total_return": 7,
    "usdcny": 10,
    "usdjpy": 10,
}


# SSE's published exchange closures, shared by both CSI 300 return series.
# https://www.sse.com.cn/disclosure/dealinstruc/closed/c/c_20251222_10802510.shtml
# Add each year's official schedule when published. Unknown years retain the
# ordinary calendar-day limit; do not infer trading holidays from civil holidays.
HS300_HOLIDAY_RANGES = {
    2026: (
        ("2026-01-01", "2026-01-03"),
        ("2026-02-15", "2026-02-23"),
        ("2026-04-04", "2026-04-06"),
        ("2026-05-01", "2026-05-05"),
        ("2026-06-19", "2026-06-21"),
        ("2026-09-25", "2026-09-27"),
        ("2026-10-01", "2026-10-07"),
    ),
}


def freshness_policy(series_id, latest_date, reference_date):
    """Extend the existing tolerance by confirmed weekday exchange closures.

    Only count closures after the last observation and through the reference
    date. Weekends already fit within the ordinary tolerance and get no extra
    allowance. Never relax another market's policy because China is closed.
    """
    base_limit = SERIES_MAX_STALENESS_DAYS.get(series_id, 7)
    holiday_days = 0
    if series_id in ("hs300_price", "hs300_total_return"):
        for ranges in HS300_HOLIDAY_RANGES.values():
            for start, end in ranges:
                day = max(date.fromisoformat(start), latest_date + timedelta(days=1))
                last = min(date.fromisoformat(end), reference_date)
                while day <= last:
                    if day.weekday() < 5:
                        holiday_days += 1
                    day += timedelta(days=1)
    age = (reference_date - latest_date).days
    limit = base_limit + holiday_days
    return {
        "ok": 0 <= age <= limit,
        "stalenessDays": age,
        "baseMaxStalenessDays": base_limit,
        "holidayAllowanceDays": holiday_days,
        "maxStalenessDays": limit,
    }


def validate_source_rows(rows, series_id, reference_date=None, require_fresh=True):
    """Reject empty, invalid or stale HTTP-200 responses before selecting a source."""
    if not rows:
        raise ValueError(f"{series_id}: source returned no rows")
    today = reference_date or date.today()
    dates = []
    for day, close in rows:
        parsed = date.fromisoformat(day)
        if parsed > today or not math.isfinite(float(close)) or float(close) <= 0:
            raise ValueError(f"{series_id}: invalid observation {day}, {close}")
        dates.append(parsed)
    policy = freshness_policy(series_id, max(dates), today)
    age = policy["stalenessDays"]
    limit = policy["maxStalenessDays"]
    if require_fresh and not policy["ok"]:
        raise ValueError(f"{series_id}: latest={max(dates)}, age={age} days, limit={limit} days")
    return rows
