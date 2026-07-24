"""Geocoding — maps natural-language region descriptions to bounding boxes.

Three-tier lookup:
  1. Exact match on normalised region name
  2. Fuzzy match (Jaccard token similarity ≥ 0.6)
  3. LLM fallback — calls OpenAI to extract bbox coordinates

REGION_BBOX: dict[str, tuple(sw_lat, sw_lng, ne_lat, ne_lng)]
All coordinates in WGS84 decimal degrees.
"""

from __future__ import annotations

import math
import re
import os
from typing import Optional

# ── Region Bounding Box Dictionary ─────────────────────────────────────────────
# Format: name_lower -> (sw_lat, sw_lng, ne_lat, ne_lng)

REGION_BBOX: dict[str, tuple[float, float, float, float]] = {
    # ── Major World Cities ────────────────────────────────────────────────────
    "new york": (40.48, -74.26, 40.92, -73.70),
    "los angeles": (33.70, -118.67, 34.34, -117.65),
    "san francisco": (37.70, -122.52, 37.82, -122.36),
    "chicago": (41.65, -87.92, 42.02, -87.52),
    "houston": (29.52, -95.80, 30.15, -94.99),
    "phoenix": (33.29, -112.35, 33.72, -111.92),
    "philadelphia": (39.87, -75.28, 40.14, -74.96),
    "san antonio": (29.22, -98.73, 29.58, -98.34),
    "san diego": (32.53, -117.31, 33.11, -116.90),
    "dallas": (32.60, -97.00, 32.95, -96.50),
    "austin": (30.10, -97.97, 30.52, -97.50),
    "seattle": (47.49, -122.45, 47.74, -122.24),
    "denver": (39.61, -105.11, 39.92, -104.76),
    "boston": (42.23, -71.20, 42.54, -70.85),
    "miami": (25.70, -80.45, 25.90, -80.12),
    "atlanta": (33.60, -84.55, 33.90, -84.23),
    "las vegas": (36.08, -115.42, 36.32, -115.00),
    "portland": (45.40, -122.84, 45.65, -122.50),
    "detroit": (42.20, -83.30, 42.50, -82.80),
    "minneapolis": (44.88, -93.45, 45.10, -93.05),
    "toronto": (43.58, -79.72, 43.85, -79.12),
    "vancouver": (49.19, -123.27, 49.40, -122.80),
    "montreal": (45.40, -73.79, 45.70, -73.47),
    "mexico city": (19.25, -99.35, 19.60, -98.95),
    "guadalajara": (20.50, -103.50, 20.80, -103.10),
    # Europe
    "london": (51.28, -0.49, 51.69, 0.34),
    "paris": (48.67, 2.25, 48.99, 2.47),
    "berlin": (52.34, 13.09, 52.67, 13.76),
    "madrid": (40.20, -3.94, 40.54, -3.52),
    "rome": (41.79, 12.35, 41.96, 12.60),
    "milan": (45.35, 9.10, 45.55, 9.35),
    "amsterdam": (52.27, 4.70, 52.45, 5.05),
    "vienna": (48.12, 16.20, 48.32, 16.60),
    "prague": (49.97, 14.20, 50.17, 14.75),
    "budapest": (47.35, 18.90, 47.60, 19.30),
    "warsaw": (52.05, 20.85, 52.40, 21.25),
    "barcelona": (41.27, 2.05, 41.47, 2.25),
    "munich": (48.08, 11.33, 48.25, 11.73),
    "zurich": (47.28, 8.48, 47.44, 8.63),
    "lisbon": (38.65, -9.23, 38.85, -9.00),
    "dublin": (53.25, -6.45, 53.40, -6.10),
    "stockholm": (59.25, 17.70, 59.45, 18.25),
    "oslo": (59.80, 10.55, 59.95, 10.90),
    "copenhagen": (55.60, 12.45, 55.75, 12.75),
    "helsinki": (60.10, 24.75, 60.25, 25.10),
    "athens": (37.85, 23.60, 38.00, 23.90),
    "brussels": (50.75, 4.20, 50.95, 4.50),
    "moscow": (55.50, 37.30, 55.90, 37.90),
    "st petersburg": (59.75, 30.05, 60.05, 30.55),
    # Asia
    "tokyo": (35.52, 139.45, 35.82, 139.92),
    "tokyo bay": (35.30, 139.50, 35.70, 140.00),
    "shanghai": (31.10, 121.25, 31.40, 121.75),
    "beijing": (39.65, 116.05, 40.15, 116.75),
    "hong kong": (22.20, 113.85, 22.60, 114.40),
    "seoul": (37.42, 126.68, 37.70, 127.20),
    "bangkok": (13.55, 100.30, 13.95, 100.80),
    "mumbai": (18.80, 72.75, 19.30, 73.15),
    "delhi": (28.40, 76.85, 28.90, 77.40),
    "bangalore": (12.75, 77.40, 13.15, 77.80),
    "kolkata": (22.45, 88.25, 22.80, 88.55),
    "jakarta": (-6.35, 106.65, -6.05, 107.00),
    "manila": (14.45, 120.85, 14.75, 121.05),
    "kuala lumpur": (3.05, 101.60, 3.25, 101.85),
    "ho chi minh city": (10.70, 106.55, 10.95, 106.85),
    "hanoi": (20.85, 105.65, 21.10, 105.95),
    "taipei": (24.95, 121.45, 25.20, 121.70),
    "osaka": (34.55, 135.35, 34.80, 135.65),
    "kyoto": (34.95, 135.60, 35.10, 135.85),
    "nagoya": (35.00, 136.70, 35.30, 137.05),
    "shenzhen": (22.40, 113.75, 22.80, 114.40),
    "guangzhou": (22.95, 113.10, 23.45, 113.65),
    "chengdu": (30.50, 104.00, 30.85, 104.40),
    "tianjin": (38.90, 117.00, 39.30, 117.60),
    "wuhan": (30.35, 114.00, 30.75, 114.50),
    "xian": (34.10, 108.80, 34.50, 109.30),
    "hangzhou": (30.05, 120.00, 30.40, 120.30),
    "nanjing": (31.90, 118.70, 32.15, 119.10),
    "pune": (18.40, 73.70, 18.70, 74.05),
    "hyderabad": (17.20, 78.30, 17.60, 78.70),
    "chennai": (12.90, 80.10, 13.25, 80.40),
    "kathmandu": (27.60, 85.20, 27.80, 85.45),
    "dhaka": (23.65, 90.25, 23.95, 90.55),
    "colombo": (6.85, 79.80, 7.05, 79.95),
    "yangon": (16.75, 96.05, 17.00, 96.30),
    "phnom penh": (11.45, 104.80, 11.65, 105.05),
    "vientiane": (17.90, 102.55, 18.10, 102.75),
    "ulaanbaatar": (47.80, 106.80, 48.00, 107.10),
    # Middle East
    "dubai": (24.98, 55.00, 25.35, 55.50),
    "abu dhabi": (24.28, 54.10, 24.70, 54.75),
    "doha": (25.20, 51.35, 25.40, 51.60),
    "riyadh": (24.45, 46.45, 24.85, 46.90),
    "jeddah": (21.40, 39.05, 21.75, 39.40),
    "tehran": (35.55, 51.20, 35.90, 51.70),
    "baghdad": (33.25, 44.20, 33.55, 44.65),
    "istanbul": (40.80, 28.65, 41.20, 29.35),
    "tel aviv": (32.00, 34.70, 32.15, 35.00),
    "jerusalem": (31.65, 35.00, 31.90, 35.35),
    # Africa
    "cairo": (30.00, 31.05, 30.25, 31.55),
    "johannesburg": (-26.35, 27.80, -26.00, 28.35),
    "cape town": (-34.05, 18.30, -33.70, 18.80),
    "nairobi": (-1.45, 36.65, -1.15, 37.05),
    "lagos": (6.35, 3.20, 6.60, 3.60),
    "addis ababa": (8.85, 38.65, 9.15, 39.05),
    "accra": (5.45, -0.35, 5.75, 0.00),
    "dakar": (14.60, -17.55, 14.80, -17.30),
    "casablanca": (33.50, -7.65, 33.65, -7.40),
    "kinshasa": (-4.50, 15.15, -4.20, 15.50),
    "dar es salaam": (-6.95, 39.15, -6.70, 39.50),
    "tunis": (36.70, 10.05, 36.95, 10.35),
    "algiers": (36.60, 3.00, 36.90, 3.35),
    "khartoum": (15.45, 32.30, 15.75, 32.75),
    # South / Central America
    "sao paulo": (-23.70, -46.83, -23.30, -46.30),
    "rio de janeiro": (-23.08, -43.70, -22.70, -43.10),
    "brasilia": (-15.90, -48.20, -15.55, -47.70),
    "buenos aires": (-34.70, -58.53, -34.45, -58.15),
    "santiago": (-33.60, -70.80, -33.20, -70.40),
    "lima": (-12.30, -77.20, -12.00, -76.80),
    "bogota": (4.45, -74.20, 4.85, -73.90),
    "caracas": (10.30, -67.15, 10.60, -66.70),
    "medellin": (6.10, -75.65, 6.45, -75.35),
    "guayaquil": (-2.35, -79.95, -2.05, -79.75),
    "montevideo": (-34.95, -56.35, -34.70, -56.00),
    "asuncion": (-25.40, -57.75, -25.10, -57.45),
    # Oceania
    "sydney": (-34.00, 150.70, -33.70, 151.35),
    "melbourne": (-38.00, 144.60, -37.60, 145.20),
    "brisbane": (-27.60, 152.80, -27.30, 153.30),
    "perth": (-32.15, 115.65, -31.75, 116.15),
    "auckland": (-37.00, 174.50, -36.70, 175.00),
    "wellington": (-41.35, 174.70, -41.10, 175.00),
    # ── Countries ─────────────────────────────────────────────────────────────
    "united states": (24.00, -125.00, 50.00, -66.00),
    "usa": (24.00, -125.00, 50.00, -66.00),
    "united kingdom": (49.60, -8.70, 60.90, 1.90),
    "uk": (49.60, -8.70, 60.90, 1.90),
    "france": (41.30, -5.10, 51.20, 9.70),
    "germany": (47.20, 5.80, 55.10, 15.10),
    "italy": (35.30, 6.60, 47.10, 18.70),
    "spain": (36.00, -9.30, 43.80, 3.30),
    "japan": (24.30, 122.90, 45.60, 153.90),
    "china": (18.00, 73.50, 53.60, 135.00),
    "india": (6.50, 68.00, 35.50, 97.50),
    "australia": (-44.00, 112.50, -10.00, 154.00),
    "brazil": (-34.00, -74.00, 5.50, -32.00),
    "canada": (41.50, -141.00, 83.50, -52.00),
    "russia": (41.00, 19.50, 82.00, 180.00),
    "south korea": (33.00, 124.50, 38.70, 131.00),
    "mexico": (14.50, -118.50, 32.50, -86.50),
    "indonesia": (-11.00, 95.00, 6.00, 141.00),
    "thailand": (5.50, 97.30, 20.50, 105.70),
    "vietnam": (8.30, 102.00, 23.50, 110.00),
    "philippines": (4.50, 116.00, 21.50, 127.00),
    "malaysia": (0.80, 99.50, 7.50, 119.50),
    "singapore": (1.20, 103.60, 1.50, 104.10),
    "pakistan": (23.50, 60.50, 37.00, 77.00),
    "bangladesh": (20.50, 88.00, 26.60, 92.70),
    "egypt": (22.00, 24.50, 32.00, 37.00),
    "nigeria": (4.00, 3.00, 14.00, 14.00),
    "south africa": (-35.00, 16.50, -22.00, 33.00),
    "kenya": (-5.00, 33.50, 5.50, 42.00),
    "ethiopia": (3.50, 33.00, 15.00, 48.00),
    "morocco": (27.50, -13.50, 36.50, -1.00),
    "argentina": (-55.00, -74.00, -21.00, -53.50),
    "chile": (-55.50, -75.50, -17.30, -66.00),
    "colombia": (-4.50, -79.00, 13.00, -66.50),
    "peru": (-18.50, -81.50, -0.50, -68.50),
    "venezuela": (0.50, -73.50, 12.50, -59.50),
    "greece": (35.00, 19.20, 41.50, 29.50),
    "turkey": (35.50, 25.50, 42.50, 45.00),
    "saudi arabia": (16.00, 34.50, 32.50, 55.50),
    "iran": (25.00, 44.00, 40.00, 63.50),
    "iraq": (29.00, 38.50, 37.50, 49.00),
    "israel": (29.40, 34.20, 33.30, 35.90),
    "ukraine": (44.00, 22.00, 52.50, 40.50),
    "poland": (49.00, 14.00, 54.50, 24.50),
    "netherlands": (50.50, 3.30, 53.60, 7.50),
    "belgium": (49.40, 2.30, 51.50, 6.50),
    "sweden": (55.00, 10.50, 69.00, 24.50),
    "norway": (58.00, 4.50, 71.00, 31.50),
    "finland": (59.50, 20.00, 70.00, 31.50),
    "denmark": (54.50, 7.50, 58.00, 15.50),
    "austria": (46.30, 9.30, 49.00, 17.20),
    "switzerland": (45.70, 5.80, 47.80, 10.50),
    "portugal": (36.80, -9.50, 42.20, -6.00),
    "ireland": (51.20, -10.50, 55.60, -5.90),
    "czech republic": (48.50, 12.00, 51.00, 18.90),
    "romania": (43.50, 20.00, 48.50, 30.30),
    "hungary": (45.50, 16.00, 48.50, 22.50),
    # ── Geographic Regions & Landmarks ──────────────────────────────────────
    "southeast asia": (-10.00, 95.00, 28.00, 130.00),
    "east asia": (18.00, 100.00, 50.00, 150.00),
    "south asia": (5.00, 60.00, 38.00, 100.00),
    "central asia": (35.00, 45.00, 55.00, 80.00),
    "indo-pacific": (-45.00, 70.00, 45.00, 180.00),
    "pacific ocean": (-90.00, -180.00, 90.00, 180.00),
    "western pacific": (-10.00, 100.00, 60.00, 180.00),
    "south china sea": (0.00, 105.00, 25.00, 122.00),
    "east china sea": (20.00, 120.00, 35.00, 130.00),
    "sea of japan": (33.00, 127.00, 52.00, 143.00),
    "yellow sea": (30.00, 118.00, 42.00, 126.00),
    "philippine sea": (0.00, 120.00, 40.00, 160.00),
    "san francisco bay": (37.20, -122.60, 38.00, -121.70),
    "chesapeake bay": (37.50, -77.50, 39.50, -75.50),
    "gulf of mexico": (18.00, -98.00, 30.50, -80.00),
    "persian gulf": (23.00, 48.00, 31.00, 57.00),
    "red sea": (12.00, 32.00, 28.50, 45.00),
    "mediterranean sea": (30.00, -5.50, 46.00, 36.00),
    "north sea": (50.00, -4.00, 62.00, 9.00),
    "baltic sea": (53.00, 9.00, 66.00, 30.50),
    "himalayas": (26.00, 72.00, 37.00, 98.00),
    "alps": (43.00, 5.00, 47.00, 15.00),
    "rocky mountains": (31.00, -123.00, 60.00, -95.00),
    "andes": (-55.00, -77.00, 12.00, -66.00),
    "carpathian mountains": (44.00, 13.00, 52.00, 30.00),
    "caucasus": (38.00, 38.00, 45.00, 51.00),
    "tian shan": (36.00, 66.00, 46.00, 88.00),
    "kunlun mountains": (32.00, 74.00, 40.00, 90.00),
    "amazon river": (-10.00, -75.00, 5.00, -48.00),
    "nile river": (1.00, 25.00, 35.00, 38.00),
    "yangtze river": (24.00, 105.00, 36.00, 122.00),
    "yellow river": (32.00, 95.00, 42.00, 123.00),
    "mississippi river": (29.00, -105.00, 48.00, -82.00),
    "ganges river": (21.00, 73.00, 32.00, 89.00),
    "mekong river": (10.00, 100.00, 30.00, 107.00),
    "congo river": (-13.00, 12.00, 5.00, 30.00),
    "danube river": (42.00, 8.00, 49.00, 30.00),
    "indus river": (24.00, 60.00, 37.00, 78.00),
    "sahara desert": (15.00, -17.00, 30.00, 30.00),
    "gobi desert": (37.00, 88.00, 50.00, 120.00),
    "arabian desert": (12.00, 35.00, 32.00, 60.00),
    "atacama desert": (-30.00, -71.50, -18.00, -68.50),
    "thar desert": (22.00, 68.00, 29.00, 76.00),
    "kalahari desert": (-28.00, 19.00, -18.00, 25.00),
    "amazon rainforest": (-20.00, -75.00, 5.00, -44.00),
    "congo rainforest": (-10.00, 10.00, 5.00, 30.00),
    "borneo rainforest": (-4.00, 108.50, 7.50, 119.50),
    "southeast asian rainforest": (-12.00, 95.00, 22.00, 130.00),
    "siberia": (50.00, 60.00, 75.00, 180.00),
    "taiga": (55.00, 50.00, 70.00, 150.00),
    "hawaii": (18.50, -160.50, 22.50, -154.50),
    "guam": (13.10, 144.50, 13.70, 145.30),
    "iceland": (63.00, -25.00, 66.50, -12.50),
    "madagascar": (-25.80, 43.00, -11.50, 50.60),
    "new zealand": (-47.00, 166.00, -34.00, 179.00),
    "sri lanka": (5.70, 79.50, 9.90, 82.10),
    "taiwan": (21.50, 119.00, 25.50, 122.50),
    "sicily": (37.50, 11.80, 38.50, 15.70),
    "sardinia": (38.80, 8.00, 41.50, 10.50),
    "corsica": (41.30, 8.40, 43.10, 9.80),
    "pacific ring of fire": (-60.00, 100.00, 60.00, -70.00),
    "typhoon alley": (0.00, 105.00, 40.00, 145.00),
    "caribbean hurricane zone": (10.00, -100.00, 30.00, -60.00),
    "sahel region": (10.00, -5.00, 20.00, 40.00),
    "horn of africa": (-5.00, 38.00, 18.00, 52.00),
    "bay of bengal": (5.00, 80.00, 23.00, 100.00),
    "arabian sea": (0.00, 55.00, 25.00, 78.00),
    "arctic": (66.50, -180.00, 90.00, 180.00),
    "antarctica": (-90.00, -180.00, -60.00, 180.00),
    "greenland": (59.50, -75.00, 84.00, -10.00),
    "gaza strip": (31.20, 34.15, 31.60, 34.60),
    "syria": (32.00, 35.50, 37.50, 42.50),
    "myanmar": (9.50, 92.00, 28.50, 101.50),
    "south sudan": (3.00, 23.50, 13.00, 36.00),
    "suez canal": (29.80, 32.30, 32.60, 33.90),
    "panama canal": (8.50, -80.50, 9.70, -79.30),
    "straits of malacca": (0.50, 95.00, 7.00, 105.00),
    "english channel": (49.50, -5.50, 51.00, 2.50),
    "california coast": (32.00, -124.50, 42.00, -114.00),
    "east coast usa": (24.00, -82.00, 45.00, -65.00),
    "northeast usa": (38.00, -80.00, 47.00, -65.00),
    "east coast china": (18.00, 108.00, 42.00, 125.00),
    "bermuda triangle": (18.00, -80.00, 28.00, -60.00),
    "great barrier reef": (-25.00, 145.00, -10.00, 155.00),
    "galapagos islands": (-1.80, -92.00, 1.70, -88.50),
    "great wall of china": (37.00, 112.00, 41.00, 125.00),
    "pyramids of giza": (29.85, 31.00, 30.15, 31.40),
    "machu picchu": (-13.50, -72.70, -13.00, -72.30),
    "midwest usa": (36.00, -105.00, 49.00, -80.00),
    "pampas region": (-35.00, -63.00, -28.00, -53.00),
    "indo-gangetic plain": (22.00, 73.00, 32.00, 90.00),
    "northeast china plain": (30.00, 110.00, 45.00, 125.00),
    "alaska": (51.00, -180.00, 72.00, -128.00),
    "svalbard": (76.00, 14.00, 81.00, 33.00),
    "demo area": (35.50, 139.50, 35.80, 139.90),
    "demo tokyo": (35.50, 139.50, 35.80, 139.90),
    "demo bay area": (37.30, -122.50, 37.90, -121.80),
}


