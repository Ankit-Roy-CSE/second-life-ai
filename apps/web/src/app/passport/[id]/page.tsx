"use client"

import React, { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { PageHeader } from "@/components/features/PageHeader"
import { PassportTimeline } from "@/components/features/PassportTimeline"
import { Skeleton } from "@/components/ui/Skeleton"
import { ErrorState } from "@/components/features/ErrorState"
import { apiClient } from "@/lib/api-client"
import { PassportResponse } from "../../../../types/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { GradeBadge } from "@/components/ui/GradeBadge"

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

  if (!passport) return null

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
          <CardContent className="p-6 space-y-4">
            <div>
              <span className="block text-sm text-muted-foreground font-semibold">Product ID</span>
              <span className="font-mono text-foreground">{passport.product_id}</span>
            </div>
            <div>
              <span className="block text-sm text-muted-foreground font-semibold mb-1">Current Grade</span>
              <GradeBadge grade={passport.current_grade} showLabel size="md" />
            </div>
            <div>
              <span className="block text-sm text-muted-foreground font-semibold">Status</span>
              <span className="inline-flex items-center rounded-md bg-accent px-2 py-1 text-xs font-medium text-accent-foreground ring-1 ring-inset ring-accent/20 capitalize">
                {passport.status.toLowerCase()}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Lifecycle History</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <PassportTimeline events={passport.timeline || []} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
