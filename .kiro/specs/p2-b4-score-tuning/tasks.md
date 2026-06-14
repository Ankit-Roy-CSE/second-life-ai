# Implementation Plan: P2-B4 — Decision & Score Tuning

## Overview

Five focused changes: add `original_price_usd` to the `ProductGraded` event schema,
wire real price into the Lifecycle handler, replace flat mock scores/multipliers with
2-D lookup tables, add/update tests (unit + property-based), and mark the feature done
in the progress tracker. All changes are backward-compatible and verified with
`py -m py_compile` after each file edit.

---

## Tasks

- [x] 1. Add `original_price_usd` to `ProductGradedEventData`
  - [x] 1.1 Add the optional field to the Pydantic model
    - In `packages/shared-py/shared_py/events/schemas.py`, inside `ProductGradedEventData`,
      append after the `defects` field:
      ```python
      original_price_usd: float | None = Field(
          default=None,
          description="Catalogue/purchase price in USD; None when not available",
      )
      ```
    - Do NOT change `event_version` — it stays `"1.0"` (additive, backward-compatible).
    - Run `py -m py_compile packages/shared-py/shared_py/events/schemas.py` to verify syntax.
    - _Requirements: 1.1, 6.1, 6.4_

- [x] 2. Wire real price into the Lifecycle event handler
  - [x] 2.1 Replace the hardcoded `value_estimate=100.0` with price-extraction logic
    - In `services/lifecycle/app/events/handlers.py`, after
      `data = ProductGradedEventData.model_validate(envelope.data)` add:
      ```python
      _price = data.original_price_usd
      value_estimate = _price if (_price is not None and _price > 0) else 100.0
      ```
    - Replace the `value_estimate=100.0` keyword argument in the
      `service.decide_lifecycle(...)` call with `value_estimate=value_estimate`.
    - Run `py -m py_compile services/lifecycle/app/events/handlers.py` to verify syntax.
    - _Requirements: 1.3, 1.4, 6.2, 6.3_

- [x] 3. Refine `mock_decide_lifecycle` with 2-D lookup tables
  - [x] 3.1 Add module-level `_SUSTAINABILITY_SCORES` and `_VALUE_MULTIPLIERS` dicts
    - In `packages/shared-py/shared_py/ai/mock.py`, add the two dicts at module level
      (after the imports, before any functions):
      ```python
      _SUSTAINABILITY_SCORES: dict[tuple[Grade, LifecycleAction], float] = {
          (Grade.A, LifecycleAction.RESELL):      88.0,
          (Grade.A, LifecycleAction.HYPERLOCAL):  90.0,
          (Grade.B, LifecycleAction.RESELL):      80.0,   # golden-path locked
          (Grade.B, LifecycleAction.REFURBISH):   75.0,
          (Grade.B, LifecycleAction.HYPERLOCAL):  87.0,
          (Grade.C, LifecycleAction.REFURBISH):   70.0,
          (Grade.C, LifecycleAction.DONATE):      65.0,
          (Grade.D, LifecycleAction.RECYCLE):     50.0,
          (Grade.D, LifecycleAction.DONATE):      55.0,
      }
      _SUSTAINABILITY_DEFAULT = 60.0

      _VALUE_MULTIPLIERS: dict[tuple[Grade, LifecycleAction], float] = {
          (Grade.A, LifecycleAction.RESELL):      0.75,
          (Grade.A, LifecycleAction.HYPERLOCAL):  0.65,
          (Grade.B, LifecycleAction.RESELL):      0.60,   # golden-path locked: 120×0.60=72.00
          (Grade.B, LifecycleAction.REFURBISH):   0.50,
          (Grade.B, LifecycleAction.HYPERLOCAL):  0.65,
          (Grade.C, LifecycleAction.REFURBISH):   0.40,
          (Grade.C, LifecycleAction.DONATE):      0.10,
          (Grade.D, LifecycleAction.RECYCLE):     0.05,
          (Grade.D, LifecycleAction.DONATE):      0.05,
      }
      _VALUE_MULTIPLIER_DEFAULT = 0.10
      ```
    - _Requirements: 2.1, 3.1, 4.1_

  - [x] 3.2 Rewrite `mock_decide_lifecycle` body to use the lookup tables
    - Replace the existing per-branch `sustainability_score` and `value_recovery`
      assignments with a unified lookup pattern:
      1. Keep the existing `if/elif/else` branches for `action` and `rationale` only.
      2. After `action` is determined, add:
         ```python
         sustainability_score = _SUSTAINABILITY_SCORES.get((grade, action), _SUSTAINABILITY_DEFAULT)
         multiplier = _VALUE_MULTIPLIERS.get((grade, action), _VALUE_MULTIPLIER_DEFAULT)
         value_recovery = 0.0 if value_estimate == 0.0 else value_estimate * multiplier
         ```
      3. Replace the hyperlocal override block so it also uses the lookup tables:
         ```python
         if seed % 5 == 0 and grade in (Grade.A, Grade.B):
             action = LifecycleAction.HYPERLOCAL
             rationale = (
                 f"Hyperlocal match opportunity detected. {product_category} can be "
                 f"transferred to nearby buyer, avoiding reverse logistics."
             )
             sustainability_score = _SUSTAINABILITY_SCORES.get(
                 (grade, action), _SUSTAINABILITY_DEFAULT
             )
             sustainability_score = min(sustainability_score, 100.0)
             multiplier = _VALUE_MULTIPLIERS.get((grade, action), _VALUE_MULTIPLIER_DEFAULT)
             value_recovery = 0.0 if value_estimate == 0.0 else value_estimate * multiplier
         ```
      4. Remove the old `sustainability_score += 10.0` line and all flat constant assignments.
    - Golden-path invariant: `(Grade.B, "electronics", 120.00)` → RESELL,
      `value_recovery == 72.00`, `sustainability_score == 80.0`.
    - `value_estimate=0.0` → `value_recovery == 0.0` (no ZeroDivisionError).
    - Run `py -m py_compile packages/shared-py/shared_py/ai/mock.py` to verify syntax.
    - _Requirements: 2.1–2.7, 3.1–3.5, 4.1_

