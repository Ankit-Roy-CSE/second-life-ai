"use client"

import React, { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { PageHeader } from "@/components/features/PageHeader"
import { PassportTimeline } from "@/components/features/PassportTimeline"
import { Skeleton } from "@/components/ui/Skeleton"
import { ErrorState } from "@/components/features/ErrorState"
import { EmptyState } from "@/components/features/EmptyState"
import { apiClient } from "@/lib/api-client"
import { PassportResponse, PassportTimelineEntry } from "../../../../types/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { GradeBadge } from "@/components/ui/GradeBadge"
import { FileSearch } from "lucide-react"

/**
 * Build a display timeline from passport fields when the backend does not
 * supply an explicit `timeline` array (live mode returns flat fields).
 */
function buildTimeline(passport: PassportResponse): PassportTimelineEntry[] {
  if (passport.timeline && passport.timeline.length > 0) {
    return passport.timeline
  }

  const entries: PassportTimelineEntry[] = []
  const created = passport.created_at || new Date().toISOString()

  entries.push({
    event: "Return Submitted",
    timestamp: created,
    details: { return_id: passport.return_id },
  })

  if (passport.current_grade) {
    entries.push({
      event: "AI Grading Completed",
      timestamp: created,
      details: {
        grade: passport.current_grade,
        ...(passport.grade_confidence != null
          ? { confidence: `${Math.round(passport.grade_confidence * 100)}%` }
          : {}),
      },
    })
  }

  if (passport.lifecycle_action) {
    entries.push({
      event: "Lifecycle Decision Made",
      timestamp: created,
      details: {
        action: passport.lifecycle_action,
        ...(passport.value_recovery_estimate != null
          ? { value_recovery: `$${passport.value_recovery_estimate.toFixed(2)}` }
          : {}),
      },
    })
  }

  entries.push({
    event: "Digital Passport Created",
    timestamp: created,
    details: { passport_id: passport.id },
  })

  return entries
}

export default function PassportPage() {
  const params = useParams()
  const passportId = params.id as string

  const [passport, setPassport] = useState<PassportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPassport = React.useCallback(async () => {
    if (!passportId) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.getPassport(passportId)
      setPassport(data)
    } catch (error: unknown) {
      const err = error as Error
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [passportId])

  useEffect(() => {
    fetchPassport()
  }, [fetchPassport])

  if (loading) {
    return (
      <div className="container mx-auto py-8 max-w-screen-xl px-4 space-y-8">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 max-w-screen-xl px-4">
        <ErrorState message={error} onRetry={fetchPassport} />
      </div>
    )
  }

  if (!passport) {
    return (
      <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
        <PageHeader title="Digital Product Passport" subtitle="" />
        <EmptyState
          icon={FileSearch}
          title="No passport found"
          description="We couldn't find passport details for this product."
        />
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6 space-y-8">
      <PageHeader 
        title="Digital Product Passport" 
        subtitle={`Passport ID: ${passport.id}`}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1">
          <CardHeader className="bg-secondary text-secondary-foreground rounded-t-lg">
            <CardTitle>Product Identity</CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-5">
            <div>
              <span className="block text-sm text-muted-foreground font-semibold">Product ID</span>
              <span className="font-mono text-foreground text-sm">{passport.product_id}</span>
            </div>
            <div>
              <span className="block text-sm text-muted-foreground font-semibold">Return ID</span>
              <span className="font-mono text-foreground text-sm">{passport.return_id}</span>
            </div>
            <div>
              <span className="block text-sm text-muted-foreground font-semibold mb-1">Current Grade</span>
              <GradeBadge grade={passport.current_grade} showLabel size="md" />
            </div>
            {passport.lifecycle_action && (
              <div>
                <span className="block text-sm text-muted-foreground font-semibold">Lifecycle Action</span>
                <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-bold text-primary ring-1 ring-inset ring-primary/20 uppercase">
                  {passport.lifecycle_action}
                </span>
              </div>
            )}
            {passport.value_recovery_estimate != null && (
              <div>
                <span className="block text-sm text-muted-foreground font-semibold">Value Recovery</span>
                <span className="text-lg font-bold text-foreground">${passport.value_recovery_estimate.toFixed(2)}</span>
              </div>
            )}
            {passport.sustainability_score != null && (
              <div>
                <span className="block text-sm text-muted-foreground font-semibold">Sustainability Score</span>
                <span className="text-lg font-bold text-green-600">{passport.sustainability_score}/100</span>
              </div>
            )}
            <div>
              <span className="block text-sm text-muted-foreground font-semibold">Status</span>
              <span className="inline-flex items-center rounded-md bg-accent px-2 py-1 text-xs font-medium text-accent-foreground ring-1 ring-inset ring-accent/20 capitalize">
                {passport.status.toLowerCase()}
              </span>
            </div>
            {passport.sustainability && (passport.sustainability.co2_avoided_kg || passport.sustainability.waste_diverted_kg) && (
              <div className="pt-3 border-t border-border space-y-2">
                <span className="block text-sm text-muted-foreground font-semibold">Environmental Impact</span>
                {passport.sustainability.co2_avoided_kg && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">CO₂ Avoided</span>
                    <span className="font-semibold text-green-600">{passport.sustainability.co2_avoided_kg} kg</span>
                  </div>
                )}
                {passport.sustainability.waste_diverted_kg && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Waste Diverted</span>
                    <span className="font-semibold text-green-600">{passport.sustainability.waste_diverted_kg} kg</span>
                  </div>
                )}
              </div>
            )}
            <div className="pt-3 border-t border-border">
              <span className="block text-sm text-muted-foreground font-semibold">Created</span>
              <span className="text-sm text-foreground">{new Date(passport.created_at).toLocaleDateString()}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Lifecycle History</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <PassportTimeline events={buildTimeline(passport)} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
