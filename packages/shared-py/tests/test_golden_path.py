"""Golden-path chain regression and fallback tests for P3-B2."""
import asyncio
import os
import unittest.mock as mock

import pytest

from shared_py.ai import (
    AIClient,
    AIMode,
    GOLDEN_PATH_MEDIA_KEY,
    GOLDEN_PATH_CATEGORY,
    GOLDEN_PATH_REASON,
    GOLDEN_PATH_VALUE_ESTIMATE,
    GOLDEN_PATH_EXPECTED_GRADE,
    GOLDEN_PATH_EXPECTED_ACTION,
    GOLDEN_PATH_EXPECTED_VALUE_RECOVERY,
    GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE,
    GOLDEN_PATH_MATCH_DISTANCE_KM,
    GOLDEN_PATH_MATCH_INTERESTS,
    GOLDEN_PATH_MATCH_SCORE,
)
from shared_py.schemas.enums import Grade, LifecycleAction


# ─────────────────────────────────────────────────────────────────────────────
# Shared async helper
# ─────────────────────────────────────────────────────────────────────────────

async def _run_golden_chain(client):
    grade = await client.grade_product(
        [GOLDEN_PATH_MEDIA_KEY], GOLDEN_PATH_REASON, GOLDEN_PATH_CATEGORY
    )
    decision = await client.decide_lifecycle(
        grade.grade, GOLDEN_PATH_CATEGORY, GOLDEN_PATH_VALUE_ESTIMATE
    )
    match = await client.match_rationale(
        GOLDEN_PATH_MATCH_DISTANCE_KM,
        GOLDEN_PATH_MATCH_INTERESTS,
        GOLDEN_PATH_CATEGORY,
        GOLDEN_PATH_MATCH_SCORE,
    )
    return grade, decision, match


# ─────────────────────────────────────────────────────────────────────────────
# Task 4 — Golden_Path_Test (chain regression)
# ─────────────────────────────────────────────────────────────────────────────

def test_golden_path_constants():
    """Verify all golden-path constants exist, have the correct Python types, and expected values."""
    assert isinstance(GOLDEN_PATH_VALUE_ESTIMATE, float), "GOLDEN_PATH_VALUE_ESTIMATE must be a float"
    assert GOLDEN_PATH_VALUE_ESTIMATE > 50.0, "GOLDEN_PATH_VALUE_ESTIMATE must be > 50.0 to trigger RESELL branch"

    assert GOLDEN_PATH_EXPECTED_GRADE is Grade.B, "GOLDEN_PATH_EXPECTED_GRADE must be Grade.B"
    assert GOLDEN_PATH_EXPECTED_ACTION is LifecycleAction.RESELL, "GOLDEN_PATH_EXPECTED_ACTION must be LifecycleAction.RESELL"

    assert isinstance(GOLDEN_PATH_EXPECTED_VALUE_RECOVERY, float), "GOLDEN_PATH_EXPECTED_VALUE_RECOVERY must be a float"
    assert isinstance(GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE, float), "GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE must be a float"

    assert isinstance(GOLDEN_PATH_MATCH_DISTANCE_KM, float), "GOLDEN_PATH_MATCH_DISTANCE_KM must be a float"

    assert isinstance(GOLDEN_PATH_MATCH_INTERESTS, list), "GOLDEN_PATH_MATCH_INTERESTS must be a list"
    assert all(isinstance(i, str) for i in GOLDEN_PATH_MATCH_INTERESTS), \
        "All elements of GOLDEN_PATH_MATCH_INTERESTS must be str"

    assert isinstance(GOLDEN_PATH_MATCH_SCORE, float), "GOLDEN_PATH_MATCH_SCORE must be a float"


@pytest.mark.asyncio
async def test_golden_path_chain():
    """Full chain regression: grade → lifecycle → match with locked per-link assertions."""
    client = AIClient(mode=AIMode.MOCK)
    grade, decision, match = await _run_golden_chain(client)

    # Locked link assertions — any drift fails loudly with a message identifying the link
    assert grade.grade == GOLDEN_PATH_EXPECTED_GRADE, "grade link: expected Grade.B"
    assert decision.action == GOLDEN_PATH_EXPECTED_ACTION, "lifecycle link: expected RESELL"
    assert decision.value_recovery_estimate == GOLDEN_PATH_EXPECTED_VALUE_RECOVERY, \
        "value_recovery link: expected 72.00"
    assert decision.sustainability_score == GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE, \
        "sustainability_score link: expected 80.0"
    assert match.logistics_benefit, "match link: logistics_benefit must be non-empty"
    assert "85%" in match.logistics_benefit, "match link: logistics_benefit must contain '85%'"

    # In-range checks (Requirements 2.3, 3.3, 3.4)
    assert 0.0 <= grade.confidence <= 1.0
    assert decision.value_recovery_estimate > 0
    assert 0.0 <= decision.sustainability_score <= 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Task 5 — Fallback_Test
