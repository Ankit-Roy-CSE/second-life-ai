import React from "react"
import { PassportTimelineEntry } from "../../../types/api"
import { formatDate } from "@/lib/utils"

export interface PassportTimelineProps {
  events: PassportTimelineEntry[]
}

export function PassportTimeline({ events }: PassportTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="text-center p-8 text-muted-foreground border border-dashed border-border rounded-lg">
        No passport events recorded yet.
      </div>
    )
  }

  return (
    <div className="relative pl-6 space-y-8 before:absolute before:inset-0 before:ml-3 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-foreground/30">
      {events.map((entry, index) => (
        <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
          {/* Marker */}
          <div className="flex items-center justify-center w-6 h-6 rounded-full border-4 border-background bg-foreground absolute left-0 md:left-1/2 -translate-x-1/2 translate-y-1 z-10" />
          
          <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-2.5rem)] bg-card border border-border p-4 rounded-lg shadow-sm">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center mb-2">
              <h4 className="font-bold text-foreground text-base">{entry.event}</h4>
              <time className="text-xs font-mono text-muted-foreground">
                {formatDate(entry.timestamp)}
              </time>
            </div>
            
            {entry.details && Object.keys(entry.details).length > 0 && (
              <div className="mt-3 space-y-1">
                {Object.entries(entry.details).map(([key, value]) => (
                  <div key={key} className="text-sm">
                    <span className="font-semibold text-muted-foreground capitalize">{key.replace(/_/g, ' ')}: </span>
                    <span className="text-foreground">{String(value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
