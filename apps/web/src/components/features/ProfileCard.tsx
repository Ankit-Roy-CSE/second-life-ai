import React from "react"
import { Leaf } from "lucide-react"
import { Card, CardHeader, CardContent } from "@/components/ui/Card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar"
import { Badge } from "@/components/ui/Badge"
import { UserResponse } from "../../../types/api"

export interface ProfileCardProps {
  user: UserResponse
}

export function ProfileCard({ user }: ProfileCardProps) {
  return (
    <Card>
      <CardHeader>
        <Avatar className="h-16 w-16">
          <AvatarImage src={undefined} alt={user.display_name} />
          <AvatarFallback className="text-xl font-semibold">
            {user.display_name[0].toUpperCase()}
          </AvatarFallback>
        </Avatar>
      </CardHeader>
      <CardContent>
        <h2 className="text-xl font-semibold text-foreground">{user.display_name}</h2>
        <p className="text-sm text-muted-foreground mt-1">{user.email}</p>
        <div className="mt-4">
          <Badge variant="success" className="gap-1.5">
            <Leaf className="h-3.5 w-3.5" />
            <span>{user.green_credits} Green Credits</span>
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
