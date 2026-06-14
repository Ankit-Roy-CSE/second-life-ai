"use client"

import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import type { ListingResponse } from "../../types/api"

/**
 * Async_Data_View hook for the Marketplace route.
 *
 * Wraps `apiClient.getMarketplace` in a TanStack Query `useQuery` call.
 * The query loads all listings once; channel/status filtering is done in
 * memory by `ListingGrid` (Tabs UI), so `refetch` targets the full dataset.
 * `refetch` is the retry control wired into `ErrorState` (Requirement 5.4) —
 * replacing the previous `window.location.reload()` approach.
 *
 * Validates: Requirements 2.1, 2.4, 5.3, 5.4
 */
export function useMarketplaceListings() {
  return useQuery<ListingResponse[], Error>({
    queryKey: ["marketplace", "listings"],
    queryFn: () => apiClient.getMarketplace(),
    staleTime: 30_000,
    retry: 1,
  })
}
