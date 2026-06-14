# Requirements Document

## Introduction

Task **P3-B2 — Golden-path demo product + AI fallback test** is the final AI-layer task that
locks in the judge demo. The full 10-event saga (ReturnSubmitted → ProductGraded →
LifecycleDecisionCreated → PassportCreated → HyperlocalMatchRequested → MatchFound →
ProductListed → PurchaseCompleted → SustainabilityUpdated) already works (CP2 verified) and the
shared AI wrapper (`packages/shared-py/shared_py/ai/`) already supports deterministic `mock` mode
seeded from `hash(media_key)` plus `aws`/`hybrid` modes with graceful fallback to mock.

This feature does **not** add new service code. It is a demo-safety, test-and-lock-in task whose
purpose is to guarantee two things before the demo:

1. **Determinism** — the golden-path demo product produces the EXACT same
   grade → decision → match → sustainability chain on every run in mock mode, so a regression is
   caught automatically before the judges ever see it.
2. **Fallback safety** — when AWS keys are absent or `AI_MODE=aws`/`hybrid` is selected but
   Bedrock/Rekognition are unreachable, the wrapper silently degrades to mock and the golden-path
   demo still completes with no crash, no 500, and no saga stall.

The deliverables live in the shared-py AI package tests (`packages/shared-py/tests/`) and a small
set of locked golden-path constants (extending the existing
`GOLDEN_PATH_MEDIA_KEY` / `GOLDEN_PATH_CATEGORY` / `GOLDEN_PATH_REASON`), with optional
reinforcement in `scripts/seed_min.py`.

Scope guardrails (from the build plan and AGENTS.md):
- This is a hackathon demo-safety task, **not** production hardening.
- All AI access stays behind the shared wrapper; no `import boto3` outside `packages/shared-py/ai`.
- The `AI_MODE=mock` path must work keyless and offline.
- Determinism is the core correctness property; the locked chain must not vary between runs.

### Known fact established during analysis (drives Requirement 1)

The golden-path media key `products/golden-path/demo-headphones-001.jpg` hashes to mock bucket
**57**, which maps to **Grade B**. The hyperlocal-override seed for `Grade.B` + `electronics`
is mod-5 = 4 (no override). Therefore the locked lifecycle action is **RESELL** *only when the
value estimate passed to `decide_lifecycle` is greater than 50*; at a value of 50 or below the
mock returns **REFURBISH**. `context/AI.md` §12 documents the intended result as
"Grade B → RESELL", so the golden-path value estimate MUST be pinned above the RESELL threshold.

## Glossary

- **AI_Wrapper**: The shared AI client singleton `ai_client` and the `AIClient` class in
  `packages/shared-py/shared_py/ai/client.py`. The only seam through which services obtain AI
  results.
- **Mock_AI_Engine**: The deterministic, network-free implementation in
  `packages/shared-py/shared_py/ai/mock.py`, seeded from `hash(media_key)` (falling back to
  `hash(reason:category)` when no media key is present).
- **Golden_Path_Product**: The locked demo product — the seeded headphones whose media key is
  `GOLDEN_PATH_MEDIA_KEY` — used in the judge demo walkthrough.
- **Golden_Path_Chain**: The ordered, locked sequence of AI-layer outputs for the
  Golden_Path_Product: grade result → lifecycle decision → match rationale → derived
  sustainability inputs.
- **Golden_Path_Constants**: The named constants that pin the Golden_Path_Product inputs and the
  expected Golden_Path_Chain outputs (media key, category, reason, value estimate, expected grade,
  expected action, expected sustainability score, match distance/interests).
- **Golden_Path_Test**: The automated regression test that asserts the Golden_Path_Product produces
  the exact expected Golden_Path_Chain.
- **Fallback_Test**: The automated test that verifies graceful degradation to mock when AWS is
  selected but unavailable.
- **Grade**: Product condition enum value (A, B, C, D) defined in `shared_py.schemas.enums.Grade`.
- **Lifecycle_Action**: Decision enum value (RESELL, REFURBISH, DONATE, RECYCLE, HYPERLOCAL)
  defined in `shared_py.schemas.enums.LifecycleAction`.
- **AI_MODE**: Environment variable selecting the AI backend: `mock` (default, keyless), `aws`,
  or `hybrid`.