# ─────────────────────────────────────────────────────────────────────────────

def _raise_boto(*args, **kwargs):
    raise RuntimeError("simulated AWS unavailable (no credentials / unreachable)")


@pytest.mark.asyncio
async def test_fallback_init_failure_completes_chain():
    with mock.patch("boto3.client", side_effect=_raise_boto):
        client = AIClient(mode=AIMode.AWS, aws_region="us-east-1")
        grade, decision, match = await _run_golden_chain(client)
    assert client.mode == AIMode.MOCK, "fallback: mode should flip to MOCK on init failure"
    assert grade.grade == GOLDEN_PATH_EXPECTED_GRADE, "fallback: grade should match golden-path grade"


class _StubBotoClient:
    """Stub that lets initialization succeed but raises on AWS API calls."""

    def converse(self, **kwargs):
        raise RuntimeError("simulated Bedrock invocation failure")

    def detect_labels(self, **kwargs):
        raise RuntimeError("simulated Rekognition detect_labels failure")

    def detect_moderation_labels(self, **kwargs):
        raise RuntimeError("simulated Rekognition detect_moderation_labels failure")


@pytest.mark.parametrize(
    "operation",
    ["grade_product", "decide_lifecycle", "match_rationale"],
)
@pytest.mark.asyncio
async def test_fallback_invocation_failure(operation):
    """Each AWS operation must fall back to mock when the AWS call raises."""
    stub = _StubBotoClient()

    with mock.patch("boto3.client", return_value=stub):
        client = AIClient(mode=AIMode.AWS, aws_region="us-east-1")
        # mode stays AWS (init succeeded), but calls will fail and fall back per-call
        if operation == "grade_product":
            result = await client.grade_product(
                [GOLDEN_PATH_MEDIA_KEY], GOLDEN_PATH_REASON, GOLDEN_PATH_CATEGORY
            )
            assert result.grade == GOLDEN_PATH_EXPECTED_GRADE, (
                "invocation fallback: grade_product should return mock grade"
            )
        elif operation == "decide_lifecycle":
            result = await client.decide_lifecycle(
                GOLDEN_PATH_EXPECTED_GRADE, GOLDEN_PATH_CATEGORY, GOLDEN_PATH_VALUE_ESTIMATE
            )
            assert result.action == GOLDEN_PATH_EXPECTED_ACTION, (
                "invocation fallback: decide_lifecycle should return mock action"
            )
        elif operation == "match_rationale":
            result = await client.match_rationale(
                GOLDEN_PATH_MATCH_DISTANCE_KM,
                GOLDEN_PATH_MATCH_INTERESTS,
                GOLDEN_PATH_CATEGORY,
                GOLDEN_PATH_MATCH_SCORE,
            )
            assert result.logistics_benefit, (
                "invocation fallback: match_rationale should return non-empty logistics_benefit"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Property-based tests (hypothesis)
# ─────────────────────────────────────────────────────────────────────────────

from hypothesis import given, settings
from hypothesis import strategies as st


# Feature: golden-path-demo, Property 1: Mock determinism across grade, decision, and match
@settings(max_examples=100)
@given(
    media_key=st.text(min_size=1),
    reason=st.sampled_from([
        "Defective", "Item not as expected", "Wrong item", "Damaged", "Changed mind",
        "Product is broken", "Screen has dead pixels", "Does not work as described",
    ]),
    category=st.sampled_from(["electronics", "clothing", "furniture", "toys"]),
    grade=st.sampled_from(list(Grade)),
    value=st.floats(min_value=0, max_value=5000, allow_nan=False, allow_infinity=False),
    distance=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    interests=st.lists(
        st.sampled_from(["electronics", "gaming", "headphones", "clothing", "furniture"]),
        min_size=0,
        max_size=5,
    ),
    score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_prop_mock_determinism(media_key, reason, category, grade, value, distance, interests, score):
    """Property 1: mock mode returns identical outputs on two calls with the same inputs."""
    client = AIClient(mode=AIMode.MOCK)

    # grade_product determinism
    r1 = asyncio.run(client.grade_product([media_key], reason, category))
    r2 = asyncio.run(client.grade_product([media_key], reason, category))
    assert r1.grade == r2.grade, f"grade non-deterministic for media_key={media_key!r}"
    assert r1.confidence == r2.confidence
    assert len(r1.defects) == len(r2.defects)
    assert r1.damage_summary.text == r2.damage_summary.text

    # decide_lifecycle determinism
    d1 = asyncio.run(client.decide_lifecycle(grade, category, value))
    d2 = asyncio.run(client.decide_lifecycle(grade, category, value))
    assert d1.action == d2.action
    assert d1.value_recovery_estimate == d2.value_recovery_estimate
    assert d1.sustainability_score == d2.sustainability_score
    assert d1.rationale == d2.rationale

    # match_rationale determinism
    m1 = asyncio.run(client.match_rationale(distance, interests, category, score))
    m2 = asyncio.run(client.match_rationale(distance, interests, category, score))
    assert m1.text == m2.text
    assert m1.key_factors == m2.key_factors
    assert m1.logistics_benefit == m2.logistics_benefit


# Feature: golden-path-demo, Property 2: Fallback safety and equivalence
@settings(max_examples=100)
@given(
    media_key=st.text(min_size=1),
    reason=st.sampled_from([
        "Defective", "Item not as expected", "Wrong item", "Damaged", "Changed mind",
    ]),
    category=st.sampled_from(["electronics", "clothing", "furniture", "toys"]),
    grade=st.sampled_from(list(Grade)),
    value=st.floats(min_value=0, max_value=5000, allow_nan=False, allow_infinity=False),
    distance=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    interests=st.lists(
        st.sampled_from(["electronics", "gaming", "headphones", "clothing", "furniture"]),
        min_size=0,
        max_size=5,
    ),
    score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_prop_fallback_safety_equivalence(media_key, reason, category, grade, value, distance, interests, score):
    """Property 2: AWS-mode with init failure returns same result as mock and raises no exception.

    Validates: Requirements 6.1, 6.2, 6.3, 6.4
    """
    mock_client = AIClient(mode=AIMode.MOCK)

    def _raise_boto_prop(*args, **kwargs):
        raise RuntimeError("property test: simulated AWS unavailable")

    with mock.patch("boto3.client", side_effect=_raise_boto_prop):
        aws_client = AIClient(mode=AIMode.AWS, aws_region="us-east-1")

        # grade_product: no exception, result equals mock
        mock_grade = asyncio.run(mock_client.grade_product([media_key], reason, category))
        aws_grade = asyncio.run(aws_client.grade_product([media_key], reason, category))
        assert aws_grade.grade == mock_grade.grade, (
            f"fallback equivalence: grade mismatch for media_key={media_key!r}"
        )

        # decide_lifecycle: no exception, result equals mock
        mock_decision = asyncio.run(mock_client.decide_lifecycle(grade, category, value))
        aws_decision = asyncio.run(aws_client.decide_lifecycle(grade, category, value))
        assert aws_decision.action == mock_decision.action, (
            f"fallback equivalence: action mismatch for grade={grade}, value={value}"
        )

        # match_rationale: no exception, result equals mock
        mock_match = asyncio.run(mock_client.match_rationale(distance, interests, category, score))
        aws_match = asyncio.run(aws_client.match_rationale(distance, interests, category, score))
        assert aws_match.logistics_benefit == mock_match.logistics_benefit, (
            f"fallback equivalence: logistics_benefit mismatch for distance={distance}"
        )

        # Full golden chain completes without raising
        asyncio.run(_run_golden_chain(aws_client))


# Feature: golden-path-demo, Property 3: Proximity logistics benefit
@settings(max_examples=100)
@given(
    distance=st.floats(min_value=0.0, max_value=4.999, allow_nan=False, allow_infinity=False),
)
def test_prop_proximity_logistics_benefit(distance):
    """Property 3: buyer distances < 5.0 km always yield an '85%' logistics benefit."""
    client = AIClient(mode=AIMode.MOCK)
    result = asyncio.run(
        client.match_rationale(
            distance,
            GOLDEN_PATH_MATCH_INTERESTS,
            GOLDEN_PATH_CATEGORY,
            GOLDEN_PATH_MATCH_SCORE,
        )
    )
    assert result.logistics_benefit, (
        f"logistics_benefit must be non-empty for distance={distance}"
    )
    assert "85%" in result.logistics_benefit, (
        f"logistics_benefit must contain '85%' for distance={distance} < 5.0 km"
    )
