"""Tests for satellite propagation and orbit calculations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

TLE_EPOCH_UTC = datetime(2024, 5, 31, 12, tzinfo=timezone.utc)


class TestPropagation:
    """Tests for satellite position propagation."""

    def test_calculate_overpass_windows_iss(self):
        """Test overpass window calculation for ISS over Tokyo."""
        from app.orbit.propagation import calculate_overpass_windows

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }
        ground_station = {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "altitude_m": 40.0,
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=24)

        windows = calculate_overpass_windows(
            satellite=satellite,
            ground_station=ground_station,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=5.0,
        )

        # ISS passes over Tokyo ~3-4 times per day
        assert len(windows) >= 2, f"Expected at least 2 overpasses, got {len(windows)}"

        for window in windows:
            assert window.aos < window.los
            assert window.max_elevation_deg >= 5.0
            assert window.duration_seconds > 0

    def test_calculate_overpass_windows_returns_dataclass(self):
        """Test that overpass windows returns proper dataclass objects."""
        from app.orbit.propagation import calculate_overpass_windows
        from app.orbit.types import OverpassWindow

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }
        ground_station = {
            "latitude": 35.6762,
            "longitude": 139.6503,
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=6)

        windows = calculate_overpass_windows(
            satellite=satellite,
            ground_station=ground_station,
            start_time=start_time,
            end_time=end_time,
        )

        for w in windows:
            assert isinstance(w, OverpassWindow)
            assert hasattr(w, "aos")
            assert hasattr(w, "los")
            assert hasattr(w, "max_elevation_deg")
            assert hasattr(w, "duration_seconds")

    def test_calculate_overpass_windows_min_elevation(self):
        """Test that min_elevation parameter filters results correctly."""
        from app.orbit.propagation import calculate_overpass_windows

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }
        ground_station = {
            "latitude": 35.6762,
            "longitude": 139.6503,
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=6)

        # Test with higher min elevation
        windows_low = calculate_overpass_windows(
            satellite=satellite,
            ground_station=ground_station,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=5.0,
        )

        windows_high = calculate_overpass_windows(
            satellite=satellite,
            ground_station=ground_station,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=30.0,
        )

        # Higher min elevation should return same or fewer windows
        assert len(windows_high) <= len(windows_low)

        # All windows should meet their min elevation threshold
        for w in windows_high:
            assert w.max_elevation_deg >= 30.0
            assert w.max_elevation_deg <= 90.0

    def test_invalid_tle_returns_empty(self):
        """Test that invalid TLE returns empty list."""
        from app.orbit.propagation import calculate_overpass_windows

        satellite = {
            "tle_line1": "INVALID",
            "tle_line2": "INVALID",
        }
        ground_station = {
            "latitude": 35.6762,
            "longitude": 139.6503,
        }

        windows = calculate_overpass_windows(
            satellite=satellite,
            ground_station=ground_station,
            start_time=TLE_EPOCH_UTC,
            end_time=TLE_EPOCH_UTC + timedelta(hours=1),
        )

        assert len(windows) == 0

    def test_naive_timestamps_are_rejected(self):
        """Naive timestamps are ambiguous and cannot enter orbital calculations."""
        from app.orbit.propagation import calculate_overpass_windows

        with pytest.raises(ValueError, match="timezone-aware"):
            calculate_overpass_windows(
                satellite={
                    "tle_line1": "1 25544U 98067A   24152.50000000",
                    "tle_line2": "2 25544  51.6400 247.8232 0006703",
                },
                ground_station={"latitude": 35.6762, "longitude": 139.6503},
                start_time=datetime(2024, 5, 31, 12),
                end_time=datetime(2024, 5, 31, 13),
            )


class TestGroundTrack:
    """Tests for satellite ground track calculation."""

    def test_calculate_ground_track(self):
        """Test ground track calculation."""
        from app.orbit.propagation import calculate_ground_track
        from app.orbit.types import GroundTrackPoint

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=1)

        points = calculate_ground_track(
            satellite=satellite,
            start_time=start_time,
            end_time=end_time,
            step_seconds=60,
        )

        assert len(points) >= 1
        for point in points:
            assert isinstance(point, GroundTrackPoint)
            assert hasattr(point, "timestamp")
            assert hasattr(point, "latitude")
            assert hasattr(point, "longitude")
            assert -90 <= point.latitude <= 90
            assert -180 <= point.longitude <= 180
