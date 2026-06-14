import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/Card"
import { StatCard } from "@/components/features/StatCard"
import { Leaf, Award } from "lucide-react"
import Link from "next/link"
import { formatNumber } from "@/lib/utils"
import type { SustainabilityMetrics } from "@/lib/schemas/sustainability"

interface SustainabilitySummaryProps {
  totals: SustainabilityMetrics["totals"]
}

/**
 * SustainabilitySummary — pure display component showing headline sustainability
 * metrics on the user dashboard.
 *
 * Renders CO₂ avoided and green credits from the validated `totals` object
 * received from the parent. Does NOT fetch its own data.
 *
 * Requirements: 3.2, 3.5
 */
export function SustainabilitySummary({ totals }: SustainabilitySummaryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Sustainability Impact</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <StatCard
            label="CO₂ Avoided"
            value={formatNumber(totals.co2_avoided_kg)}
            unit="kg"
            tone="success"
            icon={Leaf}
          />
          <StatCard
            label="Green Credits"
            value={formatNumber(totals.green_credits)}
            icon={Award}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Link
          href="/sustainability"
          className="text-sm text-primary hover:underline"
        >
          View full report →
        </Link>
      </CardFooter>
    </Card>
  )
}
