"use client"

import React from "react"
import { Grade } from "../../../types/enums"
import { cn } from "@/lib/utils"

export interface GradeBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  grade: Grade
  size?: "sm" | "md" | "lg"
  showLabel?: boolean
}

const gradeStyles: Record<Grade, string> = {
  [Grade.A]: "bg-grade-a text-grade-a-foreground",
  [Grade.B]: "bg-grade-b text-grade-b-foreground",
  [Grade.C]: "bg-grade-c text-grade-c-foreground",
  [Grade.D]: "bg-grade-d text-grade-d-foreground",
}

const gradeLabels: Record<Grade, string> = {
  [Grade.A]: "Like New",
  [Grade.B]: "Good",
  [Grade.C]: "Fair",
  [Grade.D]: "Poor",
}

export function GradeBadge({ grade, size = "md", showLabel = true, className, ...props }: GradeBadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-full font-bold uppercase",
        gradeStyles[grade],
        size === "sm" && "h-6 w-6 text-xs",
        size === "md" && "h-8 w-8 text-sm",
        size === "lg" && "h-12 w-12 text-lg",
        showLabel && "w-auto px-3 rounded-md", // override if label is shown
        className
      )}
      {...props}
    >
      <span className="mr-1">{grade}</span>
      {showLabel && <span className="font-medium"> - {gradeLabels[grade]}</span>}
    </div>
  )
}
