import Link from "next/link"
import { Package } from "lucide-react"

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card"
import { EmptyState } from "@/components/features/EmptyState"
import { ReturnStatusBadge } from "@/components/features/ReturnStatusBadge"
import { Button } from "@/components/ui/Button"
import { ReturnResponse } from "../../../types/api"

interface ActiveReturnsListProps {
  returns: ReturnResponse[]
}

function truncateProductId(productId: string): string {
  if (productId.length > 16) {
    return productId.slice(0, 16) + "..."
  }
  return productId
}

export function ActiveReturnsList({ returns }: ActiveReturnsListProps) {
  if (returns.length === 0) {
    return (
      <EmptyState
        icon={Package}
        title="No active returns"
        description="Submit a return to get started"
        action={
          <Button asChild>
            <Link href="/returns">Go to Returns</Link>
          </Button>
        }
      />
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Returns</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y divide-border">
          {returns.map((r) => (
            <li key={r.id}>
              <Link
                href={`/returns/${r.id}`}
                className="flex items-center justify-between gap-4 py-3 border-b last:border-0 hover:bg-muted/40 transition-colors rounded px-1 -mx-1"
              >
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="text-sm font-medium truncate">
                    {truncateProductId(r.product_id)}
                  </span>
                  <span className="text-xs text-muted-foreground truncate">
                    {r.reason}
                  </span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-muted-foreground hidden sm:block">
                    {new Date(r.created_at).toLocaleDateString()}
                  </span>
                  <ReturnStatusBadge status={r.status} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