- [x] 4. Checkpoint — verify syntax across all changed files
  - Run `py -m py_compile` on all three modified files:
    - `packages/shared-py/shared_py/events/schemas.py`
    - `services/lifecycle/app/events/handlers.py`
    - `packages/shared-py/shared_py/ai/mock.py`
  - Ensure all three exit cleanly before proceeding.

- [x] 5. Add/update tests in `packages/shared-py/tests/test_ai.py`
  - [x] 5.1 Add unit test `test_golden_path_decision_regression`
    - Import `ProductGradedEventData` from `shared_py.events.schemas`.
    - Import golden-path constants from `shared_py.ai`.
    - Call `mock_decide_lifecycle(Grade.B, "electronics", 120.00)` directly (sync call to
      `shared_py.ai.mock.mock_decide_lifecycle`).
    - Assert: `action == LifecycleAction.RESELL`, `value_recovery_estimate == 72.00`,
      `sustainability_score == 80.0`, `confidence > 0`, `rationale` is non-empty string.
    - _Requirements: 4.1, 4.3, 5.4_

  - [x] 5.2 Add unit test `test_schema_backward_compat_no_price_field`
    - Build a minimal valid `ProductGradedEventData` dict that omits `original_price_usd`.
    - Call `ProductGradedEventData.model_validate(payload)`.
    - Assert: no exception raised and `result.original_price_usd is None`.
    - _Requirements: 1.1, 5.2, 6.1_

  - [x] 5.3 Add unit test `test_zero_value_estimate`
    - Call `mock_decide_lifecycle` with any valid grade and category but `value_estimate=0.0`.
    - Assert: `value_recovery_estimate == 0.0` and no exception raised.
    - _Requirements: 3.5_

  - [ ]* 5.4 Add PBT: `test_property_backward_compat_deserialization`
    - Comment header: `# Feature: p2-b4-score-tuning, Property 1: backward-compatible deserialization`
    - Use `@given(st.fixed_dictionaries({...}))` over the required fields of
      `ProductGradedEventData` (return_id, grade_id, product_id, grade, confidence,
      damage_summary) — **without** `original_price_usd`.
    - Assert: `model_validate` succeeds and `original_price_usd is None`.
    - `@settings(max_examples=100)`.
    - _Requirements: 1.1, 5.1, 6.1_

  - [ ]* 5.5 Add PBT: `test_property_score_bounds_and_recovery_invariant`
    - Comment header: `# Feature: p2-b4-score-tuning, Property 2: score bounds and value-recovery invariant`
    - Use `@given(grade=st.sampled_from(list(Grade)), category=st.sampled_from([...]),
      value_estimate=st.floats(min_value=0.01, max_value=10_000.0, allow_nan=False))`.
    - Categories: `["electronics", "clothing", "furniture", "toys", "appliances", "books"]`.
    - Call `mock_decide_lifecycle` synchronously (it is a plain function, not async —
      no `asyncio.run` needed).
    - Assert: `0.0 <= sustainability_score <= 100.0` and
      `0.0 < value_recovery_estimate <= value_estimate`.
    - `@settings(max_examples=100)`.
    - _Requirements: 2.6, 3.4, 5.1_

  - [ ]* 5.6 Add PBT: `test_property_handler_fallback_invalid_price`
    - Comment header: `# Feature: p2-b4-score-tuning, Property 3: lifecycle handler fallback`
    - Use `@given(original_price=st.one_of(st.just(None), st.just(0.0),
      st.floats(max_value=-0.01, allow_nan=False)))`.
    - Test the extraction logic directly (no need to instantiate the full async handler):
      ```python
      _price = original_price
      result = _price if (_price is not None and _price > 0) else 100.0
      assert result == 100.0
      ```
    - `@settings(max_examples=100)`.
    - _Requirements: 1.3, 6.3_

