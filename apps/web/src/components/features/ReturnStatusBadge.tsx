import { Badge } from "@/components/ui/Badge"
import { ReturnStatus } from "../../../types/enums"

type BadgeVariant = "info" | "warning" | "success" | "danger"

interface StatusConfig {
  variant: BadgeVariant
  label: string
}

const STATUS_MAP: Record<ReturnStatus, StatusConfig> = {
  [ReturnStatus.SUBMITTED]:  { variant: "info",    label: "Submitted"   },
  [ReturnStatus.GRADED]:     { variant: "info",    label: "Graded"      },
  [ReturnStatus.DECIDED]:    { variant: "warning", label: "Decided"     },
  [ReturnStatus.PASSPORTED]: { variant: "warning", label: "Passported"  },
  [ReturnStatus.MATCHING]:   { variant: "warning", label: "Matching"    },
  [ReturnStatus.LISTED]:     { variant: "success", label: "Listed"      },
  [ReturnStatus.SOLD]:       { variant: "success", label: "Sold"        },
  [ReturnStatus.FAILED]:     { variant: "danger",  label: "Failed"      },
}

interface ReturnStatusBadgeProps {
  status: ReturnStatus
}

export function ReturnStatusBadge({ status }: ReturnStatusBadgeProps) {
  const { variant, label } = STATUS_MAP[status]
  return <Badge variant={variant}>{label}</Badge>
}
