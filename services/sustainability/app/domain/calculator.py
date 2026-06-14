"""
Sustainability impact calculator — pure deterministic logic, no LLM.

All metrics are derived from lookup tables and simple arithmetic.
Each function is pure (no DB, no network) so the logic is trivially testable.

Emission factor sources (simplified for demo):
  - Average product weight by category: industry average estimates
  - CO₂ per kg shipped: 0.5 kg CO₂ / km / kg (road freight average)
  - Landfill avoided: product weight (electronics are heavier; clothing lighter)
  - Green-credit rate: 1 credit per $1 value recovered + 5 credits per kg CO₂ avoided
"""

from __future__ import annotations

# ── Category-specific constants ───────────────────────────────────────────────
# Average product weight in kg by category (used when exact weight is unavailable)
_AVG_WEIGHT_KG: dict[str, float] = {
    "electronics": 1.2,
    "clothing": 0.5,
    "furniture": 8.0,
    "toys": 0.8,
    "appliances": 5.0,
    "books": 0.4,
}
_DEFAULT_WEIGHT_KG = 1.0

# CO₂ emitted per kg-km by transport mode
_CO2_PER_KG_KM = 0.00015  # kg CO₂ per (product-kg × distance-km)

# Average return logistics distance (km) if no better estimate is available
_AVG_LOGISTICS_KM = 200.0

# Landfill diversion fraction: how much of the product weight is diverted
_LANDFILL_FRACTION_BY_ACTION: dict[str, float] = {
    "RESELL": 0.95,       # nearly all diverted
    "REFURBISH": 0.90,    # some consumables discarded in refurb
    "DONATE": 0.85,
    "RECYCLE": 0.70,      # some non-recyclable fractions lost
    "HYPERLOCAL": 0.95,
}
_DEFAULT_LANDFILL_FRACTION = 0.80

# Green credit rates
_CREDITS_PER_USD_VALUE = 1.0       # 1 credit per $1 recovered
_CREDITS_PER_KG_CO2 = 5.0         # 5 credits per kg CO₂ avoided


def _product_weight_kg(category: str) -> float:
    return _AVG_WEIGHT_KG.get(category.lower(), _DEFAULT_WEIGHT_KG)


def calculate_co2_avoided(
    category: str,
    distance_km: float | None = None,
) -> float:
    """
    Estimate CO₂ avoided in kg by diverting a product from reverse logistics.

    The model: shipping a product round-trip to a warehouse-and-back emits
    (weight × distance × co2_factor) kg of CO₂.  Hyperlocal transfer avoids
    most of that; marketplace listing avoids less (item still moves, but shorter).

    Args:
        category:     Product category string.
        distance_km:  Actual buyer distance if known (hyperlocal match), else
                      uses the average logistics estimate.

    Returns:
        Estimated CO₂ avoided in kg (non-negative).
    """
    weight = _product_weight_kg(category)
    km = distance_km if distance_km is not None else _AVG_LOGISTICS_KM
    # Round-trip from warehouse is ~2× distance; local pickup avoids that entirely
    return round(weight * km * 2 * _CO2_PER_KG_KM, 4)


def calculate_waste_diverted(
    category: str,
    lifecycle_action: str,
) -> float:
    """
    Estimate waste diverted from landfill in kg.

    Args:
        category:          Product category.
        lifecycle_action:  One of RESELL / REFURBISH / DONATE / RECYCLE / HYPERLOCAL.

    Returns:
        Estimated waste diverted in kg (non-negative).
    """
    weight = _product_weight_kg(category)
    fraction = _LANDFILL_FRACTION_BY_ACTION.get(
        lifecycle_action.upper(), _DEFAULT_LANDFILL_FRACTION
    )
    return round(weight * fraction, 4)


def calculate_green_credits(
    co2_avoided_kg: float,
    value_recovered: float,
) -> float:
    """
    Calculate green credits awarded to the returning customer.

    Args:
        co2_avoided_kg:  Calculated CO₂ avoided (kg).
        value_recovered: Estimated or actual value recovered (USD).

    Returns:
        Green credits (non-negative float).
    """
    credits = (
        co2_avoided_kg * _CREDITS_PER_KG_CO2
        + value_recovered * _CREDITS_PER_USD_VALUE
    )
    return round(max(0.0, credits), 2)


def calculate_metrics(
    *,
    category: str,
    lifecycle_action: str,
    value_recovered: float,
    distance_km: float | None = None,
) -> dict[str, float]:
    """
    Calculate all sustainability metrics in a single call.

    Returns a dict with keys:
        co2_avoided_kg, waste_diverted_kg, value_recovered, green_credits
    """
    co2 = calculate_co2_avoided(category, distance_km)
    waste = calculate_waste_diverted(category, lifecycle_action)
    credits = calculate_green_credits(co2, value_recovered)

    return {
        "co2_avoided_kg": co2,
        "waste_diverted_kg": waste,
        "value_recovered": round(value_recovered, 2),
        "green_credits": credits,
    }
