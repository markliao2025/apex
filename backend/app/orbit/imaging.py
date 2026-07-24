"""Imaging window calculator — determines when a satellite can image a target area."""

import math
from datetime import datetime, timedelta, timezone

from skyfield.api import EarthSatellite as make_satellite, Topos, load as skyfield_load


def _as_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime and reject ambiguous naive inputs."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Imaging calculation timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _solar_zenith_angle(
    target_lat_deg: float, target_lon_deg: float, dt: datetime
) -> float:
    """Compute the solar zenith angle at (target_lat, target_lon) for a given datetime.

    Uses the NOAA solar declination/zenith approximation which does NOT require
    a full ephemeris download.
    Returns degrees.
    """
    # Day of year
    doy = dt.timetuple().tm_yday

    # Solar declination (approximate)
    declination_deg = -23.45 * math.cos(math.radians(360.0 / 365.0 * (doy + 10)))
    declination_rad = math.radians(declination_deg)

    # Hour angle (UTC): -180° at midnight, +180° at next midnight
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    hour_angle_deg = 15.0 * (hour - 12.0)
    hour_angle_rad = math.radians(hour_angle_deg)

    # Zenith angle
    lat_rad = math.radians(target_lat_deg)
    cos_zenith = math.sin(lat_rad) * math.sin(declination_rad) + math.cos(
        lat_rad
    ) * math.cos(declination_rad) * math.cos(hour_angle_rad)
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    return math.degrees(math.acos(cos_zenith))


def calculate_imaging_windows(
    satellite: dict,
    bbox: dict,
    start_time: datetime,
    end_time: datetime,
    min_elevation_deg: float = 5.0,
    max_sun_angle_deg: float = 60.0,
    step_seconds: int = 30,
) -> list[dict]:
    """Calculate imaging windows for a target bounding box.

    A satellite can image a target when:
    1. It passes over or near the target area with sufficient elevation
    2. The target is sunlit (solar zenith angle < max_sun_angle_deg)

    The detection radius is set to 5° (covers swath for most LEO satellites),
    then elevation is computed from the target centre.

    Returns a list of dicts with keys: aos, los, max_elevation_deg,
    illumination_pct, duration_seconds, satellite_id, target_bbox.
    """
    try:
        sat_obj = make_satellite(satellite["tle_line1"], satellite["tle_line2"])
    except Exception:
        return []

    ts = skyfield_load.timescale()

    # Target centre point
    center_lat = (bbox["sw_lat"] + bbox["ne_lat"]) / 2
    center_lon = (bbox["sw_lng"] + bbox["ne_lng"]) / 2

    # Detection radius: 5° is conservative — covers LEO swath widths
    target_radius_deg = 5.0

    start_time = _as_utc(start_time)
    end_time = _as_utc(end_time)
    current = start_time

    windows: list[dict] = []
    in_window = False
    window_start: datetime | None = None
    max_el = 0.0
    min_illum = 1.0
    sat_id = satellite.get("id", satellite.get("norad_id", ""))

    # Pre-build Topos for target centre
    target_topos = Topos(latitude_degrees=center_lat, longitude_degrees=center_lon)
    target_to_satellite = sat_obj - target_topos

    while current < end_time:
        t = ts.from_datetime(current)
        try:
            sat_at_t = sat_obj.at(t)
            sub = sat_at_t.subpoint()
            sat_lat = float(sub.latitude.degrees)
            sat_lon = float(sub.longitude.degrees)

            # Distance from target centre
            dist_deg = math.sqrt(
                (sat_lat - center_lat) ** 2 + (sat_lon - center_lon) ** 2
            )
            over_target = dist_deg < target_radius_deg

            # Elevation from target perspective
            if over_target:
                altitude, _, _ = target_to_satellite.at(t).altaz()
                elev_deg = float(altitude.degrees)
            else:
                elev_deg = 0.0

            # Illumination — solar zenith angle (NOAA approximation)
            sun_zenith_deg = _solar_zenith_angle(center_lat, center_lon, current)
            illumination = max(0.0, 1.0 - sun_zenith_deg / 90.0)

            if elev_deg >= min_elevation_deg and illumination > 0.1:
                if not in_window:
                    in_window = True
                    window_start = current
                    max_el = elev_deg
                    min_illum = illumination
                else:
                    max_el = max(max_el, elev_deg)
                    min_illum = min(min_illum, illumination)
            else:
                if in_window and window_start:
                    duration = (current - window_start).total_seconds()
                    windows.append(
                        {
                            "aos": window_start,
                            "los": current,
                            "max_elevation_deg": round(max_el, 2),
                            "illumination_pct": round(min_illum, 4),
                            "duration_seconds": round(duration, 1),
                            "satellite_id": sat_id,
                            "target_bbox": bbox,
                        }
                    )
                    in_window = False
        except Exception:
            pass

        current += timedelta(seconds=step_seconds)

    # Close any open window
    if in_window and window_start:
        duration = (end_time - window_start).total_seconds()
        windows.append(
            {
                "aos": window_start,
                "los": end_time,
                "max_elevation_deg": round(max_el, 2),
                "illumination_pct": round(min_illum, 4),
                "duration_seconds": round(duration, 1),
                "satellite_id": sat_id,
                "target_bbox": bbox,
            }
        )

    return windows
