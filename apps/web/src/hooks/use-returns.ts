"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import type { ReturnResponse } from "../../types/api"

export const RETURNS_QUERY_KEY = ["returns"] as const

/**
 * TanStack Query hook for the user's returns list.
 *
 * Wraps `apiClient.getReturns` in a `useQuery` call. The `refetch` function
 * is the retry control wired into `ErrorState` components (Requirement 5.3).
 *
 * Validates: Requirements 2.1, 5.3
 */
export function useReturns() {
  return useQuery<ReturnResponse[], Error>({
    queryKey: [...RETURNS_QUERY_KEY],
    queryFn: () => apiClient.getReturns(),
    staleTime: 30_000,
    retry: 1,
  })
}
