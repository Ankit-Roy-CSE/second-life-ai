/**
 * Zod schemas and inferred types for the Sustainability Dashboard.
 *
 * These schemas validate the Gateway Metrics_Endpoint response
 * (GET /sustainability/metrics?user_id=) before it reaches the UI.
 *
 * The inferred `SustainabilityMetrics` type is structurally assignable to the
 * hand-written `SustainabilityMetricsResponse` interface in `types/api.ts` and
 * supersedes it as the runtime-validated source of truth.
 *
 * Validates: Requirements 4.4, 4.5, 4.7
 */

import { z } from "zod"

// ─── Lifecycle action enum ────────────────────────────────────────────────────
// Mirrors LifecycleAction in types/enums.ts (and packages/shared-py/shared_py/schemas/enums.py).

export const LifecycleActionSchema = z.enum([
  "RESELL",
  "REFURBISH",
  "DONATE",
  "RECYCLE",
  "HYPERLOCAL",
])

// ─── Breakdown entry ──────────────────────────────────────────────────────────
// One row in the per-action breakdown array.

export const BreakdownEntrySchema = z.object({
  action: LifecycleActionSchema,
  count: z.number().int().nonnegative(),
  co2_avoided_kg: z.number().nonnegative(),
  waste_diverted_kg: z.number().nonnegative(),
  value_recovered: z.number().nonnegative(),
})

// ─── Totals ───────────────────────────────────────────────────────────────────
// Aggregate headline metrics across all processed returns.

export const MetricsTotalsSchema = z.object({
  co2_avoided_kg: z.number().nonnegative(),
  waste_diverted_kg: z.number().nonnegative(),
  value_recovered: z.number().nonnegative(),
  green_credits: z.number().nonnegative(),
  returns_processed: z.number().int().nonnegative(),
})

// ─── Top-level metrics schema ─────────────────────────────────────────────────
// Mirrors the full SustainabilityMetricsResponse shape from types/api.ts.

export const MetricsSchema = z.object({
  totals: MetricsTotalsSchema,
  breakdown: z.array(BreakdownEntrySchema),
})

// ─── Inferred types ───────────────────────────────────────────────────────────

/** Parsed, validated sustainability metrics from the Gateway Metrics_Endpoint. */
export type SustainabilityMetrics = z.infer<typeof MetricsSchema>

/** One entry from the per-lifecycle-action breakdown array. */
export type MetricsBreakdownEntry = z.infer<typeof BreakdownEntrySchema>
