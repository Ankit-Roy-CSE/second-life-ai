# Implementation Plan: Sustainability Dashboard (P3-C1)

## Overview

This plan implements the `/sustainability` page in `apps/web` (Next.js 14 App Router, TypeScript,
Tailwind, TanStack Query, Zod, Recharts), scoped to Member C / Frontend only. Work proceeds from
foundations outward: first the Chart_Tokens (so chart colors exist before use), then the validation
schema, then the data transport (API client method + mock fixture), then the query hook, then the
presentation components (`StatCardRow`, new `ChartCard`), then the page that wires the async states
together. Property-based tests (fast-check) cover the four correctness properties from the design;
example/integration/smoke tests cover routing, state wiring, and token/registry constraints. The
final step flips the `ChartCard` registry entry to `✅ Built`.

Each task builds on the previous ones and ends with everything wired into the page — no orphaned
code. Implementation language is **TypeScript** (the established stack for `apps/web`).

## Tasks

- [x] 1. Add Chart_Tokens to the token configuration and a typed accessor
  - [x] 1.1 Add `--chart-1 … --chart-6` CSS variables and `chart` Tailwind color mapping
    - Add the six `--chart-1 … --chart-6` HSL CSS variables to `:root` in
      `apps/web/src/app/globals.css`, matching the values in `docs/ui-tokens.md §2.6`
    - Add the `chart: { 1..6: "hsl(var(--chart-N))" }` mapping under `extend.colors` in
      `apps/web/tailwind.config.ts`
    - Use no raw hex literals in components; the hex in comments documents the token source only
    - _Requirements: 7.4_

  - [x] 1.2 Create the ordered `CHART_TOKENS` accessor
    - Create `apps/web/src/lib/chart-tokens.ts` exporting `CHART_TOKENS` as an ordered tuple of
      `"hsl(var(--chart-1))" … "hsl(var(--chart-6))"` for Recharts to consume
    - _Requirements: 3.2, 7.3, 7.4_

  - [ ]* 1.3 Write smoke/static test for Chart_Tokens presence
    - Assert `--chart-1 … --chart-6` appear in `globals.css` and the `chart` mapping appears in
      `tailwind.config.ts`; assert `CHART_TOKENS` has six entries all in `hsl(var(--chart-N))` form
    - _Requirements: 7.4_

- [x] 2. Implement the Metrics_Schema (Zod)
  - [x] 2.1 Create the Zod schema and inferred types
    - Create `apps/web/src/lib/schemas/sustainability.ts` with `LifecycleActionSchema`,
      `BreakdownEntrySchema`, `MetricsTotalsSchema`, and `MetricsSchema` exactly as specified in the
      design (non-negative numbers, non-negative-integer counts/`returns_processed`)
    - Export inferred types `SustainabilityMetrics` and `MetricsBreakdownEntry`
    - Keep the inferred type assignable to the existing `SustainabilityMetricsResponse` interface in
      `apps/web/types/api.ts`
    - _Requirements: 4.4_

  - [ ]* 2.2 Write property test for Metrics_Schema round-trip
    - **Property 1: Metrics schema round-trip**
    - Build a `validMetricsArbitrary` (non-negative numbers, non-negative-integer counts, `action`
      from the LifecycleAction enum, breakdown length 0..N); assert `MetricsSchema.parse(obj)`
      succeeds and deep-equals `obj`; include the Mock_Layer fixture as a case. Min 100 iterations
    - Tag: `// Feature: sustainability-dashboard, Property 1: ...`
    - **Validates: Requirements 4.4, 4.7**

  - [ ]* 2.3 Write property test for malformed-metrics rejection
    - **Property 2: Malformed metrics are rejected and surfaced as errors**
    - Build an `invalidMetricsArbitrary` that corrupts a valid object (drop a required field, swap a
      number for a string, or inject a negative value); assert `MetricsSchema.parse(bad)` throws.
      Min 100 iterations
    - Tag: `// Feature: sustainability-dashboard, Property 2: ...`
    - **Validates: Requirements 4.5**

