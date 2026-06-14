"""
Unit tests for the Haversine distance formula and scoring logic.

These are pure-function tests — no DB or network required.
"""

import pytest

from app.domain.service import _compute_score, _estimated_savings, _haversine_km


class TestHaversine:
    def test_same_point_is_zero(self):
        assert _haversine_km(0.0, 0.0, 0.0, 0.0) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_london_paris(self):
        # London (51.507, -0.128) → Paris (48.857, 2.352) ≈ 341 km
        dist = _haversine_km(51.507, -0.128, 48.857, 2.352)
        assert 330 < dist < 360

    def test_symmetry(self):
        d1 = _haversine_km(40.0, -74.0, 34.0, -118.0)
        d2 = _haversine_km(34.0, -118.0, 40.0, -74.0)
        assert d1 == pytest.approx(d2, rel=1e-6)

    def test_non_negative(self):
        dist = _haversine_km(12.345, 67.890, 9.876, 54.321)
        assert dist >= 0.0


class TestComputeScore:
    def test_zero_distance_no_interest_match(self):
        score = _compute_score(
            distance_km=0.0, radius_km=50.0, buyer_interests=["clothing"], product_category="electronics"
        )
        # 70% proximity (100) + 0% interest = 70.0
        assert score == pytest.approx(70.0, abs=0.1)

    def test_zero_distance_with_interest_match(self):
        score = _compute_score(
            distance_km=0.0, radius_km=50.0, buyer_interests=["electronics"], product_category="electronics"
        )
        # 70% proximity (100) + 30% interest (100) = 100.0
        assert score == pytest.approx(100.0, abs=0.1)

    def test_beyond_radius_returns_zero(self):
        score = _compute_score(
            distance_km=60.0, radius_km=50.0, buyer_interests=["electronics"], product_category="electronics"
        )
        assert score == 0.0

    def test_at_radius_boundary_returns_zero_proximity(self):
        score = _compute_score(
            distance_km=50.0, radius_km=50.0, buyer_interests=[], product_category="x"
        )
        # proximity = 0, interest = 0
        assert score == pytest.approx(0.0, abs=0.1)

    def test_interest_case_insensitive(self):
        score = _compute_score(
            distance_km=0.0, radius_km=50.0, buyer_interests=["ELECTRONICS"], product_category="electronics"
        )
        assert score == pytest.approx(100.0, abs=0.1)


class TestEstimatedSavings:
    def test_nearby_buyer_has_high_savings(self):
        savings = _estimated_savings(distance_km=5.0)
        assert savings > 0

    def test_far_buyer_has_zero_savings(self):
        # distance_km > 50 → clamps to 0
        savings = _estimated_savings(distance_km=55.0)
        assert savings == 0.0

    def test_non_negative(self):
        assert _estimated_savings(200.0) >= 0.0
