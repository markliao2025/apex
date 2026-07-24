"""Small, dependency-free TLE validation helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def parse_tle_epoch(line1: str) -> datetime:
    """Parse the fixed-width YYDDD.dddddddd TLE epoch using the 57/00 rule."""
    if len(line1) < 32 or not line1.startswith("1 "):
        raise ValueError("TLE line 1 is too short or has the wrong prefix")
    raw = line1[18:32].strip()
    if len(raw) < 5:
        raise ValueError("TLE epoch field is missing")
    try:
        two_digit_year = int(raw[:2])
        day_of_year = float(raw[2:])
    except ValueError as exc:
        raise ValueError("TLE epoch is not YYDDD.fraction") from exc
    year = 1900 + two_digit_year if two_digit_year >= 57 else 2000 + two_digit_year
    whole_day = int(day_of_year)
    if whole_day < 1 or whole_day > 366:
        raise ValueError("TLE day of year is outside 1..366")
    fraction = day_of_year - whole_day
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=whole_day - 1, seconds=fraction * 86400
    )
