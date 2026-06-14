"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import type { MatchResponse } from "../../types/api"

/**
 * Async_Data_View hook for the Matches route.
 *
 * Wraps `apiClient.getMatches` in a TanStack Query `useQuery` call.
 * `refetch` is the retry control wired into `ErrorState` (Requirement 5.4) —
 * replacing the previous `window.location.reload()` approach.
 *
 * Validates: Requirements 2.1, 2.4, 5.3, 5.4
 */
export function useMatches(returnId: string) {
  return useQuery<MatchResponse[], Error>({
    queryKey: ["matches", returnId],
    queryFn: () => apiClient.getMatches(returnId),
    staleTime: 30_000,
    retry: 1,
  })
}
