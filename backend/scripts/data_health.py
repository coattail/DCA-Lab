"""Shared freshness policy for source selection and final publication checks."""

import math
from datetime import date


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
    age = (today - max(dates)).days
    limit = SERIES_MAX_STALENESS_DAYS[series_id]
    if require_fresh and age > limit:
        raise ValueError(f"{series_id}: latest={max(dates)}, age={age} days, limit={limit} days")
    return rows
