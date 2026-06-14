# Implementation Plan: Golden-Path Demo Product + AI Fallback Test (P3-B2)

## Overview

Lock in the judge demo by:
1. Pinning all golden-path chain values as named literal constants in `shared_py/ai/client.py` and re-exporting them.
2. Adding an autouse conftest fixture that restores `AI_MODE` after every test.
3. Writing a full chain regression test (`test_golden_path.py`) with per-link assertions.
4. Writing init-failure and invocation-failure fallback tests in the same file.
5. Adding three property-based tests (determinism, fallback safety, proximity) using `hypothesis`.
6. Aligning `scripts/seed_min.py` to reference `GOLDEN_PATH_VALUE_ESTIMATE` for the headphones `original_price_usd`.
7. Marking P3-B2 done in `docs/progress-tracker.md`.

No new service code, no new endpoints, no new event types. All work lives in `packages/shared-py/`.

---

## Tasks

- [x] 1. Add Golden_Path_Constants to `shared_py/ai/client.py`
  - Open `packages/shared-py/shared_py/ai/client.py`
  - Locate the existing golden-path constants block (just below the comment
    `# ═══════════════════════════════════════════════════════════════════════════`
    `# Golden-path demo constants`)
  - Append the following literal constants immediately after `GOLDEN_PATH_REASON`, still inside
    the same section and before the next separator:
    ```python
    # Input pin — must be > 50.0 so the Grade.B mock branch returns RESELL (not REFURBISH)
    GOLDEN_PATH_VALUE_ESTIMATE: float = 120.00

    # Expected chain outputs — locked literals; any drift fails the Golden_Path_Test
    GOLDEN_PATH_EXPECTED_GRADE = Grade.B
    GOLDEN_PATH_EXPECTED_ACTION = LifecycleAction.RESELL
    GOLDEN_PATH_EXPECTED_VALUE_RECOVERY: float = 72.00
    GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE: float = 80.0

    # Match inputs — distance < 5.0 km guarantees the "85%" logistics benefit string
    GOLDEN_PATH_MATCH_DISTANCE_KM: float = 0.4
    GOLDEN_PATH_MATCH_INTERESTS: list[str] = ["electronics", "gaming", "headphones"]
    GOLDEN_PATH_MATCH_SCORE: float = 0.92
    ```
  - All values are literals — no runtime computation
  - `Grade` and `LifecycleAction` are already imported in `client.py`
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2. Re-export new constants from `shared_py/ai/__init__.py`
  - Open `packages/shared-py/shared_py/ai/__init__.py`
  - Add all eight new constant names to the `from .client import (...)` block:
    `GOLDEN_PATH_VALUE_ESTIMATE`, `GOLDEN_PATH_EXPECTED_GRADE`, `GOLDEN_PATH_EXPECTED_ACTION`,
    `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY`, `GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE`,
    `GOLDEN_PATH_MATCH_DISTANCE_KM`, `GOLDEN_PATH_MATCH_INTERESTS`, `GOLDEN_PATH_MATCH_SCORE`
  - Add the same names to `__all__`
  - _Requirements: 1.1, 1.6_

- [x] 3. Create `packages/shared-py/tests/conftest.py` with autouse `AI_MODE` fixture
  - Create the file `packages/shared-py/tests/conftest.py` (new file — does not exist yet)
  - Implement an autouse pytest fixture that snapshots `os.environ.get("AI_MODE")` before
    every test and restores (or removes) it in the `finally` block:
    ```python
    import os
    import pytest

    @pytest.fixture(autouse=True)
    def _restore_ai_mode():
        prior = os.environ.get("AI_MODE")
        try:
            yield
        finally:
            if prior is None:
                os.environ.pop("AI_MODE", None)
            else:
                os.environ["AI_MODE"] = prior
    ```
  - No other fixtures needed in conftest for this feature
  - _Requirements: 9.4_