- **Sustainability_Inputs**: The deterministic AI-layer outputs that feed the downstream
  Sustainability Service — `value_recovery_estimate` and `sustainability_score` from the lifecycle
  decision, and `logistics_benefit` from the match rationale.

## Requirements

### Requirement 1: Locked golden-path constants

**User Story:** As Member B preparing the demo, I want the golden-path inputs and expected outputs
captured as named constants, so that the demo product's grade, decision, match, and sustainability
values are pinned in one place and cannot drift silently.

#### Acceptance Criteria

1. THE Golden_Path_Constants SHALL define the existing input constants `GOLDEN_PATH_MEDIA_KEY`,
   `GOLDEN_PATH_CATEGORY`, and `GOLDEN_PATH_REASON` with their current values.
2. THE Golden_Path_Constants SHALL define a golden-path value estimate constant whose value is
   greater than 50.0 United States dollars.
3. THE Golden_Path_Constants SHALL define the expected grade for the Golden_Path_Product as
   `Grade.B`.
4. THE Golden_Path_Constants SHALL define the expected Lifecycle_Action for the Golden_Path_Product
   as `LifecycleAction.RESELL`.
5. THE Golden_Path_Constants SHALL define the expected match buyer distance in kilometers and the
   expected match buyer interests used to compute the locked match rationale.
6. WHERE a Golden_Path_Constant expresses a floating-point value, THE Golden_Path_Constants SHALL
   express the value as a literal constant rather than a runtime computation.

### Requirement 2: Deterministic golden-path grade

**User Story:** As Member B, I want the golden-path grade to be reproducible, so that the AI grade
shown to judges is identical on every demo run.

#### Acceptance Criteria

1. WHEN the AI_Wrapper grades the Golden_Path_Product in mock mode, THE AI_Wrapper SHALL return
   grade `Grade.B`.
2. WHEN the AI_Wrapper grades the Golden_Path_Product in mock mode two or more times within a run,
   THE AI_Wrapper SHALL return identical grade, confidence, defect count, and damage summary text
   on each call.
3. WHEN the AI_Wrapper grades the Golden_Path_Product in mock mode, THE AI_Wrapper SHALL return a
   confidence value within the closed interval 0.0 to 1.0.
4. THE Mock_AI_Engine SHALL derive the golden-path grade solely from the Golden_Path_Product input
   constants, independent of process, machine, or invocation order.

### Requirement 3: Deterministic golden-path lifecycle decision

**User Story:** As Member B, I want the golden-path lifecycle decision to be reproducible, so that
the "Resell" recommendation and its value-recovery estimate shown to judges never change.

#### Acceptance Criteria

1. WHEN the AI_Wrapper decides the lifecycle for grade `Grade.B`, category `electronics`, and the
   golden-path value estimate in mock mode, THE AI_Wrapper SHALL return Lifecycle_Action
   `LifecycleAction.RESELL`.
2. WHEN the AI_Wrapper decides the golden-path lifecycle in mock mode two or more times within a
   run, THE AI_Wrapper SHALL return identical action, value-recovery estimate, sustainability
   score, and rationale text on each call.
3. WHEN the AI_Wrapper decides the golden-path lifecycle in mock mode, THE AI_Wrapper SHALL return
   a value-recovery estimate greater than 0.0 United States dollars.
4. WHEN the AI_Wrapper decides the golden-path lifecycle in mock mode, THE AI_Wrapper SHALL return
   a sustainability score within the closed interval 0.0 to 100.0.

### Requirement 4: Deterministic golden-path match rationale

**User Story:** As Member B, I want the golden-path hyperlocal match to be reproducible, so that
the nearby-buyer match and its logistics savings shown to judges are stable.

#### Acceptance Criteria

1. WHEN the AI_Wrapper generates a match rationale for the golden-path match distance, interests,
   category, and score in mock mode, THE AI_Wrapper SHALL return a non-empty rationale text and a
   non-empty logistics benefit string.
2. WHEN the AI_Wrapper generates the golden-path match rationale in mock mode two or more times
   within a run, THE AI_Wrapper SHALL return identical text, key factors, and logistics benefit on
   each call.
3. WHERE the golden-path match buyer distance is less than 5.0 kilometers, THE AI_Wrapper SHALL
   include the value `85%` in the logistics benefit string.

