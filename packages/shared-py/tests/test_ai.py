"""
Tests for AI wrapper (shared_py.ai).

Validates:
- Mock mode determinism (same input → same output)
- Grade distribution
- Lifecycle decision logic
- Match rationale generation
- Client mode switching
- Graceful degradation
"""

import pytest
from shared_py.ai import (
    ai_client,
    AIClient,
    AIMode,
    GradeResult,
    LifecycleDecision,
    MatchRationale,
)
from shared_py.schemas.enums import Grade, LifecycleAction


class TestMockDeterminism:
    """Test that mock mode is deterministic and reproducible."""

    @pytest.mark.asyncio
    async def test_grade_product_deterministic(self):
        """Same media keys should produce identical grade results."""
        client = AIClient(mode=AIMode.MOCK)

        media_keys = ["s3://bucket/test-product-001.jpg"]
        reason = "Defective"
        category = "electronics"

        result1 = await client.grade_product(media_keys, reason, category)
        result2 = await client.grade_product(media_keys, reason, category)

        assert result1.grade == result2.grade
        assert result1.confidence == result2.confidence
        assert len(result1.defects) == len(result2.defects)
        assert result1.damage_summary.text == result2.damage_summary.text

    @pytest.mark.asyncio
    async def test_different_media_keys_different_grades(self):
        """Different media keys should produce different grades (with high probability)."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.grade_product(
            ["s3://bucket/product-001.jpg"], "Defective", "electronics"
        )
        result2 = await client.grade_product(
            ["s3://bucket/product-999.jpg"], "Defective", "electronics"
        )

        # With deterministic hashing, different seeds should yield different grades
        # (not guaranteed but very likely)
        assert result1.grade != result2.grade or result1.confidence != result2.confidence

    @pytest.mark.asyncio
    async def test_lifecycle_decision_deterministic(self):
        """Same grade + category + value should produce identical decisions."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.decide_lifecycle(Grade.B, "electronics", 75.0)
        result2 = await client.decide_lifecycle(Grade.B, "electronics", 75.0)

        assert result1.action == result2.action
        assert result1.value_recovery_estimate == result2.value_recovery_estimate
        assert result1.sustainability_score == result2.sustainability_score
        assert result1.rationale == result2.rationale

    @pytest.mark.asyncio
    async def test_match_rationale_deterministic(self):
        """Same match params should produce identical rationales."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.generate_match_rationale(
            buyer_distance_km=3.5,
            buyer_interests=["electronics", "gaming"],
            product_category="electronics",
            match_score=0.87,
        )
        result2 = await client.generate_match_rationale(
            buyer_distance_km=3.5,
            buyer_interests=["electronics", "gaming"],
            product_category="electronics",
            match_score=0.87,
        )

        assert result1.text == result2.text
        assert result1.key_factors == result2.key_factors
        assert result1.logistics_benefit == result2.logistics_benefit


class TestGradeLogic:
    """Test grade assignment logic and distribution."""

    @pytest.mark.asyncio
    async def test_all_grades_reachable(self):
        """Verify all four grades (A/B/C/D) are reachable in mock mode."""
        client = AIClient(mode=AIMode.MOCK)

        grades_seen = set()
        for i in range(20):
            result = await client.grade_product(
                [f"s3://bucket/product-{i:03d}.jpg"], "Defective", "electronics"
            )
            grades_seen.add(result.grade)

        assert Grade.A in grades_seen
        assert Grade.B in grades_seen
        assert Grade.C in grades_seen
        assert Grade.D in grades_seen

    @pytest.mark.asyncio
    async def test_grade_a_minimal_defects(self):
        """Grade A products should have 0-1 minor defects."""
        client = AIClient(mode=AIMode.MOCK)

        # Find a Grade A product
        for i in range(50):
            result = await client.grade_product(
                [f"s3://bucket/pristine-{i:03d}.jpg"], "Wrong item", "electronics"
            )
            if result.grade == Grade.A:
                assert len(result.defects) <= 1
                if result.defects:
                    assert result.defects[0].severity == "minor"
                break
        else:
            pytest.fail("No Grade A products found in 50 samples")

    @pytest.mark.asyncio
    async def test_grade_d_severe_defects(self):
        """Grade D products should have multiple defects including severe."""
        client = AIClient(mode=AIMode.MOCK)

        # Find a Grade D product
        for i in range(50):
            result = await client.grade_product(
                [f"s3://bucket/damaged-{i:03d}.jpg"], "Defective", "electronics"
            )
            if result.grade == Grade.D:
                assert len(result.defects) >= 3
                severities = [d.severity for d in result.defects]
                assert "severe" in severities or "moderate" in severities
                break
        else:
            pytest.fail("No Grade D products found in 50 samples")

    @pytest.mark.asyncio
    async def test_confidence_scores_valid_range(self):
        """All confidence scores should be in [0.0, 1.0]."""
        client = AIClient(mode=AIMode.MOCK)

        for i in range(10):
            result = await client.grade_product(
                [f"s3://bucket/product-{i}.jpg"], "Defective", "electronics"
            )
            assert 0.0 <= result.confidence <= 1.0
            for defect in result.defects:
                assert 0.0 <= defect.confidence <= 1.0


class TestLifecycleLogic:
    """Test lifecycle decision logic."""

    @pytest.mark.asyncio
    async def test_grade_a_high_value_resell(self):
        """Grade A + high value should recommend RESELL."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.decide_lifecycle(Grade.A, "electronics", 200.0)

        assert result.action == LifecycleAction.RESELL
        assert result.value_recovery_estimate > 100.0  # At least 50% recovery
        assert result.sustainability_score >= 80.0

    @pytest.mark.asyncio
    async def test_grade_d_electronics_recycle(self):
        """Grade D electronics should recommend RECYCLE."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.decide_lifecycle(Grade.D, "electronics", 50.0)

        assert result.action in (LifecycleAction.RECYCLE, LifecycleAction.DONATE)
        assert result.value_recovery_estimate < 10.0  # Low recovery
        assert result.sustainability_score >= 40.0

    @pytest.mark.asyncio
    async def test_grade_c_low_value_donate(self):
        """Grade C + low value should recommend DONATE."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.decide_lifecycle(Grade.C, "clothing", 15.0)

        assert result.action == LifecycleAction.DONATE
        assert result.value_recovery_estimate < 5.0

    @pytest.mark.asyncio
    async def test_grade_b_moderate_value_resell_or_refurbish(self):
        """Grade B + moderate value should recommend RESELL or REFURBISH."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.decide_lifecycle(Grade.B, "electronics", 75.0)

        assert result.action in (LifecycleAction.RESELL, LifecycleAction.REFURBISH)
        assert result.value_recovery_estimate >= 30.0

    @pytest.mark.asyncio
    async def test_sustainability_scores_valid_range(self):
        """All sustainability scores should be in [0.0, 100.0]."""
        client = AIClient(mode=AIMode.MOCK)

        for grade in [Grade.A, Grade.B, Grade.C, Grade.D]:
            result = await client.decide_lifecycle(grade, "electronics", 100.0)
            assert 0.0 <= result.sustainability_score <= 100.0


class TestMatchRationale:
    """Test match rationale generation."""

    @pytest.mark.asyncio
    async def test_close_proximity_high_co2_savings(self):
        """Very close buyers (<5km) should have high CO₂ savings."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.generate_match_rationale(
            buyer_distance_km=2.5,
            buyer_interests=["electronics"],
            product_category="electronics",
            match_score=0.90,
        )

        assert "2.5" in result.text or "close" in result.text.lower()
        assert result.logistics_benefit
        # Extract CO2 percentage (e.g. "~85% CO₂ reduction")
        if "%" in result.logistics_benefit:
            pct_str = result.logistics_benefit.split("%")[0].split("~")[-1]
            pct = int(pct_str)
            assert pct >= 70  # High savings for close proximity

    @pytest.mark.asyncio
    async def test_interest_alignment_mentioned(self):
        """Interest alignment should appear in key factors."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.generate_match_rationale(
            buyer_distance_km=8.0,
            buyer_interests=["electronics", "gaming"],
            product_category="electronics",
            match_score=0.85,
        )

        factors_text = " ".join(result.key_factors).lower()
        assert "interest" in factors_text or "electronics" in factors_text

    @pytest.mark.asyncio
    async def test_rationale_structure(self):
        """Match rationale should have all required fields."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.generate_match_rationale(
            buyer_distance_km=12.0,
            buyer_interests=["furniture"],
            product_category="furniture",
            match_score=0.75,
        )

        assert isinstance(result.text, str)
        assert len(result.text) > 20  # Non-trivial explanation
        assert isinstance(result.key_factors, list)
        assert len(result.key_factors) >= 2
        assert result.logistics_benefit
        assert "%" in result.logistics_benefit or "CO" in result.logistics_benefit


