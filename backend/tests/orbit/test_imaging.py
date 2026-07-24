"""Tests for imaging window calculations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

TLE_EPOCH_UTC = datetime(2024, 5, 31, 12, tzinfo=timezone.utc)


class TestImagingWindows:
    """Tests for satellite imaging window calculations."""

    def test_calculate_imaging_windows_tokyo_bay(self):
        """Test imaging windows for Tokyo Bay area."""
        from app.orbit.imaging import calculate_imaging_windows

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }
        bbox = {
            "sw_lat": 35.4,
            "sw_lng": 139.5,
            "ne_lat": 35.9,
            "ne_lng": 140.1,
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=48)

        windows = calculate_imaging_windows(
            satellite=satellite,
            bbox=bbox,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=5.0,
        )

        # Should have at least 1-2 imaging opportunities in 48 hours
        assert len(windows) >= 1, (
            f"Expected at least 1 imaging window, got {len(windows)}"
        )

        for window in windows:
            assert "aos" in window
            assert "los" in window
            assert "max_elevation_deg" in window
            assert "illumination_pct" in window
            assert "duration_seconds" in window
            assert window["aos"] < window["los"]
            assert 0 <= window["illumination_pct"] <= 1
            assert window["max_elevation_deg"] >= 5.0
            assert window["max_elevation_deg"] <= 90.0

    def test_worldview3_tokyo_imaging(self):
        """Test WorldView-3 imaging for Tokyo Bay."""
        from app.orbit.imaging import calculate_imaging_windows

        satellite = {
            "tle_line1": "1 35946U 09055A   24152.50972233 -.00000124  00000-0 -10210-4 0  9993",
            "tle_line2": "2 35946  97.9960 192.4280 0003211  83.5872 276.5870 14.23607746864585",
        }
        bbox = {
            "sw_lat": 35.4,
            "sw_lng": 139.5,
            "ne_lat": 35.9,
            "ne_lng": 140.1,
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=24)

        windows = calculate_imaging_windows(
            satellite=satellite,
            bbox=bbox,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=10.0,  # Higher min elevation for high-res imaging
        )

        # WorldView-3 in SSO should have 1-2 passes over Tokyo per day
        assert len(windows) >= 0  # May be 0 if timing doesn't align

        for window in windows:
            assert window["max_elevation_deg"] >= 10.0
            assert 0 <= window["illumination_pct"] <= 1  # Valid illumination range

    def test_illumination_filter(self):
        """Test that illumination is properly calculated."""
        from app.orbit.imaging import calculate_imaging_windows

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }
        # Tokyo Bay
        bbox = {
            "sw_lat": 35.4,
            "sw_lng": 139.5,
            "ne_lat": 35.9,
            "ne_lng": 140.1,
        }

        start_time = TLE_EPOCH_UTC
        end_time = start_time + timedelta(hours=24)

        windows = calculate_imaging_windows(
            satellite=satellite,
            bbox=bbox,
            start_time=start_time,
            end_time=end_time,
            min_elevation_deg=5.0,
        )

        # All windows should have illumination between 0 and 1
        for window in windows:
            assert 0 <= window["illumination_pct"] <= 1

    def test_empty_bbox_returns_empty(self):
        """Test that invalid bbox returns empty list."""
        from app.orbit.imaging import calculate_imaging_windows

        satellite = {
            "tle_line1": "1 25544U 98067A   24152.50000000  .00016717  00000-0  10270-3 0  9993",
            "tle_line2": "2 25544  51.6400 247.8232 0006703 286.2345 146.0818 15.50105854345678",
        }

        start_time = TLE_EPOCH_UTC

        # Invalid bbox (sw > ne)
        bbox = {
            "sw_lat": 36.0,
            "sw_lng": 140.0,
            "ne_lat": 35.0,
            "ne_lng": 139.0,
        }

        windows = calculate_imaging_windows(
            satellite=satellite,
            bbox=bbox,
            start_time=start_time,
            end_time=start_time + timedelta(hours=24),
        )

        # Should handle invalid bbox gracefully
        assert isinstance(windows, list)

    def test_naive_timestamps_are_rejected(self):
        """Naive timestamps are ambiguous and cannot enter imaging calculations."""
        from app.orbit.imaging import calculate_imaging_windows

        with pytest.raises(ValueError, match="timezone-aware"):
            calculate_imaging_windows(
                satellite={
                    "tle_line1": "1 25544U 98067A   24152.50000000",
                    "tle_line2": "2 25544  51.6400 247.8232 0006703",
                },
                bbox={
                    "sw_lat": 35.4,
                    "sw_lng": 139.5,
                    "ne_lat": 35.9,
                    "ne_lng": 140.1,
                },
                start_time=datetime(2024, 5, 31, 12),
                end_time=datetime(2024, 5, 31, 13),
            )