- [x] 3. Add the API_Client method and Mock_Layer fixture
  - [x] 3.1 Add `getSustainabilityMetrics(userId?)` to the API_Client
    - Add the method to `apps/web/src/lib/api-client.ts` without disturbing existing methods
    - Mock path: when `NEXT_PUBLIC_USE_MOCKS !== "false"`, return
      `MetricsSchema.parse(MOCKS.sustainabilityMetrics)`
    - Live path: `GET ${API_BASE_URL}/sustainability/metrics?user_id=...` (encode `user_id`), throw
      `Error("Failed to fetch sustainability metrics")` on non-2xx, then `MetricsSchema.parse(json)`
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 4.6_

  - [x] 3.2 Add the Mock_Layer fixture
    - Add `MOCKS.sustainabilityMetrics` in `apps/web/src/lib/api-client.ts` with the totals and a
      non-empty five-entry `breakdown` (RESELL, REFURBISH, DONATE, RECYCLE, HYPERLOCAL) from the
      design, so the demo chart is populated and the fixture conforms to `Metrics_Schema`
    - _Requirements: 4.6, 4.7_

  - [ ]* 3.3 Write integration test for the live request shape
    - With mocks disabled and `fetch` mocked, assert `getSustainabilityMetrics("u1")` calls
      `GET {API_BASE_URL}/sustainability/metrics?user_id=u1` and parses the response
    - _Requirements: 4.1, 4.2_

  - [ ]* 3.4 Write example test for the mock path
    - With mocks enabled, assert `getSustainabilityMetrics()` resolves to the fixture and that the
      result parses cleanly through `MetricsSchema`
    - _Requirements: 4.6_

- [x] 4. Implement the Dashboard_Query hook
  - [x] 4.1 Create `useSustainabilityMetrics`
    - Create `apps/web/src/hooks/use-sustainability-metrics.ts` (`"use client"`) wrapping
      `apiClient.getSustainabilityMetrics(userId)` in `useQuery` with `SUSTAINABILITY_METRICS_KEY`,
      `staleTime: 30_000`, `retry: 1`; expose `data/isLoading/isError/error/refetch`
    - A `ZodError` thrown in the client propagates as a rejected query (`isError === true`)
    - _Requirements: 4.4, 4.5, 5.3_

- [x] 5. Implement the StatCard_Row
  - [x] 5.1 Create `StatCardRow` reusing the existing StatCard
    - Create `apps/web/src/components/features/StatCardRow.tsx` that maps the four Headline_Metrics
      (CO₂ avoided, waste diverted, value recovered, green credits) onto the existing `StatCard`
      component — do not reimplement the metric tile
    - Pass `unit="kg"` to the two mass tiles; format every value with `formatNumber` from
      `lib/utils`; source all spacing/typography from token-based Tailwind classes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 7.1, 7.2_

  - [ ]* 5.2 Write property test for StatCard_Row totals mapping
    - **Property 3: StatCard_Row reflects totals formatted with formatNumber**
    - Render `StatCardRow` with generated valid `totals`; assert one tile per Headline_Metric and
      each displayed value equals `formatNumber(field)`. Min 100 iterations
    - Tag: `// Feature: sustainability-dashboard, Property 3: ...`
    - **Validates: Requirements 2.3, 2.5**

  - [ ]* 5.3 Write example tests for StatCard_Row structure
    - Assert exactly four tiles with the correct labels render, the two mass tiles carry `unit="kg"`,
      and the component imports/reuses `StatCard`
    - _Requirements: 2.1, 2.2, 2.4_

