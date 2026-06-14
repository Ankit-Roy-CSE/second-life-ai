import React from "react"
import { Card, CardContent } from "@/components/ui/Card"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/Avatar"
import { Progress } from "@/components/ui/Progress"
import { Badge } from "@/components/ui/Badge"
import { MapPin, DollarSign } from "lucide-react"

export interface MatchCardProps {
  buyer: {
    name: string;
    avatar?: string;
  };
  score: number;
  estimatedSavings: number;
  distanceKm: number;
}

export function MatchCard({ buyer, score, estimatedSavings, distanceKm }: MatchCardProps) {
  const isHighMatch = score >= 80;
  const fallbackInitials = buyer.name ? buyer.name.substring(0, 2).toUpperCase() : "?";
  
  return (
    <Card className="overflow-hidden transition-all hover:border-primary/50 hover:shadow-md">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-4">
            <Avatar className="h-12 w-12">
              <AvatarImage src={buyer.avatar} alt={buyer.name} />
              <AvatarFallback>{fallbackInitials}</AvatarFallback>
            </Avatar>
            <div>
              <h4 className="font-semibold text-lg">{buyer.name}</h4>
              <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                <span>{distanceKm.toFixed(1)} km away</span>
              </div>
            </div>
          </div>
          {isHighMatch && (
            <Badge variant="success">Great Match</Badge>
          )}
        </div>
        
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium text-foreground">Match Score</span>
              <span className="font-bold text-primary">{score}%</span>
            </div>
            <Progress value={score} />
          </div>
          
          <div className="flex items-center gap-4 pt-4 border-t border-border">
            <div className="flex items-center gap-3 flex-1">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success/10 text-success">
                <DollarSign className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Logistics Savings</span>
                <span className="text-base font-bold">${estimatedSavings.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
