"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import type { SustainabilityMetrics } from "@/lib/schemas/sustainability"

export const SUSTAINABILITY_METRICS_KEY = ["sustainability", "metrics"] as const

/**
 * Dashboard_Query hook for the Sustainability Dashboard.
 *
 * Wraps `apiClient.getSustainabilityMetrics` in a TanStack Query `useQuery`
 * call. The API_Client validates the response through `MetricsSchema` (Zod)
 * before returning, so a `ZodError` on a malformed payload propagates as a
 * rejected query (`isError === true`) — satisfying Requirements 4.4 and 4.5.
 *
 * `refetch` is the retry control wired into `ErrorState` (Requirement 5.3).
 *
 * Validates: Requirements 4.4, 4.5, 5.3
 */
export function useSustainabilityMetrics(userId?: string) {
  return useQuery<SustainabilityMetrics, Error>({
    queryKey: [...SUSTAINABILITY_METRICS_KEY, userId ?? null],
    queryFn: () => apiClient.getSustainabilityMetrics(userId),
    staleTime: 30_000,
    retry: 1,
  })
}
