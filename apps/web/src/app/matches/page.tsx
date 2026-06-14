"use client"

import React, { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { useMatches } from "@/hooks/use-matches"
import { MatchCard } from "@/components/features/MatchCard"
import { PageHeader } from "@/components/features/PageHeader"
import { EmptyState } from "@/components/features/EmptyState"
import { ErrorState } from "@/components/features/ErrorState"
import { Skeleton } from "@/components/ui/Skeleton"
import { Search } from "lucide-react"

function MatchesContent() {
  const searchParams = useSearchParams()
  const returnId = searchParams.get("return_id") || "ret_123" // Fallback to mock ID for demo

  const { data: matches = [], isLoading, isError, error, refetch } = useMatches(returnId)

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
      <PageHeader
        title="Hyperlocal Matches"
        subtitle={`Showing nearby buyers interested in this product (Return ID: ${returnId})`}
        className="mb-8"
      />

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