# ── Fuzzy Matching ────────────────────────────────────────────────────────────


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation, split into word tokens."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return set(text.split())


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity coefficient between two token sets."""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


def _levenshtein_ratio(s: str, t: str) -> float:
    """Normalized Levenshtein similarity (0–1)."""
    if not s and not t:
        return 1.0
    if not s or not t:
        return 0.0
    len_s, len_t = len(s), len(t)
    if len_s > len_t:
        s, t = t, s
        len_s, len_t = len_t, len_s
    # Two rows algorithm
    prev = list(range(len_s + 1))
    curr = [0] * (len_s + 1)
    for i in range(1, len_t + 1):
        curr[0] = i
        for j in range(1, len_s + 1):
            cost = 0 if t[i - 1] == s[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev
    max_len = max(len_s, len_t)
    return 1.0 - prev[len_s] / max_len


def _fuzzy_match(query: str, threshold: float = 0.55) -> Optional[str]:
    """Find best matching region key using Jaccard + Levenshtein combo."""
    query_tokens = _tokenize(query)
    best_key: str | None = None
    best_score = 0.0

    for key in REGION_BBOX:
        key_tokens = _tokenize(key)
        jaccard = _jaccard(query_tokens, key_tokens)
        lev = _levenshtein_ratio(query.lower(), key)
        # Combined: Jaccard for multi-word queries, Levenshtein for single-word
        score = 0.6 * jaccard + 0.4 * lev

        if score > best_score and score >= threshold:
            best_score = score
            best_key = key

    return best_key


# ── LLM Fallback ─────────────────────────────────────────────────────────────


def _call_llm_geocode(region_description: str) -> Optional[dict]:
    """Call OpenAI to extract bounding box coordinates from a region description."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your-openai-api-key-here":
        return None

    try:
        import openai
        import json

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=256,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a geographic bounding-box extractor. "
                        "Given a region description, return a JSON object with fields: "
                        "sw_lat, sw_lng, ne_lat, ne_lng (all decimal degrees, WGS84). "
                        "Return null if the region is unrecognisable. "
                        "Output ONLY the JSON, no markdown, no explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"What is the approximate bounding box for: {region_description}",
                },
            ],
        )
        text = response.choices[0].message.content.strip()
        data = json.loads(text)
        if data is None:
            return None
        return {
            "sw_lat": float(data["sw_lat"]),
            "sw_lng": float(data["sw_lng"]),
            "ne_lat": float(data["ne_lat"]),
            "ne_lng": float(data["ne_lng"]),
        }
    except Exception:
        return None


