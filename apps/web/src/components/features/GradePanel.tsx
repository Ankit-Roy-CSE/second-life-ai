"use client"

import React from "react"
import { Grade } from "../../../types/enums"
import { Card, CardContent } from "@/components/ui/Card"
import { GradeBadge } from "@/components/ui/GradeBadge"
import { Progress } from "@/components/ui/Progress"
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react"

export interface GradePanelProps {
  grade: Grade
  confidence: number // 0-1
  damageSummary: string
  defects: string[]
}

export function GradePanel({ grade, confidence, damageSummary, defects }: GradePanelProps) {
  const confidencePercent = Math.round(confidence * 100)
  
  return (
    <Card className="overflow-hidden border-border">
      <div className="bg-secondary p-4 text-secondary-foreground">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-primary" aria-hidden={true} />
          <h3 className="font-semibold text-lg">AI Inspection Results</h3>
        </div>
      </div>
      <CardContent className="p-6 space-y-5">
        {/* Row 1: Grade + Confidence side by side */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col items-center justify-center space-y-2 p-5 bg-muted rounded-lg border border-border">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Condition Grade</span>
            <GradeBadge grade={grade} size="lg" showLabel={false} className="h-16 w-16 text-3xl" />
            <span className="font-medium text-foreground text-sm">
              {grade === Grade.A && "Like New"}
              {grade === Grade.B && "Good"}
              {grade === Grade.C && "Fair"}
              {grade === Grade.D && "Poor"}
            </span>
          </div>

          <div className="flex flex-col justify-center space-y-3 p-5 bg-muted rounded-lg border border-border">
            <div className="flex justify-between text-sm font-medium">
              <span className="text-muted-foreground">AI Confidence</span>
              <span className="text-foreground font-semibold">{confidencePercent}%</span>
            </div>
            <Progress value={confidencePercent} className="h-2.5" />
            <span className="text-xs text-muted-foreground">
              {confidencePercent >= 90 ? "High confidence" : confidencePercent >= 75 ? "Moderate confidence" : "Low confidence"}
            </span>
          </div>
        </div>

        {/* Row 2: Damage Summary — full width */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Damage Summary</h4>
          <p className="text-sm text-muted-foreground bg-muted p-4 rounded-md border border-border/50 leading-relaxed">
            {damageSummary}
          </p>
        </div>

        {/* Row 3: Detected Defects — full width */}
        {defects && defects.length > 0 ? (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Detected Defects</h4>
            <ul className="space-y-1.5">
              {defects.map((defect, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                  <AlertTriangle className="h-4 w-4 text-warning shrink-0 mt-0.5" aria-hidden={true} />
                  <span>{defect}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Detected Defects</h4>
            <div className="flex items-center gap-2 text-sm text-success">
              <CheckCircle2 className="h-4 w-4" aria-hidden={true} />
              <span>No visible defects detected.</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
