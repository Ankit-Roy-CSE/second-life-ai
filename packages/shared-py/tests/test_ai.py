"""
Tests for AI wrapper (shared_py.ai).

Validates:
- Mock mode determinism (same input → same output)
- Grade distribution
- Lifecycle decision logic
- Match rationale generation
- Client mode switching
- Graceful degradation
- Golden-path reproducibility
- Spec function separation (analyze_media, summarize_damage)
"""

import pytest
from shared_py.ai import (
    ai_client,
    AIClient,
    AIMode,
    GradeResult,
    LifecycleDecision,
    MatchRationale,
    MediaLabels,
    DamageSummary,
    GOLDEN_PATH_MEDIA_KEY,
    GOLDEN_PATH_CATEGORY,
    GOLDEN_PATH_REASON,
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

        result1 = await client.grade_product(media_keys, reason, category, correlation_id="test-1")
        result2 = await client.grade_product(media_keys, reason, category, correlation_id="test-1")

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
        assert result1.grade != result2.grade or result1.confidence != result2.confidence

    @pytest.mark.asyncio
    async def test_lifecycle_decision_deterministic(self):
        """Same grade + category + value should produce identical decisions."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.decide_lifecycle(Grade.B, "electronics", 75.0, correlation_id="r1")
        result2 = await client.decide_lifecycle(Grade.B, "electronics", 75.0, correlation_id="r1")

        assert result1.action == result2.action
        assert result1.value_recovery_estimate == result2.value_recovery_estimate
        assert result1.sustainability_score == result2.sustainability_score
        assert result1.rationale == result2.rationale

    @pytest.mark.asyncio
    async def test_match_rationale_deterministic(self):
        """Same match params should produce identical rationales."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.match_rationale(
            buyer_distance_km=3.5,
            buyer_interests=["electronics", "gaming"],
            product_category="electronics",
            match_score=0.87,
            correlation_id="r1",
        )
        result2 = await client.match_rationale(
            buyer_distance_km=3.5,
            buyer_interests=["electronics", "gaming"],
            product_category="electronics",
            match_score=0.87,
            correlation_id="r1",
        )

        assert result1.text == result2.text
        assert result1.key_factors == result2.key_factors
        assert result1.logistics_benefit == result2.logistics_benefit