# ── BBox Dataclass ─────────────────────────────────────────────────────────────


class BBox:
    """A bounding box with WGS84 coordinates."""

    __slots__ = ("sw_lat", "sw_lng", "ne_lat", "ne_lng")

    def __init__(
        self,
        sw_lat: float,
        sw_lng: float,
        ne_lat: float,
        ne_lng: float,
    ) -> None:
        self.sw_lat = sw_lat
        self.sw_lng = sw_lng
        self.ne_lat = ne_lat
        self.ne_lng = ne_lng

    def __repr__(self) -> str:
        return (
            f"BBox(sw=({self.sw_lat:.4f},{self.sw_lng:.4f}) "
            f"ne=({self.ne_lat:.4f},{self.ne_lng:.4f}))"
        )

    def to_dict(self) -> dict:
        return {
            "sw_lat": self.sw_lat,
            "sw_lng": self.sw_lng,
            "ne_lat": self.ne_lat,
            "ne_lng": self.ne_lng,
        }

    @property
    def center_lat(self) -> float:
        return (self.sw_lat + self.ne_lat) / 2

    @property
    def center_lng(self) -> float:
        return (self.sw_lng + self.ne_lng) / 2

    def area_km2(self) -> float:
        """Approximate area in km² (very rough)."""
        lat_span = abs(self.ne_lat - self.sw_lat) * 111.0
        avg_lat_rad = math.radians((self.sw_lat + self.ne_lat) / 2)
        lon_span = abs(self.ne_lng - self.sw_lng) * 111.32 * math.cos(avg_lat_rad)
        return lat_span * lon_span


