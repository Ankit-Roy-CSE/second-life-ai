"use client"

import { PageHeader } from "@/components/features/PageHeader"
import { StatCardRow } from "@/components/features/StatCardRow"
import { ChartCard } from "@/components/features/ChartCard"
import { ErrorState } from "@/components/features/ErrorState"
import { Skeleton } from "@/components/ui/Skeleton"
import { useSustainabilityMetrics } from "@/hooks/use-sustainability-metrics"

/**
 * Inline skeleton placeholder shown while the metrics query is loading.
 * Mirrors the rough shape of: 4-tile stat row + chart card.
 *
 * Requirements: 5.1
 */
function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Stat card row skeleton — 4 tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-xl" />
        ))}
      </div>
      {/* Chart card skeleton */}
      <Skeleton className="h-80 w-full rounded-xl" />
    </div>
  )
}

/**
 * SustainabilityPage — `/sustainability` route.
 *
 * Composes PageHeader, StatCardRow, and ChartCard around the
 * useSustainabilityMetrics TanStack Query hook, with full
 * loading / error / success async-state branching.
 *
 * Requirements: 1.1, 1.2, 1.3, 4.1, 4.3, 5.1, 5.2, 5.3, 5.5, 6.1, 7.1, 7.2
 */
export default function SustainabilityPage() {
  const { data, isLoading, isError, error, refetch } = useSustainabilityMetrics()

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
      {/* Always rendered — Requirement 1.2 */}
      <PageHeader
        title="Sustainability Impact"
        subtitle="Cumulative environmental and economic outcomes from processed returns"
        className="mb-8"
      />

      {isLoading ? (
        /* Requirement 5.1 */
        <DashboardSkeleton />
      ) : isError ? (
        /* Requirements 5.2, 5.3 */
        <ErrorState
          message={error?.message ?? "Failed to load sustainability metrics."}
          onRetry={() => refetch()}
        />
      ) : (
        /* Requirement 5.5 */
        <div className="space-y-8">
          <StatCardRow totals={data!.totals} />
          <ChartCard
            title="Impact by lifecycle action"
            description="CO₂ avoided per lifecycle decision across all processed returns"
            breakdown={data!.breakdown}
          />
        </div>
      )}
    </div>
  )
}