class TestGoldenPath:
    """Test golden-path demo product reproducibility."""

    @pytest.mark.asyncio
    async def test_golden_path_produces_known_result(self):
        """The golden-path media key should always produce the same grade."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.grade_product(
            [GOLDEN_PATH_MEDIA_KEY], GOLDEN_PATH_REASON, GOLDEN_PATH_CATEGORY
        )
        result2 = await client.grade_product(
            [GOLDEN_PATH_MEDIA_KEY], GOLDEN_PATH_REASON, GOLDEN_PATH_CATEGORY
        )

        assert result1.grade == result2.grade
        assert result1.confidence == result2.confidence
        # Golden-path should produce a demo-friendly grade (not D/recycle)
        assert result1.grade in (Grade.A, Grade.B, Grade.C)

    @pytest.mark.asyncio
    async def test_golden_path_full_saga(self):
        """Golden-path should produce a coherent grade → decision → rationale chain."""
        client = AIClient(mode=AIMode.MOCK)

        grade_result = await client.grade_product(
            [GOLDEN_PATH_MEDIA_KEY], GOLDEN_PATH_REASON, GOLDEN_PATH_CATEGORY
        )
        decision = await client.decide_lifecycle(
            grade_result.grade, GOLDEN_PATH_CATEGORY, 120.0
        )

        # Decision should be a value-recovery action (not recycle) for demo
        assert decision.action in (
            LifecycleAction.RESELL,
            LifecycleAction.REFURBISH,
            LifecycleAction.HYPERLOCAL,
        )
        assert decision.value_recovery_estimate > 0


class TestSpecFunctions:
    """Test that analyze_media and summarize_damage work as separate spec functions."""

    @pytest.mark.asyncio
    async def test_analyze_media_returns_labels(self):
        """analyze_media should return MediaLabels with labels and defect cues."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.analyze_media(
            ["s3://bucket/product-123.jpg"],
            "Defective screen",
            "electronics",
            correlation_id="r-123",
        )

        assert isinstance(result, MediaLabels)
        assert len(result.labels) >= 3
        assert 0.0 <= result.confidence_avg <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_media_defect_cues_from_reason(self):
        """Defect-related return reasons should produce defect cues."""
        client = AIClient(mode=AIMode.MOCK)

        result_defect = await client.analyze_media(
            ["s3://bucket/item.jpg"], "Product is damaged", "electronics"
        )
        result_wrong = await client.analyze_media(
            ["s3://bucket/item.jpg"], "Wrong item shipped", "electronics"
        )

        assert len(result_defect.defect_cues) > 0
        assert len(result_wrong.defect_cues) == 0

    @pytest.mark.asyncio
    async def test_summarize_damage_returns_summary(self):
        """summarize_damage should return natural language summary."""
        client = AIClient(mode=AIMode.MOCK)

        labels = MediaLabels(labels=["device", "screen"], defect_cues=["scratch_detected"])
        from shared_py.ai.schemas import DefectItem

        defects = [DefectItem(name="scratch", severity="minor", location="screen", confidence=0.9)]

        result = await client.summarize_damage(labels, defects, "electronics", correlation_id="r1")

        assert isinstance(result, DamageSummary)
        assert len(result.text) > 10
        assert len(result.key_points) >= 1


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
        assert result.value_recovery_estimate > 100.0
        assert result.sustainability_score >= 80.0

    @pytest.mark.asyncio
    async def test_grade_d_electronics_recycle(self):
        """Grade D electronics should recommend RECYCLE."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.decide_lifecycle(Grade.D, "electronics", 50.0)

        assert result.action in (LifecycleAction.RECYCLE, LifecycleAction.DONATE)
        assert result.value_recovery_estimate < 10.0
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

        assert result.action in (
            LifecycleAction.RESELL,
            LifecycleAction.REFURBISH,
            LifecycleAction.HYPERLOCAL,
        )
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

        result = await client.match_rationale(
            buyer_distance_km=2.5,
            buyer_interests=["electronics"],
            product_category="electronics",
            match_score=0.90,
        )

        assert result.logistics_benefit
        assert "85%" in result.logistics_benefit

    @pytest.mark.asyncio
    async def test_interest_alignment_mentioned(self):
        """Interest alignment should appear in key factors."""
        client = AIClient(mode=AIMode.MOCK)

        result = await client.match_rationale(
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

        result = await client.match_rationale(
            buyer_distance_km=12.0,
            buyer_interests=["furniture"],
            product_category="furniture",
            match_score=0.75,
        )

        assert isinstance(result.text, str)
        assert len(result.text) > 20
        assert isinstance(result.key_factors, list)
        assert len(result.key_factors) >= 2
        assert result.logistics_benefit
        assert "%" in result.logistics_benefit


class TestClientModes:
    """Test AI client mode switching."""

    def test_mock_mode_default(self):
        """AI client should default to mock mode."""
        import os

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

    def test_bedrock_model_id_accepted(self):
        """Client should accept and store bedrock_model_id."""
        client = AIClient(mode=AIMode.MOCK, bedrock_model_id="anthropic.claude-3-sonnet")
        assert client.bedrock_model_id == "anthropic.claude-3-sonnet"

    def test_aws_mode_falls_back_without_credentials(self):
        """AWS mode without credentials should fall back to mock gracefully."""
        client = AIClient(mode=AIMode.AWS, aws_region="us-east-1")
        assert client.mode in (AIMode.AWS, AIMode.MOCK)


class TestGracefulDegradation:
    """Test that AI failures don't crash the system."""

    @pytest.mark.asyncio
    async def test_empty_media_keys_handled(self):
        """Empty media keys should not crash and should vary by reason/category."""
        client = AIClient(mode=AIMode.MOCK)

        result1 = await client.grade_product([], "Defective", "electronics")
        result2 = await client.grade_product([], "Wrong item", "clothing")

        assert isinstance(result1, GradeResult)
        assert isinstance(result2, GradeResult)
        # Different reason+category should produce different results (not same "default" hash)
        assert result1.grade != result2.grade or result1.confidence != result2.confidence

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

        result = await client.match_rationale(
            buyer_distance_km=-1.0,
            buyer_interests=[],
            product_category="electronics",
            match_score=0.5,
        )

        assert isinstance(result, MatchRationale)

    @pytest.mark.asyncio
    async def test_correlation_id_optional(self):
        """All methods should work with and without correlation_id."""
        client = AIClient(mode=AIMode.MOCK)

        # Without correlation_id
        r1 = await client.grade_product(["s3://img.jpg"], "Defective", "electronics")
        assert isinstance(r1, GradeResult)

        # With correlation_id
        r2 = await client.grade_product(
            ["s3://img.jpg"], "Defective", "electronics", correlation_id="test-corr-id"
        )
        assert isinstance(r2, GradeResult)
        assert r1.grade == r2.grade  # correlation_id doesn't affect output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
