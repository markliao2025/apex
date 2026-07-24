"""Seed deterministic demo satellite and ground-station data.

Network access is opt-in. The default path is reproducible and works offline.
"""

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models import GroundStation
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.orbit.tle import parse_tle_epoch

logger = logging.getLogger("apex.seed")


# Predefined satellite configurations — actual CelesTrak NORAD IDs for EO satellites
SATELLITE_CONFIGS: list[dict[str, Any]] = [
    {
        "norad_id": "40697",
        "name": "Sentinel-2A",
        "orbit_type": "sso",
        "altitude_km_min": 786.0,
        "altitude_km_max": 786.0,
        "inclination_deg": 98.6,
        "eccentricity": 0.0001,
        "payload_type": "eo_multispectral",
        "max_resolution_m": 10.0,
        "swath_width_km": 290.0,
        "max_storage_gb": 1000.0,
        "max_power_w": 2500.0,
    },
    {
        "norad_id": "49260",
        "name": "Landsat-9",
        "orbit_type": "sso",
        "altitude_km_min": 705.0,
        "altitude_km_max": 705.0,
        "inclination_deg": 98.2,
        "eccentricity": 0.0001,
        "payload_type": "eo_multispectral",
        "max_resolution_m": 15.0,
        "swath_width_km": 185.0,
        "max_storage_gb": 800.0,
        "max_power_w": 2200.0,
    },
]

# Synthetic demo TLE inputs with epochs on 2024 day 152. They are for
# deterministic software demonstration only, not operational flight use.
FALLBACK_TLES = {
    "40697": {
        "tle_line1": "1 40697U 15028A   24152.50000000 -.00000101  00000+0 -22011-4 0  9991",
        "tle_line2": "2 40697  98.5681 259.8867 0001208  96.3482 263.7838 14.30819553576175",
    },
    "49260": {
        "tle_line1": "1 49260U 21088A   24152.50000000  .00000410  00000+0  10118-3 0  9997",
        "tle_line2": "2 49260  98.2274 255.1296 0001161  88.7566 271.3765 14.57109297253471",
    },
}

GROUND_STATIONS = [
    {
        "name": "Tokyo",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "altitude_m": 40.0,
        "band": "x_band",
        "antenna_diameter_m": 12.0,
    },
    {
        "name": "Nairobi",
        "latitude": -1.2864,
        "longitude": 36.8172,
        "altitude_m": 1795.0,
        "band": "s_band",
        "antenna_diameter_m": 10.0,
    },
    {
        "name": "White Sands",
        "latitude": 32.3906,
        "longitude": -106.3956,
        "altitude_m": 1290.0,
        "band": "x_band",
        "antenna_diameter_m": 18.0,
    },
    {
        "name": "Svalbard",
        "latitude": 78.2297,
        "longitude": 15.3975,
        "altitude_m": 450.0,
        "band": "ku_band",
        "antenna_diameter_m": 14.0,
    },
]


def _fetch_tle_from_celestrak(http_client: httpx.Client) -> dict[str, tuple[str, str]]:
    """Fetch TLE data from CelesTrak GPQ for specific NORAD IDs."""
    # NORAD IDs we need
    norad_ids = ["40697", "37840", "40769", "49260"]
    tles: dict[str, tuple[str, str]] = {}

    for nid in norad_ids:
        try:
            url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={nid}&FORMAT=tle"
            response = http_client.get(url, timeout=5.0)
            response.raise_for_status()
            lines = response.text.strip().split("\n")
            if len(lines) >= 3:
                # Line 0 is the satellite name, line 1-2 are TLE
                line1 = lines[1].strip()
                line2 = lines[2].strip()
                if line1.startswith("1 ") and line2.startswith("2 "):
                    tles[nid] = (line1, line2)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "tle_fetch_failed norad_id=%s error=%s", nid, type(exc).__name__
            )

    return tles


def seed_satellites(
    db: Session, force: bool = False, allow_network: bool | None = None
) -> int:
    """Seed the database with predefined satellites and ground stations.

    Args:
        db: Active SQLAlchemy session.
        force: If True, delete existing satellite data before seeding.

    Returns:
        Number of satellites seeded/updated.
    """
    from app.models import Satellite as SatModel

    settings = get_settings()
    network_enabled = (
        settings.ALLOW_NETWORK_SEED if allow_network is None else allow_network
    )

    # Fetch fresh TLEs only after explicit opt-in.
    tles: dict[str, tuple[str, str]] = {}
    if network_enabled:
        try:
            with httpx.Client() as client:
                tles = _fetch_tle_from_celestrak(client)
        except httpx.HTTPError as exc:
            logger.warning("tle_catalog_unavailable error=%s", type(exc).__name__)

    # Populate fallback TLEs for any missing NORAD IDs
    for cfg in SATELLITE_CONFIGS:
        nid = str(cfg["norad_id"])
        if nid and nid not in tles and nid in FALLBACK_TLES:
            ft = FALLBACK_TLES[nid]
            tles[nid] = (ft["tle_line1"], ft["tle_line2"])

    count = 0

    for cfg in SATELLITE_CONFIGS:
        norad_id = str(cfg["norad_id"])
        tle_pair = tles.get(norad_id)

        if not tle_pair:
            continue

        existing = db.query(SatModel).filter(SatModel.norad_id == norad_id).first()
        if existing and not force:
            continue

        tle_line1, tle_line2 = tle_pair

        sat_data = {
            "norad_id": str(norad_id),
            "name": cfg["name"],
            "tle_line1": tle_line1,
            "tle_line2": tle_line2,
            "tle_epoch": parse_tle_epoch(tle_line1),
            "orbit_type": cfg["orbit_type"],
            "altitude_km_min": cfg["altitude_km_min"],
            "altitude_km_max": cfg["altitude_km_max"],
            "inclination_deg": cfg["inclination_deg"],
            "eccentricity": cfg["eccentricity"],
            "payload_type": cfg["payload_type"],
            "max_resolution_m": cfg["max_resolution_m"],
            "swath_width_km": cfg["swath_width_km"],
            "max_storage_gb": cfg["max_storage_gb"],
            "max_power_w": cfg["max_power_w"],
        }

        if existing:
            for k, v in sat_data.items():
                setattr(existing, k, v)
            count += 1
        else:
            db.add(SatModel(**sat_data))
            count += 1

    # Seed ground stations (idempotent by name)
    for gs_cfg in GROUND_STATIONS:
        existing = (
            db.query(GroundStation).filter(GroundStation.name == gs_cfg["name"]).first()
        )
        if not existing:
            db.add(GroundStation(**gs_cfg))

    db.commit()
    return count


def main() -> None:
    """CLI entry-point for seeding."""
    db = SessionLocal()
    try:
        count = seed_satellites(db, force=True)
        print(f"Seeded {count} satellites and {len(GROUND_STATIONS)} ground stations.")
    except Exception:
        db.rollback()
        logger.exception("seed_failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
