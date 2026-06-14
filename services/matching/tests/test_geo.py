"""
Unit tests for Haversine geo utilities.

Pure math functions — no DB or network required.
"""

import pytest

from app.domain.geo import distance_to_score, estimate_savings, haversine_km


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine_km(37.7749, -122.4194, 37.7749, -122.4194) == pytest.approx(0.0, abs=0.001)

    def test_known_distance_sf_la(self):
        # San Francisco ↔ Los Angeles ≈ 559 km
        dist = haversine_km(37.7749, -122.4194, 34.0522, -118.2437)
        assert 550 < dist < 570

    def test_short_hyperlocal_distance(self):
        # ~1 km apart — very hyperlocal
        dist = haversine_km(37.7749, -122.4194, 37.7839, -122.4194)
        assert 0.5 < dist < 2.0

    def test_symmetry(self):
        d1 = haversine_km(37.7749, -122.4194, 37.8, -122.5)
        d2 = haversine_km(37.8, -122.5, 37.7749, -122.4194)
        assert d1 == pytest.approx(d2, rel=1e-6)


class TestDistanceToScore:
    def test_zero_distance_is_100(self):
        assert distance_to_score(0.0) == pytest.approx(100.0)

    def test_at_max_radius_is_zero(self):
        assert distance_to_score(50.0, max_radius_km=50.0) == pytest.approx(0.0)

    def test_midpoint_is_50(self):
        assert distance_to_score(25.0, max_radius_km=50.0) == pytest.approx(50.0)

    def test_beyond_radius_clamped_to_zero(self):
        assert distance_to_score(100.0, max_radius_km=50.0) == pytest.approx(0.0)

    def test_score_in_valid_range(self):
        for km in [0, 5, 10, 25, 40, 50]:
            score = distance_to_score(float(km))
            assert 0.0 <= score <= 100.0


class TestEstimateSavings:
    def test_zero_distance_maximum_savings(self):
        savings = estimate_savings(0.0)
        assert savings == pytest.approx(25.0)

    def test_savings_decrease_with_distance(self):
        assert estimate_savings(5.0) > estimate_savings(20.0)

    def test_savings_never_negative(self):
        assert estimate_savings(200.0) == pytest.approx(0.0)

    def test_midrange(self):
        # 50 km → 25 - 50*0.20 = 15.0
        assert estimate_savings(50.0) == pytest.approx(15.0)
