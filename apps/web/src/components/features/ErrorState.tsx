"use client"

import React from "react"
import { AlertCircle, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/Button"
import { cn } from "@/lib/utils"

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
  ...props
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center space-y-4 rounded-lg border border-danger/30 bg-danger/5 p-8 text-center",
        className
      )}
      {...props}
    >
      <AlertCircle className="h-10 w-10 text-danger" aria-hidden="true" />
      <div className="space-y-1">
        <h4 className="text-lg font-bold text-foreground">{title}</h4>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          {message}
        </p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-4">
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      )}
    </div>
  )
}
