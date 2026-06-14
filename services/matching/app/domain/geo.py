"""
Haversine distance calculation — pure Python, no PostGIS dependency.

Used by the matching service to score buyer candidates by proximity.
"""

import math


_EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance (km) between two points on Earth.

    Uses the Haversine formula which is accurate to within ~0.5% for most
    distances relevant to hyperlocal matching (< 500 km).

    Args:
        lat1, lng1: Coordinates of the first point (seller/product location).
        lat2, lng2: Coordinates of the second point (buyer location).

    Returns:
        Distance in kilometres (always >= 0).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_KM * c


def distance_to_score(distance_km: float, max_radius_km: float = 50.0) -> float:
    """
    Convert a distance into a 0–100 match score.

    Score decays linearly from 100 (at distance 0) to 0 (at max_radius_km).
    Buyers beyond the radius are excluded before scoring, so clamping at 0
    is a safety net only.

    Args:
        distance_km: Calculated Haversine distance.
        max_radius_km: Maximum radius used in the candidate query.

    Returns:
        Float score in [0.0, 100.0].
    """
    if distance_km <= 0:
        return 100.0
    if distance_km >= max_radius_km:
        return 0.0
    return max(0.0, 100.0 * (1.0 - distance_km / max_radius_km))


def estimate_savings(distance_km: float) -> float:
    """
    Rough USD estimate of logistics savings from hyperlocal delivery vs. warehouse shipping.

    Uses a simple linear model:
      savings = BASE_SAVING - (distance_km × COST_PER_KM)

    The model is intentionally simple for demo purposes. Real production code
    would integrate carrier rate cards.

    Args:
        distance_km: Distance to buyer in kilometres.

    Returns:
        Estimated savings in USD (clamped to >= 0).
    """
    BASE_SAVING = 25.0   # USD saved vs. standard warehouse fulfilment
    COST_PER_KM = 0.20   # incremental cost per km of local delivery

    return max(0.0, BASE_SAVING - distance_km * COST_PER_KM)
