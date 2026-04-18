"""Synthetic Devon/Torbay/Plymouth traffic data generator.

Approximates what a GPS/mobile-probe dataset looks like:
- Zones: Devon towns with lat/lon centroids
- OD (origin-destination) trip counts by hour-of-day and day-of-week
- Speed profiles on key road links (A38, A30, A380, M5, ...)
- Journey time distributions between town pairs
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Geography — 18 Devon zones including Torbay + Plymouth
# ---------------------------------------------------------------------------
ZONES: dict[str, tuple[float, float, int]] = {
    # name: (lat, lon, approximate_population)
    "Plymouth":      (50.3755, -4.1427, 264695),
    "Torquay":       (50.4619, -3.5253,  65245),
    "Paignton":      (50.4368, -3.5639,  49021),
    "Brixham":       (50.3934, -3.5151,  16693),
    "Exeter":        (50.7184, -3.5339, 130428),
    "Exmouth":       (50.6194, -3.4150,  34432),
    "Newton Abbot":  (50.5292, -3.6108,  26045),
    "Barnstaple":    (51.0805, -4.0600,  24932),
    "Tiverton":      (50.9018, -3.4898,  19544),
    "Bideford":      (51.0168, -4.2080,  17106),
    "Okehampton":    (50.7394, -4.0003,   7647),
    "Totnes":        (50.4313, -3.6850,   8076),
    "Teignmouth":    (50.5465, -3.4981,  15229),
    "Dawlish":       (50.5811, -3.4636,  13355),
    "Ivybridge":     (50.3911, -3.9206,  12056),
    "Tavistock":     (50.5478, -4.1430,  13028),
    "Ilfracombe":    (51.2089, -4.1134,  11184),
    "Sidmouth":      (50.6810, -3.2388,  12569),
}

TORBAY = {"Torquay", "Paignton", "Brixham"}
PLYMOUTH_AREA = {"Plymouth", "Ivybridge", "Tavistock"}


# Key road corridors as (road_name, from_zone, to_zone, free_flow_mph, length_miles)
CORRIDORS: list[tuple[str, str, str, int, float]] = [
    ("M5",   "Exeter",      "Tiverton",   70, 14.5),
    ("A38",  "Exeter",      "Plymouth",   70, 43.0),
    ("A38",  "Plymouth",    "Ivybridge",  70,  9.8),
    ("A30",  "Exeter",      "Okehampton", 70, 24.0),
    ("A380", "Exeter",      "Newton Abbot", 60, 13.5),
    ("A380", "Newton Abbot", "Torquay",   50,  5.5),
    ("A379", "Torquay",     "Paignton",   30,  3.2),
    ("A386", "Plymouth",    "Tavistock",  50, 14.1),
    ("A361", "Tiverton",    "Barnstaple", 55, 33.0),
    ("A39",  "Barnstaple",  "Bideford",   50,  8.9),
    ("A377", "Exeter",      "Barnstaple", 50, 38.6),
    ("A376", "Exeter",      "Exmouth",    40,  9.7),
]


# ---------------------------------------------------------------------------
# Core generators
# ---------------------------------------------------------------------------
@dataclass
class SynthConfig:
    seed: int = 42
    days: int = 14
    start: datetime = datetime(2026, 4, 1)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _haversine_miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = np.radians(a)
    lat2, lon2 = np.radians(b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(3958.8 * 2 * np.arcsin(np.sqrt(h)))


def build_zones_df() -> pd.DataFrame:
    rows = []
    for name, (lat, lon, pop) in ZONES.items():
        region = (
            "Torbay" if name in TORBAY
            else "Plymouth" if name in PLYMOUTH_AREA
            else "Devon"
        )
        rows.append({"zone": name, "lat": lat, "lon": lon, "population": pop, "region": region})
    return pd.DataFrame(rows)


def build_od_matrix(cfg: SynthConfig = SynthConfig()) -> pd.DataFrame:
    """Daily aggregate origin-destination trip counts (gravity model + noise)."""
    rng = _rng(cfg.seed)
    zones = build_zones_df()
    rows = []
    for _, o in zones.iterrows():
        for _, d in zones.iterrows():
            if o.zone == d.zone:
                continue
            dist = _haversine_miles((o.lat, o.lon), (d.lat, d.lon))
            # gravity: (pop_o * pop_d) / distance^1.6, scaled
            base = (o.population * d.population) / (dist ** 1.6 + 1)
            trips = base / 1e6
            # intra-Torbay and intra-Plymouth get a boost
            if o.region == d.region and o.region != "Devon":
                trips *= 2.5
            trips *= rng.uniform(0.8, 1.2)
            rows.append({
                "origin": o.zone,
                "destination": d.zone,
                "trips_per_day": int(max(1, trips)),
                "distance_miles": round(dist, 1),
            })
    return pd.DataFrame(rows)


def build_journey_times(cfg: SynthConfig = SynthConfig()) -> pd.DataFrame:
    """Per-trip journey time observations between selected common pairs."""
    rng = _rng(cfg.seed + 1)
    pairs = [
        ("Plymouth", "Exeter"),
        ("Exeter", "Torquay"),
        ("Plymouth", "Torquay"),
        ("Exeter", "Barnstaple"),
        ("Exeter", "Tiverton"),
        ("Torquay", "Paignton"),
        ("Plymouth", "Tavistock"),
        ("Exeter", "Exmouth"),
    ]
    zones = build_zones_df().set_index("zone")
    rows = []
    for o, d in pairs:
        a = (zones.loc[o].lat, zones.loc[o].lon)
        b = (zones.loc[d].lat, zones.loc[d].lon)
        miles = _haversine_miles(a, b)
        free_flow_min = miles / 55 * 60  # 55 mph assumed free-flow avg
        for hour in range(24):
            # rush-hour congestion factor
            if hour in (7, 8, 17, 18):
                cong = rng.uniform(1.4, 1.9)
            elif hour in (6, 9, 16, 19):
                cong = rng.uniform(1.15, 1.35)
            elif 22 <= hour or hour <= 5:
                cong = rng.uniform(0.9, 1.0)
            else:
                cong = rng.uniform(1.0, 1.15)
            # draw 120 observations per hour per pair
            n = 120
            mean = free_flow_min * cong
            obs = rng.normal(mean, mean * 0.08, size=n).clip(min=free_flow_min * 0.9)
            for t in obs:
                rows.append({
                    "origin": o,
                    "destination": d,
                    "hour": hour,
                    "journey_time_min": round(float(t), 2),
                    "distance_miles": round(miles, 1),
                })
    return pd.DataFrame(rows)


def build_speed_timeseries(cfg: SynthConfig = SynthConfig()) -> pd.DataFrame:
    """Hourly mean speeds on each corridor across `cfg.days` days."""
    rng = _rng(cfg.seed + 2)
    rows = []
    hours = cfg.days * 24
    for road, frm, to, free_flow, miles in CORRIDORS:
        link = f"{road}: {frm}→{to}"
        for i in range(hours):
            ts = cfg.start + timedelta(hours=i)
            hour = ts.hour
            dow = ts.weekday()
            # rush-hour reductions, weekends milder
            if dow < 5 and hour in (7, 8, 17, 18):
                factor = rng.uniform(0.45, 0.70)
            elif dow < 5 and hour in (6, 9, 16, 19):
                factor = rng.uniform(0.75, 0.90)
            elif dow >= 5 and 10 <= hour <= 18:
                factor = rng.uniform(0.80, 0.95)
            elif 22 <= hour or hour <= 5:
                factor = rng.uniform(0.95, 1.02)
            else:
                factor = rng.uniform(0.88, 1.00)
            mean_speed = free_flow * factor + rng.normal(0, 1.5)
            rows.append({
                "timestamp": ts,
                "road": road,
                "link": link,
                "from_zone": frm,
                "to_zone": to,
                "mean_speed_mph": round(float(mean_speed), 1),
                "free_flow_mph": free_flow,
                "length_miles": miles,
            })
    return pd.DataFrame(rows)


def build_gps_pings(cfg: SynthConfig = SynthConfig(), n: int = 5000) -> pd.DataFrame:
    """Scatter of synthetic GPS pings around zone centroids weighted by population."""
    rng = _rng(cfg.seed + 3)
    zones = build_zones_df()
    weights = zones.population / zones.population.sum()
    idx = rng.choice(len(zones), size=n, p=weights)
    rows = []
    for i in idx:
        z = zones.iloc[i]
        rows.append({
            "zone": z.zone,
            "region": z.region,
            "lat": z.lat + rng.normal(0, 0.03),
            "lon": z.lon + rng.normal(0, 0.04),
            "speed_mph": float(min(75.0, max(0.0, rng.gamma(3, 7)))),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Cached bundle
# ---------------------------------------------------------------------------
_CACHE: dict = {}


def get_bundle(cfg: SynthConfig | None = None) -> dict[str, pd.DataFrame]:
    """Return all synthetic tables, memoised on config."""
    cfg = cfg or SynthConfig()
    key = (cfg.seed, cfg.days, cfg.start.isoformat())
    if key in _CACHE:
        return _CACHE[key]
    bundle = {
        "zones": build_zones_df(),
        "od": build_od_matrix(cfg),
        "journey": build_journey_times(cfg),
        "speed": build_speed_timeseries(cfg),
        "gps": build_gps_pings(cfg),
    }
    _CACHE[key] = bundle
    return bundle