- [x] 4. Create `packages/shared-py/tests/test_golden_path.py` — Golden_Path_Test (chain regression)
  - Create the new file `packages/shared-py/tests/test_golden_path.py`
  - Add the shared `_run_golden_chain` async helper at module level:
    ```python
    async def _run_golden_chain(client):
        grade = await client.grade_product(
            [GOLDEN_PATH_MEDIA_KEY], GOLDEN_PATH_REASON, GOLDEN_PATH_CATEGORY
        )
        decision = await client.decide_lifecycle(
            grade.grade, GOLDEN_PATH_CATEGORY, GOLDEN_PATH_VALUE_ESTIMATE
        )
        match = await client.match_rationale(
            GOLDEN_PATH_MATCH_DISTANCE_KM, GOLDEN_PATH_MATCH_INTERESTS,
            GOLDEN_PATH_CATEGORY, GOLDEN_PATH_MATCH_SCORE,
        )
        return grade, decision, match
    ```
  - Implement `test_golden_path_chain` (async, `@pytest.mark.asyncio`):
    - Construct `AIClient(mode=AIMode.MOCK)` explicitly
    - Call `_run_golden_chain(client)` and unpack `grade, decision, match`
    - Assert each locked link with a message identifying the diverging link:
      - `assert grade.grade == GOLDEN_PATH_EXPECTED_GRADE, "grade link: expected Grade.B"`
      - `assert decision.action == GOLDEN_PATH_EXPECTED_ACTION, "lifecycle link: expected RESELL"`
      - `assert decision.value_recovery_estimate == GOLDEN_PATH_EXPECTED_VALUE_RECOVERY, "value_recovery link: expected 72.00"`
      - `assert decision.sustainability_score == GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE, "sustainability_score link: expected 80.0"`
      - `assert match.logistics_benefit, "match link: logistics_benefit must be non-empty"`
      - `assert "85%" in match.logistics_benefit, "match link: logistics_benefit must contain '85%'"`
    - Assert in-range checks (Requirements 2.3, 3.3, 3.4):
      - `assert 0.0 <= grade.confidence <= 1.0`
      - `assert decision.value_recovery_estimate > 0`
      - `assert 0.0 <= decision.sustainability_score <= 100.0`
  - Implement `test_golden_path_constants` (sync):
    - Assert all new constants exist, have the correct Python types, and that
      `GOLDEN_PATH_VALUE_ESTIMATE > 50.0`
    - Cover: `GOLDEN_PATH_VALUE_ESTIMATE` (float, > 50.0), `GOLDEN_PATH_EXPECTED_GRADE`
      (is `Grade.B`), `GOLDEN_PATH_EXPECTED_ACTION` (is `LifecycleAction.RESELL`),
      `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY` (float), `GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE`
      (float), `GOLDEN_PATH_MATCH_DISTANCE_KM` (float), `GOLDEN_PATH_MATCH_INTERESTS` (list),
      `GOLDEN_PATH_MATCH_SCORE` (float)
  - _Requirements: 2.1, 2.3, 3.1, 3.3, 3.4, 4.1, 4.3, 5.1–5.6_

  - [-]* 4.1 Write unit tests for constant types and chain assertions
    - Verify `GOLDEN_PATH_VALUE_ESTIMATE > 50.0` with an explicit assertion message
    - Verify `isinstance(GOLDEN_PATH_MATCH_INTERESTS, list)` and all elements are `str`
    - _Requirements: 1.2, 1.5, 1.6_

- [x] 5. Add Fallback_Test to `packages/shared-py/tests/test_golden_path.py`
  - In the same file as Task 4, implement:
  - `test_fallback_init_failure_completes_chain` (async, `@pytest.mark.asyncio`):
    - Define `_raise_boto(*args, **kwargs)` that raises `RuntimeError("simulated AWS unavailable")`
    - Use `with unittest.mock.patch("boto3.client", side_effect=_raise_boto):` as a context manager
    - Construct `AIClient(mode=AIMode.AWS, aws_region="us-east-1")` inside the `with` block
    - Call `await _run_golden_chain(client)` — must not raise
    - After the `with` block, assert `client.mode == AIMode.MOCK` (Requirement 6.1)
    - Assert `grade.grade == GOLDEN_PATH_EXPECTED_GRADE` (Requirements 6.2, 7.2)
  - `test_fallback_invocation_failure` — parametrized over the three AWS operations:
    - Parameters: `("grade_product", "converse")`, `("decide_lifecycle", "converse")`,
      `("match_rationale", "converse")`; also cover Rekognition via `"detect_labels"` and
      `"detect_moderation_labels"` sub-variants
    - Build a stub boto3 client object whose target method raises on call; patch
      `boto3.client` to return the stub (mode stays `AWS`, does NOT flip to MOCK)
    - Run the affected chain step; assert no exception escapes and a mock result is returned
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1–7.5_

