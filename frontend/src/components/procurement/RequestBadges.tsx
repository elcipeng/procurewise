import { Tag } from '@carbon/react'
import { PRIORITY_LABELS, REQUEST_STATUS_LABELS } from '@/lib/labels'
import type { Priority, RequestStatus } from '@/types/procurement'

// warna tag mengikuti makna: biru menunggu diproses, hijau sudah selesai diproses, abu-abu arsip histori
const STATUS_TAG_TYPES = {
  new: 'blue',
  recommended: 'green',
  completed: 'gray',
  cancelled: 'gray',
} as const

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  return (
    <Tag type={STATUS_TAG_TYPES[status]} size="sm">
      {REQUEST_STATUS_LABELS[status]}
    </Tag>
  )
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <Tag type={priority === 'high' ? 'red' : 'gray'} size="sm">
      {PRIORITY_LABELS[priority]}
    </Tag>
  )
}
