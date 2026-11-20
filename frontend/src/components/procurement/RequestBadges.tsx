import { StatusBadge } from '@/components/StatusBadge'
import { PRIORITY_LABELS, REQUEST_STATUS_LABELS } from '@/lib/labels'
import type { Priority, RequestStatus } from '@/types/procurement'

const STATUS_TONES = {
  new: 'warning',
  recommended: 'success',
  completed: 'neutral',
  cancelled: 'neutral',
} as const

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  return <StatusBadge tone={STATUS_TONES[status]} label={REQUEST_STATUS_LABELS[status]} />
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return <StatusBadge tone={priority === 'high' ? 'warning' : 'neutral'} label={PRIORITY_LABELS[priority]} />
}
