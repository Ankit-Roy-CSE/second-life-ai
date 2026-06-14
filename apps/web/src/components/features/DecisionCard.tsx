import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { LifecycleAction } from "../../../types/enums"
import { StatCard } from "./StatCard"
import { Leaf, RefreshCw, HandHeart, Recycle, MapPin } from "lucide-react"

export interface DecisionCardProps {
  action: LifecycleAction
  rationale: string
  valueRecovery: number
  sustainabilityScore: number
}

const actionConfig: Record<LifecycleAction, { colorClass: string; icon: React.ElementType; label: string }> = {
  [LifecycleAction.RESELL]: { colorClass: "text-accent", icon: RefreshCw, label: "Resell" },
  [LifecycleAction.REFURBISH]: { colorClass: "text-info", icon: RefreshCw, label: "Refurbish" },
  [LifecycleAction.DONATE]: { colorClass: "text-action-donate", icon: HandHeart, label: "Donate" },
  [LifecycleAction.RECYCLE]: { colorClass: "text-primary", icon: Recycle, label: "Recycle" },
  [LifecycleAction.HYPERLOCAL]: { colorClass: "text-action-hyperlocal", icon: MapPin, label: "Hyperlocal Match" },
}

export function DecisionCard({ action, rationale, valueRecovery, sustainabilityScore }: DecisionCardProps) {
  const config = actionConfig[action] || actionConfig[LifecycleAction.RESELL]
  const Icon = config.icon

  return (
    <Card className="overflow-hidden border-border">
      <CardHeader className="bg-secondary text-secondary-foreground">
        <CardTitle className="text-xl flex items-center gap-2">
          <Icon className={config.colorClass} />
          Lifecycle Decision: <span className={config.colorClass}>{config.label}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6 space-y-8">
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">Rationale</h4>
          <p className="text-base text-foreground leading-relaxed">{rationale}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard
            label="Est. Value Recovery"
            value={`$${valueRecovery.toFixed(2)}`}
            tone="default"
          />
          <StatCard
            label="Sustainability Score"
            value={sustainabilityScore}
            unit="/ 100"
            icon={Leaf}
            tone="success"
          />
        </div>
      </CardContent>
    </Card>
  )
}