### Requirement 5: Golden-path chain regression test

**User Story:** As Member B, I want one automated test that asserts the entire golden-path chain,
so that any regression in grade, decision, match, or sustainability is caught before the demo.

#### Acceptance Criteria

1. THE Golden_Path_Test SHALL assert that the Golden_Path_Chain grade equals the expected grade
   constant.
2. THE Golden_Path_Test SHALL assert that the Golden_Path_Chain lifecycle action equals the
   expected Lifecycle_Action constant.
3. THE Golden_Path_Test SHALL assert that the Golden_Path_Chain match rationale produces a
   non-empty logistics benefit.
4. THE Golden_Path_Test SHALL assert that the Sustainability_Inputs (value-recovery estimate and
   sustainability score) match the locked expected values.
5. WHEN the Golden_Path_Test runs with `AI_MODE=mock` and no AWS credentials present, THE
   Golden_Path_Test SHALL pass.
6. IF any link in the Golden_Path_Chain produces a value other than its locked expected value,
   THEN THE Golden_Path_Test SHALL fail with an assertion identifying the diverging link.

### Requirement 6: Fallback to mock when AWS is selected but unavailable

**User Story:** As Member B, I want the demo to survive missing or unreachable AWS, so that the
golden-path runs even if `AI_MODE=aws` is set without working credentials.

#### Acceptance Criteria

1. WHEN the AI_Wrapper is constructed with `AIMode.AWS` and AWS clients cannot be initialized,
   THE AI_Wrapper SHALL set its active mode to `AIMode.MOCK`.
2. WHEN the AI_Wrapper grades the Golden_Path_Product with `AIMode.AWS` selected and AWS
   unreachable, THE AI_Wrapper SHALL return the same grade as the mock golden-path grade.
3. IF a real AWS call raises an error during grading, decision, or matching, THEN THE AI_Wrapper
   SHALL return a mock result for that call rather than propagating the error to the caller.
4. WHILE AWS is unavailable, THE AI_Wrapper SHALL complete the full Golden_Path_Chain without
   raising an exception.

### Requirement 7: Fallback verification test

**User Story:** As Member B, I want an automated fallback test, so that graceful degradation is
proven and stays proven, not assumed.

#### Acceptance Criteria

1. THE Fallback_Test SHALL exercise the Golden_Path_Chain with `AIMode.AWS` selected while AWS is
   unavailable.
2. THE Fallback_Test SHALL assert that the resulting grade equals the locked golden-path grade.
3. THE Fallback_Test SHALL assert that no exception is raised while completing the chain.
4. THE Fallback_Test SHALL run without requiring AWS credentials or network access.
5. WHERE the Fallback_Test simulates AWS unavailability, THE Fallback_Test SHALL do so by
   inducing AWS client initialization or invocation failure rather than by setting `AIMode.MOCK`
   directly.

### Requirement 8: Seed and documentation alignment

**User Story:** As a teammate running the demo, I want the seed data and documentation to reflect
the locked golden-path values, so that the seeded product matches what the tests assert.

#### Acceptance Criteria

1. THE seed script `scripts/seed_min.py` SHALL reference the Golden_Path_Constants for the
   golden-path product's media key, category, and reason.
2. WHERE the seeded golden-path product carries an original price attribute, THE seed data SHALL
   keep the golden-path value estimate consistent with the locked RESELL decision documented in
   Requirement 3.
3. THE feature SHALL update `docs/progress-tracker.md` to mark task P3-B2 status per the Definition
   of Done in AGENTS.md.

### Requirement 9: Test suite hygiene and keyless execution

**User Story:** As any engineer in the repo, I want the new tests to run cleanly in the existing
suite, so that CI and local runs stay green and keyless.

#### Acceptance Criteria

1. THE Golden_Path_Test and Fallback_Test SHALL reside under `packages/shared-py/tests/`.
2. WHEN the shared-py test suite runs with `AI_MODE=mock` and no AWS credentials, THE Golden_Path_Test
   and Fallback_Test SHALL pass without network access.
3. THE Golden_Path_Test and Fallback_Test SHALL pass `ruff` linting and `black` formatting checks
   configured in `packages/shared-py/pyproject.toml`.
4. IF either test leaves the `AI_MODE` environment variable modified, THEN the test SHALL restore
   the prior value before completing.
