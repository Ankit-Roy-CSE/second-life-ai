"use client"

import React, { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { PageHeader } from "@/components/features/PageHeader"
import { GradePanel } from "@/components/features/GradePanel"
import { DecisionCard } from "@/components/features/DecisionCard"
import { EmptyState } from "@/components/features/EmptyState"
import { Skeleton } from "@/components/ui/Skeleton"
import { ErrorState } from "@/components/features/ErrorState"
import { ClipboardCheck } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { ReturnDetailResponse } from "../../../../types/api"

export default function ReturnDetailPage() {
  const params = useParams()
  const returnId = params.id as string

  const [returnDetail, setReturnDetail] = useState<ReturnDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDetail = React.useCallback(async () => {
    if (!returnId) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.getReturn(returnId)
      setReturnDetail(data)
    } catch (error: unknown) {
      const err = error as Error
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [returnId])

  useEffect(() => {
    fetchDetail()
  }, [fetchDetail])

  if (loading) {
    return (
      <div className="container mx-auto py-8 max-w-screen-xl px-4 space-y-8">
        <Skeleton className="h-12 w-[300px]" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 max-w-screen-xl px-4">
        <ErrorState message={error} onRetry={fetchDetail} />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6 space-y-8">
      <PageHeader 
        title={`Return Details`} 
        subtitle={`ID: ${returnDetail?.id}`}
      />
      
      {returnDetail?.grade ? (
        <GradePanel 
          grade={returnDetail.grade.grade}
          confidence={returnDetail.grade.confidence}
          damageSummary={returnDetail.grade.damage_summary}
          defects={returnDetail.grade.defects}
        />
      ) : (
        <EmptyState
          icon={ClipboardCheck}
          title="Not graded yet"
          description="This return hasn't been graded by the AI inspector yet. Check back shortly."
        />
      )}

      {returnDetail?.decision && (
        <DecisionCard 
          action={returnDetail.decision.action}
          rationale={returnDetail.decision.rationale}
          valueRecovery={returnDetail.decision.value_recovery_estimate}
          sustainabilityScore={returnDetail.decision.sustainability_score}
        />
      )}
    </div>
  )
}
