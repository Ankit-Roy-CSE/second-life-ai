import { StatCard } from "@/components/features/StatCard"
import { formatNumber } from "@/lib/utils"
import { Leaf, Trash2, DollarSign, Award } from "lucide-react"
import type { SustainabilityMetrics } from "@/lib/schemas/sustainability"

interface StatCardRowProps {
  totals: SustainabilityMetrics["totals"]
}

/**
 * StatCard_Row — maps the four Headline_Metrics onto the existing StatCard component.
 *
 * Renders one tile each for CO₂ avoided, waste diverted, value recovered, and
 * green credits, all sourced from the validated `totals` object.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 7.1, 7.2
 */
export function StatCardRow({ totals }: StatCardRowProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        label="CO₂ Avoided"
        value={formatNumber(totals.co2_avoided_kg)}
        unit="kg"
        icon={Leaf}
        tone="success"
      />
      <StatCard
        label="Waste Diverted"
        value={formatNumber(totals.waste_diverted_kg)}
        unit="kg"
        icon={Trash2}
        tone="success"
      />
      <StatCard
        label="Value Recovered"
        value={formatNumber(totals.value_recovered)}
        icon={DollarSign}
      />
      <StatCard
        label="Green Credits"
        value={formatNumber(totals.green_credits)}
        icon={Award}
      />
    </div>
  )
}