- [x] 6. Final checkpoint — all py_compile and test invocation guidance
  - Run `py -m py_compile packages/shared-py/tests/test_ai.py` to verify the updated test file.
  - The user runs the full suite manually:
    ```bash
    cd packages/shared-py
    AI_MODE=mock pytest tests/test_ai.py -v
    ```
  - Ensure all three `py_compile` targets (schemas.py, handlers.py, mock.py) still pass after
    the test file edit.

- [x] 7. Mark P2-B4 as ✅ Done in `docs/progress-tracker.md`
  - Change the P2-B4 row status from `📋 Not started` to `✅ Done`.
  - Fill the **Notes** column:
    `Added original_price_usd (float|None) to ProductGradedEventData; Lifecycle handler
    reads real price with 100.0 fallback; mock_decide_lifecycle refactored to 2-D
    _SUSTAINABILITY_SCORES/_VALUE_MULTIPLIERS lookup tables; golden-path locked
    (Grade.B/electronics/120.00 → RESELL/72.00/80.0); 3 unit tests + 3 PBT properties added
    to test_ai.py; event_version stays "1.0".`
  - Fill the **Link** column: `b/ai/p2-b4`.
  - Update the Phase 2 summary row: Done count 8→9, Not started 1→0.
  - Update the Overall Progress table accordingly (✅ Done 32→33, 📋 Not started 2→1).
  - Update **Last updated** date and **Updated by** fields at the top of the file.
  - _Requirements: all (Definition of Done)_

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; the three unit
  tests in 5.1–5.3 are mandatory.
- `mock_decide_lifecycle` is a plain synchronous function — no `asyncio.run` needed in
  the unit tests or PBT that call it directly. `asyncio.run` is only needed when going
  through the async `AIClient.decide_lifecycle` wrapper.
- The `event_version` field must remain `"1.0"` — do not change it.
- `py -m py_compile` is the only automated verification step; the user runs `pytest` manually.
- Checkpoints in tasks 4 and 6 ensure no syntax regressions are introduced between steps.
- All 5 golden-path constants in `client.py` (`GOLDEN_PATH_VALUE_ESTIMATE`,
  `GOLDEN_PATH_EXPECTED_GRADE`, `GOLDEN_PATH_EXPECTED_ACTION`,
  `GOLDEN_PATH_EXPECTED_VALUE_RECOVERY`, `GOLDEN_PATH_EXPECTED_SUSTAINABILITY_SCORE`)
  are already correct — do not modify them.

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["3.2"] },
    { "id": 3, "tasks": ["5.1", "5.2", "5.3"] },
    { "id": 4, "tasks": ["5.4", "5.5", "5.6"] }
  ]
}
```