# ── Public API ────────────────────────────────────────────────────────────────


def geocode_region(region_description: str) -> Optional[BBox]:
    """Convert a region description string to a bounding box.

    Three-tier strategy:
      1. Exact match on normalised key in REGION_BBOX
      2. Fuzzy match (Jaccard + Levenshtein, score ≥ 0.55)
      3. LLM fallback via OpenAI GPT-4o-mini

    Returns None if all strategies fail.
    """
    if not region_description or not region_description.strip():
        return None

    query = region_description.strip().lower()

    # ── Tier 1: Exact match ──────────────────────────────────────────────────
    if query in REGION_BBOX:
        sw_lat, sw_lng, ne_lat, ne_lng = REGION_BBOX[query]
        return BBox(sw_lat, sw_lng, ne_lat, ne_lng)

    # ── Tier 2: Fuzzy match ──────────────────────────────────────────────────
    matched_key = _fuzzy_match(query, threshold=0.55)
    if matched_key:
        sw_lat, sw_lng, ne_lat, ne_lng = REGION_BBOX[matched_key]
        return BBox(sw_lat, sw_lng, ne_lat, ne_lng)

    # ── Tier 3: LLM fallback ──────────────────────────────────────────────────
    result = _call_llm_geocode(region_description)
    if result:
        return BBox(
            sw_lat=result["sw_lat"],
            sw_lng=result["sw_lng"],
            ne_lat=result["ne_lat"],
            ne_lng=result["ne_lng"],
        )

    return None
