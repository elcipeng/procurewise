import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { formatDate, formatRupiah } from '@/lib/format'
import { CATEGORY_LABELS, UNIT_LABELS } from '@/lib/labels'
import type { ProcurementRequest } from '@/types/procurement'
import { PriorityBadge, RequestStatusBadge } from './RequestBadges'

function Item({ label, children, wide }: { label: string; children: ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? 'sm:col-span-2 lg:col-span-4' : undefined}>
      <dt className="text-caption text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium text-foreground">{children}</dd>
    </div>
  )
}

export function RequestSummary({ request }: { request: ProcurementRequest }) {
  return (
    <Card className="py-5 shadow-card">
      <CardContent>
        <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-4">
          <Item label="Material">
            {request.material_code} - {request.material_name}
            <span className="block text-caption font-normal text-muted-foreground">
              {CATEGORY_LABELS[request.material_category]}
            </span>
          </Item>
          <Item label="Jumlah">
            <span className="tabular-nums">
              {request.qty.toLocaleString('id-ID')} {UNIT_LABELS[request.material_unit]}
            </span>
          </Item>
          <Item label="Dibutuhkan paling lambat">{formatDate(request.needed_by)}</Item>
          <Item label="Tanggal kebutuhan dibuat">{formatDate(request.request_date)}</Item>
          <Item label="Prioritas">
            <PriorityBadge priority={request.priority} />
          </Item>
          <Item label="Budget maksimal">
            {request.max_budget === null ? 'Tidak dibatasi' : formatRupiah(request.max_budget)}
          </Item>
          <Item label="Status">
            <RequestStatusBadge status={request.status} />
          </Item>
          {request.notes && (
            <Item label="Catatan" wide>
              <span className="font-normal">{request.notes}</span>
            </Item>
          )}
        </dl>
      </CardContent>
    </Card>
  )
}
