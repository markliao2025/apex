"""TLE epoch parsing is deterministic and timezone-aware."""

from datetime import timezone

import pytest

from app.orbit.tle import parse_tle_epoch


def test_parse_modern_tle_epoch() -> None:
    parsed = parse_tle_epoch(
        "1 40697U 15028A   26185.27762785 -.00000101  00000+0 -22011-4 0  9991"
    )
    assert parsed.year == 2026
    assert parsed.timetuple().tm_yday == 185
    assert parsed.tzinfo == timezone.utc


def test_parse_57_boundary() -> None:
    assert parse_tle_epoch("1 00001U 00001A   57001.00000000").year == 1957
    assert parse_tle_epoch("1 00001U 00001A   56001.00000000").year == 2056


def test_invalid_tle_epoch_rejected() -> None:
    with pytest.raises(ValueError):
        parse_tle_epoch("not-a-tle")