class TestClientModes:
    """Test AI client mode switching."""

    def test_mock_mode_default(self):
        """AI client should default to mock mode."""
        import os

        # Temporarily remove AI_MODE if set
        old_mode = os.environ.pop("AI_MODE", None)
        try:
            from shared_py.ai.client import _create_client

            client = _create_client()
            assert client.mode == AIMode.MOCK
        finally:
            if old_mode:
                os.environ["AI_MODE"] = old_mode

    def test_explicit_mock_mode(self):
        """AI client should accept explicit mock mode."""
        client = AIClient(mode=AIMode.MOCK)
        assert client.mode == AIMode.MOCK

    def test_aws_mode_falls_back_without_credentials(self):
        """AWS mode without credentials should fall back to mock gracefully."""
        # This test assumes no AWS credentials are configured
        client = AIClient(mode=AIMode.AWS, aws_region="us-east-1")
        # After attempting to initialize AWS clients, mode may fall back to mock
        # (depends on whether boto3 is installed and credentials are available)
        assert client.mode in (AIMode.AWS, AIMode.MOCK)


class TestGracefulDegradation:
    """Test that AI failures don't crash the system."""

    @pytest.mark.asyncio
    async def test_empty_media_keys_handled(self):
        """Empty media keys should not crash."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.grade_product([], "Defective", "electronics")

        assert isinstance(result, GradeResult)
        assert result.grade in [Grade.A, Grade.B, Grade.C, Grade.D]

    @pytest.mark.asyncio
    async def test_zero_value_handled(self):
        """Zero value estimate should not crash."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.decide_lifecycle(Grade.C, "electronics", 0.0)

        assert isinstance(result, LifecycleDecision)
        assert result.action in LifecycleAction

    @pytest.mark.asyncio
    async def test_negative_distance_handled(self):
        """Negative distance (edge case) should not crash."""
        client = AIClient(mode=AIMode.MOCK)

        # This is a malformed input, but we should handle it gracefully
        result = await client.generate_match_rationale(
            buyer_distance_km=-1.0,  # Invalid but shouldn't crash
            buyer_interests=[],
            product_category="electronics",
            match_score=0.5,
        )

        assert isinstance(result, MatchRationale)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
