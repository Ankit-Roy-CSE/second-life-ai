import React from "react"
import { Card, CardContent } from "@/components/ui/Card"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

export interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  delta?: number
  icon?: LucideIcon
  tone?: "default" | "success" | "warning" | "danger"
}

export function StatCard({ label, value, unit, delta, icon: Icon, tone = "default", className }: StatCardProps & { className?: string }) {
  const getToneClasses = () => {
    switch (tone) {
      case "success": return "text-success"
      case "warning": return "text-warning"
      case "danger": return "text-danger"
      default: return "text-foreground"
    }
  }

  const getDeltaClasses = () => {
    if (delta === undefined) return ""
    return delta > 0 ? "text-success" : delta < 0 ? "text-danger" : "text-muted-foreground"
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-4">
          <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            {label}
          </p>
          {Icon && (
            <div className="p-2 bg-muted rounded-md text-accent">
              <Icon className="w-5 h-5" />
            </div>
          )}
        </div>
        <div className="flex items-baseline gap-2">
          <h3 className={cn("text-3xl font-mono tabular-nums font-bold", getToneClasses())}>
            {value}
          </h3>
          {unit && (
            <span className="text-sm text-muted-foreground font-medium">
              {unit}
            </span>
          )}
        </div>
        {delta !== undefined && (
          <div className="mt-2">
            <span className={cn("text-xs font-semibold", getDeltaClasses())}>
              {delta > 0 ? `+${delta}` : delta}
            </span>
            <span className="text-xs text-muted-foreground ml-1">
              from last period
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
