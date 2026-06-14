"use client"

import { BarChart3 } from "lucide-react"
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { CHART_TOKENS } from "@/lib/chart-tokens"
import type { MetricsBreakdownEntry } from "@/lib/schemas/sustainability"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card"
import { Skeleton } from "@/components/ui/Skeleton"
import { EmptyState } from "@/components/features/EmptyState"
import { ErrorState } from "@/components/features/ErrorState"

export interface ChartCardProps {
  title: string
  description?: string
  breakdown: MetricsBreakdownEntry[]
  isLoading?: boolean
  isError?: boolean
  onRetry?: () => void
}

export function ChartCard({
  title,
  description,
  breakdown,
  isLoading,
  isError,
  onRetry,
}: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-72 w-full rounded-lg" />
        ) : isError ? (
          <ErrorState message="Failed to load chart data." onRetry={onRetry} />
        ) : breakdown.length === 0 ? (
          <EmptyState
            icon={BarChart3}
            title="No impact data yet"
            description="Process a return to see lifecycle impact here."
          />
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <BarChart data={breakdown}>
              <XAxis dataKey="action" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="co2_avoided_kg">
                {breakdown.map((entry, i) => (
                  <Cell
                    key={entry.action}
                    fill={CHART_TOKENS[i % CHART_TOKENS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