- [x] 6. Add property-based tests to `packages/shared-py/tests/test_golden_path.py`

  - [x] 6.1 Add `hypothesis==6.*` to `[project.optional-dependencies].dev` in `packages/shared-py/pyproject.toml`
    - Add `"hypothesis==6.*",` to the `dev` list alongside the existing `pytest`, `pytest-asyncio`,
      `ruff`, `black` entries
    - _Requirements: 9.1, 9.3_

  - [-]* 6.2 Write property test for Property 1 — Mock determinism
    - `# Feature: golden-path-demo, Property 1: Mock determinism across grade, decision, and match`
    - `@settings(max_examples=100)`
    - `@given(...)` — draw: media keys (`st.text(min_size=1)`), reasons
      (`st.sampled_from([...])`), categories (`st.sampled_from(["electronics","clothing","furniture","toys"])`),
      grades (`st.sampled_from(list(Grade))`), value estimates
      (`st.floats(min_value=0, max_value=5000, allow_nan=False, allow_infinity=False)`),
      distances (`st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)`),
      interests (`st.lists(st.sampled_from(["electronics","gaming","headphones","clothing","furniture"]), min_size=0, max_size=5)`),
      scores (`st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)`)
    - Construct `AIClient(mode=AIMode.MOCK)` inside the test body; invoke each operation twice
      via `asyncio.run(...)` and assert field equality:
      - `grade_product`: grade, confidence, defect count, damage summary text are equal on both calls
      - `decide_lifecycle`: action, value_recovery_estimate, sustainability_score, rationale equal
      - `match_rationale`: text, key_factors, logistics_benefit equal
    - **Validates: Requirements 2.2, 2.4, 3.2, 4.2**

  - [-]* 6.3 Write property test for Property 2 — Fallback safety and equivalence
    - `# Feature: golden-path-demo, Property 2: Fallback safety and equivalence`
    - `@settings(max_examples=100)`
    - `@given(...)` over the same input space as Property 1
    - For each generated example:
      - Compute mock-mode result for the operation
      - Patch `boto3.client` to raise, build `AIClient(mode=AIMode.AWS)`, call the same operation
      - Assert the AWS-mode result equals the mock-mode result and that no exception was raised
    - Also assert full golden chain completes without raising under induced AWS failure
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

  - [-]* 6.4 Write property test for Property 3 — Proximity logistics benefit
    - `# Feature: golden-path-demo, Property 3: Proximity logistics benefit`
    - `@settings(max_examples=100)`
    - `@given(distance=st.floats(min_value=0.0, max_value=4.999, allow_nan=False, allow_infinity=False))`
    - Construct `AIClient(mode=AIMode.MOCK)`; call `match_rationale` with the drawn distance,
      `GOLDEN_PATH_MATCH_INTERESTS`, `GOLDEN_PATH_CATEGORY`, and `GOLDEN_PATH_MATCH_SCORE`
    - Assert `match.logistics_benefit` is non-empty and `"85%" in match.logistics_benefit`
    - **Validates: Requirement 4.3**

- [ ] 7. Align `scripts/seed_min.py` — import and use `GOLDEN_PATH_VALUE_ESTIMATE`
  - Open `scripts/seed_min.py`
  - Add `GOLDEN_PATH_VALUE_ESTIMATE` to the existing import from `shared_py.ai.client`:
    ```python
    from shared_py.ai.client import (
        GOLDEN_PATH_MEDIA_KEY,
        GOLDEN_PATH_CATEGORY,
        GOLDEN_PATH_REASON,
        GOLDEN_PATH_VALUE_ESTIMATE,
    )
    ```
  - In the `PRODUCTS` list, find the headphones product (`PRODUCT_HEADPHONES_ID`) and update
    `"original_price_usd"` inside `attributes` from the hardcoded `45.00` to
    `GOLDEN_PATH_VALUE_ESTIMATE` — this ensures the seeded price is consistent with the locked
    RESELL threshold (must be > 50.0 per Requirement 1.2)
  - No other changes to `seed_min.py`
  - _Requirements: 8.1, 8.2_

- [ ] 8. Update `docs/progress-tracker.md` — mark P3-B2 done
  - Locate the `P3-B2` row in the Phase 3 table
  - Set status to `✅ Done`
  - Fill in Notes: e.g. `Golden_Path_Constants added to client.py + re-exported; conftest.py
    AI_MODE fixture; test_golden_path.py: chain regression, fallback init+invocation, 3 hypothesis
    properties (determinism, fallback safety, proximity); seed_min.py price aligned to
    GOLDEN_PATH_VALUE_ESTIMATE; hypothesis==6.* added to pyproject.toml dev extras`
  - Update the Phase 3 "Not started" count (−1) and "Done" count (+1) in the Overall Progress table
  - Update `Last updated` header line
  - _Requirements: 8.3_

- [ ] 9. Final checkpoint — ensure the suite is clean
  - Run `AI_MODE=mock pytest packages/shared-py/tests/test_golden_path.py -q` (or equivalent
    local invocation) and confirm all tests pass
  - Run `ruff check .` and `black --check .` from `packages/shared-py` and fix any issues
  - Ensure no test leaves `AI_MODE` modified (autouse fixture in conftest.py covers this)
  - Ensure all tests pass without AWS credentials or network access

---

## Notes

- Tasks marked with `*` are optional (property-based and unit tests) and can be skipped for a
  faster MVP; the core constant, test-chain, and fallback tasks are mandatory.
- All tests construct `AIClient(mode=...)` explicitly — never rely on the module-level `ai_client`
  singleton so tests remain keyless and offline.
- Property tests call async operations via `asyncio.run(...)` inside `@given` functions (not
  `@pytest.mark.asyncio`) to avoid known Hypothesis + asyncio fixture interaction issues.
- `boto3.client` is patched via `unittest.mock.patch` as a context manager (not the function-scoped
  `monkeypatch` fixture) so the patch is applied and torn down correctly for each Hypothesis example.
- `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY = 72.00` is a literal (not `120.00 * 0.60`) — this is
  intentional: any drift in the mock's multipliers will fail the test loudly.
- The headphones `original_price_usd` in seed_min.py is currently `45.00` (below the RESELL
  threshold). Task 7 corrects this by referencing the constant.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2", "3", "6.1"] },
    { "id": 2, "tasks": ["4", "5"] },
    { "id": 3, "tasks": ["4.1", "6.2", "6.3", "6.4"] },
    { "id": 4, "tasks": ["7", "8"] },
    { "id": 5, "tasks": ["9"] }
  ]
}
```