- [x] 6. Implement the new ChartCard component
  - [x] 6.1 Create `ChartCard` with Recharts and its own async states
    - Create `apps/web/src/components/features/ChartCard.tsx` (`"use client"`) implementing the
      `ChartCardProps` contract (`title`, `description?`, `breakdown`, `isLoading?`, `isError?`,
      `onRetry?`)
    - Always render the title; render the description beneath it only when provided
    - Branch: `isLoading` → `Skeleton`; `isError` → `ErrorState` with `onRetry`; empty `breakdown` →
      `EmptyState`; otherwise a Recharts `BarChart` with one `Cell` per breakdown entry colored from
      `CHART_TOKENS[i % CHART_TOKENS.length]`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.4, 7.3_

  - [ ]* 6.2 Write property test for ChartCard datum count
    - **Property 4: ChartCard renders one datum per breakdown entry**
    - Render `ChartCard` with generated `breakdown`; assert rendered datum count equals
      `breakdown.length`, and that an `EmptyState` (and no chart data points) renders iff the array
      is empty. Min 100 iterations
    - Tag: `// Feature: sustainability-dashboard, Property 4: ...`
    - **Validates: Requirements 3.3, 5.4**

  - [ ]* 6.3 Write example tests for ChartCard presentation and tokens
    - Assert title always shows and description shows only when provided; assert `Cell` fills come
      from `CHART_TOKENS` and no raw hex appears in the file
    - _Requirements: 3.2, 3.4, 3.5, 7.3_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Wire the Sustainability page and async states
  - [x] 8.1 Create the `/sustainability` page composing all pieces
    - Create `apps/web/src/app/sustainability/page.tsx` (`"use client"`) rendering `PageHeader`
      (title + subtitle) within the existing app shell layout, then branching on the
      `useSustainabilityMetrics` result: loading → `Skeleton` placeholders; error → `ErrorState`
      with retry wired to `refetch()`; success → `StatCardRow` (from `totals`) + `ChartCard` (from
      `breakdown`)
    - Obtain all data only through `useSustainabilityMetrics`/`apiClient`; reference no backend
      service ports directly; use only token-based Tailwind classes
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.3, 5.1, 5.2, 5.3, 5.5, 6.1, 7.1, 7.2_

  - [ ]* 8.2 Write example tests for routing and async-state wiring
    - Assert the route renders `PageHeader` title + subtitle; loading shows `Skeleton`; error shows
      `ErrorState` and activating retry calls `refetch`; success renders the row + chart
    - _Requirements: 1.1, 1.2, 5.1, 5.2, 5.3, 5.5_

  - [ ]* 8.3 Write smoke/static checks for boundaries and tokens
    - Assert the page imports data only via `apiClient` (no backend service ports), and that the new
      files contain no raw hex/px (colors/spacing/typography via tokens)
    - _Requirements: 4.3, 6.1, 7.1, 7.2_

- [x] 9. Update the Component Registry
  - [x] 9.1 Flip the ChartCard registry entry to Built
    - In `docs/ui-registry.md`, change the `ChartCard` entry from `📋 Planned` to `✅ Built`,
      recording path (`apps/web/src/components/features/ChartCard.tsx`), final props (`title`,
      `description?`, `breakdown`, `isLoading?`, `isError?`, `onRetry?`), tokens used
      (`Card`, `chart-1..6`), and dependencies (Card, recharts, Skeleton, EmptyState, ErrorState);
      update the registry status summary counts
    - _Requirements: 6.2, 6.3_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP.
- Each task references specific requirements (granular sub-requirement clauses) for traceability.
- Checkpoints ensure incremental validation.
- Property tests (fast-check, min 100 iterations each) validate the four universal correctness
  properties from the design; example/integration/smoke tests validate routing, state wiring, and
  token/registry constraints.
- Run the test runner single-pass (e.g. `vitest --run` / `jest`), never watch mode.
- Implementation language is TypeScript, per the `apps/web` stack.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1"] },
    { "id": 1, "tasks": ["1.3", "2.2", "2.3", "3.1", "5.1", "6.1"] },
    { "id": 2, "tasks": ["3.2", "4.1", "5.2", "5.3", "6.2", "6.3"] },
    { "id": 3, "tasks": ["3.3", "3.4", "8.1"] },
    { "id": 4, "tasks": ["8.2", "8.3", "9.1"] }
  ]
}
```
