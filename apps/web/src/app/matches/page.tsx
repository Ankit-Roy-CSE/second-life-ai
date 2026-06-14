"use client"

import React, { Suspense, useState } from "react"
import { useSearchParams } from "next/navigation"
import { useMatches } from "@/hooks/use-matches"
import { useQuery } from "@tanstack/react-query"
import { MatchCard } from "@/components/features/MatchCard"
import { PageHeader } from "@/components/features/PageHeader"
import { EmptyState } from "@/components/features/EmptyState"
import { ErrorState } from "@/components/features/ErrorState"
import { Skeleton } from "@/components/ui/Skeleton"
import { Search } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import type { ReturnResponse } from "../../../types/api"

function MatchesContent() {
  const searchParams = useSearchParams()
  const initialReturnId = searchParams.get("return_id") || ""

  const [selectedReturnId, setSelectedReturnId] = useState(initialReturnId)

  // Fetch user's returns to populate the filter dropdown
  const { data: returns = [] } = useQuery<ReturnResponse[], Error>({
    queryKey: ["returns"],
    queryFn: () => apiClient.getReturns(),
    staleTime: 60_000,
  })

  // Use first return as default if no selection and returns are loaded
  const activeReturnId = selectedReturnId || (returns.length > 0 ? returns[0].id : "ret_123")

  const { data: matches = [], isLoading, isError, error, refetch } = useMatches(activeReturnId)

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
      <PageHeader
        title="Hyperlocal Matches"
        subtitle="Nearby buyers interested in your returned products"
        className="mb-6"
      />

      {/* Return/Product filter */}
      <div className="mb-8">
        <label htmlFor="return-filter" className="block text-sm font-semibold text-muted-foreground mb-2">
          Filter by Return
        </label>
        <select
          id="return-filter"
          value={activeReturnId}
          onChange={(e) => setSelectedReturnId(e.target.value)}
          className="w-full max-w-md rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {returns.length > 0 ? (
            returns.map((ret) => (
              <option key={ret.id} value={ret.id}>
                {ret.reason} — {ret.product_id.slice(0, 8)}… ({ret.status})
              </option>
            ))
          ) : (
            <option value={activeReturnId}>Return {activeReturnId.slice(0, 8)}…</option>
          )}
        </select>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-48 w-full rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState
          message={error?.message ?? "Failed to load matches."}
          onRetry={() => refetch()}
        />
      ) : matches.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No matches found"
          description="We couldn't find any nearby buyers for this product right now."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in-50 duration-500">
          {matches.map((match) => (
            <MatchCard
              key={match.id}
              buyer={{ name: match.buyer_display_name || "Unknown Buyer" }}
              score={match.score}
              estimatedSavings={match.estimated_savings}
              distanceKm={match.distance_km}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function MatchesPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
        <PageHeader 
          title="Hyperlocal Matches" 
          subtitle="Loading..."
          className="mb-8"
        />
      </div>
    }>
      <MatchesContent />
    </Suspense>
  )
}
