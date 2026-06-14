"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

import { useAuth } from "@/lib/auth-context"
import { useReturns } from "@/hooks/use-returns"
import { useSustainabilityMetrics } from "@/hooks/use-sustainability-metrics"
import { ProfileCard } from "@/components/features/ProfileCard"
import { ActiveReturnsList } from "@/components/features/ActiveReturnsList"
import { SustainabilitySummary } from "@/components/features/SustainabilitySummary"
import { PageHeader } from "@/components/features/PageHeader"
import { ErrorState } from "@/components/features/ErrorState"
import { Skeleton } from "@/components/ui/Skeleton"

/**
 * DashboardPage — authenticated landing page at `/dashboard`.
 *
 * Auth guard: if `user` is null the component immediately pushes to `/login`
 * and returns null so no dashboard content is ever flashed.
 *
 * Both `useReturns` and `useSustainabilityMetrics` are mounted in parallel
 * so their network requests fire concurrently — not sequentially.
 * All hooks are called unconditionally (rules-of-hooks) — the early return
 * for unauthenticated users happens *after* every hook call.
 *
 * Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3
 */
export default function DashboardPage() {
  const { user } = useAuth()
  const router = useRouter()

  // Auth guard — Requirement 1.1, 1.2
  useEffect(() => {
    if (!user) router.push("/login")
  }, [user, router])

  // Both queries mounted unconditionally so hooks order is stable.
  // When user is null these calls are harmless: useReturns has no user
  // dependency and useSustainabilityMetrics accepts undefined userId.
  // Requirement 5.4 — parallel, not sequential.
  const {
    data: returns,
    isLoading: returnsLoading,
    isError: returnsError,
    error: returnsErrorMsg,
    refetch: retryReturns,
  } = useReturns()

  const {
    data: metrics,
    isLoading: metricsLoading,
    isError: metricsError,
    error: metricsErrorMsg,
    refetch: retryMetrics,
  } = useSustainabilityMetrics(user?.id)

  // Return null after all hooks — never renders dashboard content when
  // unauthenticated, consistent with Property 1.
  if (!user) return null

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
      {/* Requirement 6.1 */}
      <PageHeader
        title="Dashboard"
        subtitle={`Welcome back, ${user.display_name}`}
        className="mb-8"
      />

      {/* Responsive grid — Requirement 6.2, 6.3 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Profile — Requirement 3.1 */}
        <div className="lg:col-span-1">
          <ProfileCard user={user} />
        </div>

        {/* Right column: Returns + Sustainability — Requirements 5.1, 5.2, 5.5, 5.6 */}
        <div className="lg:col-span-2 space-y-6">
          {/* Returns section — Requirement 2.1, 5.1, 5.2 */}
          {returnsLoading ? (
            <Skeleton className="h-48 w-full rounded-xl" />
          ) : returnsError ? (
            <ErrorState
              message={returnsErrorMsg?.message ?? "Could not load returns."}
              onRetry={() => retryReturns()}
            />
          ) : (
            <ActiveReturnsList returns={returns!} />
          )}

          {/* Sustainability section — Requirement 3.2, 5.1, 5.2 */}
          {metricsLoading ? (
            <Skeleton className="h-36 w-full rounded-xl" />
          ) : metricsError ? (
            <ErrorState
              message={
                metricsErrorMsg?.message ??
                "Could not load sustainability data."
              }
              onRetry={() => retryMetrics()}
            />
          ) : (
            <SustainabilitySummary totals={metrics!.totals} />
          )}
        </div>
      </div>
    </div>
  )
}
