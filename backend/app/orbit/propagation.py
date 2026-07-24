"""Orbit propagation using skyfield EarthSatellite (SGP4).

Skyfield 1.54 API:
  - Topos has no .observe() — use vector subtraction:
      diff = sat.at(t) - topos.at(t)
      az, el, dist = diff.altaz()
  - ts.utc() requires tz-aware datetime (tzinfo=utc or pytz)
"""

from datetime import datetime, timedelta, timezone

from skyfield.api import EarthSatellite, Topos, load

from app.orbit.types import OverpassWindow, GroundTrackPoint


def _parse_tle(tle_line1: str, tle_line2: str) -> EarthSatellite:
    """Parse TLE lines into a skyfield EarthSatellite object."""
    return EarthSatellite(tle_line1.strip(), tle_line2.strip())


def _as_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime and reject ambiguous naive inputs."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Orbit calculation timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def calculate_overpass_windows(
    satellite: dict,
    ground_station: dict,
    start_time: datetime,
    end_time: datetime,
    min_elevation_deg: float = 5.0,
    step_seconds: int = 30,
) -> list[OverpassWindow]:
    """Calculate ground-station visibility windows for a satellite.

    Scans the time range at regular intervals, groups consecutive
    above-threshold samples into windows, and reports AOS / LOS / max_el.

    Args:
        satellite: Dict with 'tle_line1', 'tle_line2', 'id'.
        ground_station: Dict with 'latitude', 'longitude', 'altitude_m', 'id'.
        start_time: Search start (UTC).
        end_time: Search end (UTC).
        min_elevation_deg: Minimum elevation to count as visible.
        step_seconds: Scan resolution in seconds.

    Returns:
        List of OverpassWindow sorted by AOS.
    """
    try:
        sat = _parse_tle(satellite["tle_line1"], satellite["tle_line2"])
    except Exception:
        return []

    ts = load.timescale()
    topos = Topos(
        latitude_degrees=ground_station["latitude"],
        longitude_degrees=ground_station["longitude"],
        elevation_m=ground_station.get("altitude_m", 0),
    )

    start_time = _as_utc(start_time)
    end_time = _as_utc(end_time)
    current = start_time

    windows: list[OverpassWindow] = []
    in_window = False
    window_start: datetime | None = None
    max_el = 0.0
    sat_id = satellite.get("id", satellite.get("norad_id", ""))
    station_id = ground_station.get("id")
    observer_to_satellite = sat - topos

    while current < end_time:
        t = ts.from_datetime(current)
        try:
            altitude, _, _ = observer_to_satellite.at(t).altaz()
            elev_deg = float(altitude.degrees)
        except Exception:
            current += timedelta(seconds=step_seconds)
            continue

        if elev_deg >= min_elevation_deg:
            if not in_window:
                in_window = True
                window_start = current
                max_el = elev_deg
            else:
                max_el = max(max_el, elev_deg)
        else:
            if in_window and window_start:
                duration = (current - window_start).total_seconds()
                windows.append(
                    OverpassWindow(
                        aos=window_start,
                        los=current,
                        max_elevation_deg=round(max_el, 2),
                        duration_seconds=round(duration, 1),
                        satellite_id=sat_id,
                        ground_station_id=station_id,
                    )
                )
                in_window = False

        current += timedelta(seconds=step_seconds)

    # Close any open window at end of range
    if in_window and window_start:
        duration = (end_time - window_start).total_seconds()
        windows.append(
            OverpassWindow(
                aos=window_start,
                los=end_time,
                max_elevation_deg=round(max_el, 2),
                duration_seconds=round(duration, 1),
                satellite_id=sat_id,
                ground_station_id=station_id,
            )
        )

    return windows


def calculate_ground_track(
    satellite: dict,
    start_time: datetime,
    end_time: datetime,
    step_seconds: int = 60,
) -> list[GroundTrackPoint]:
    """Calculate satellite ground track over a time range.

    Returns a list of GroundTrackPoint with (timestamp, lat, lon, alt_km).
    """
    try:
        sat = _parse_tle(satellite["tle_line1"], satellite["tle_line2"])
    except Exception:
        return []

    ts = load.timescale()
    current = _as_utc(start_time)
    end = _as_utc(end_time)

    points: list[GroundTrackPoint] = []
    while current <= end:
        t = ts.from_datetime(current)
        try:
            sub = sat.at(t).subpoint()
            points.append(
                GroundTrackPoint(
                    timestamp=current,
                    latitude=round(float(sub.latitude.degrees), 6),
                    longitude=round(float(sub.longitude.degrees), 6),
                    altitude_km=round(float(sub.elevation.km), 3),
                )
            )
        except Exception:
            pass
        current += timedelta(seconds=step_seconds)

    return points
