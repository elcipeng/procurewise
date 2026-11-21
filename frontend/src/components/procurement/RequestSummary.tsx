import type { ReactNode } from 'react'
import { Tile } from '@carbon/react'
import { formatDate, formatRupiah } from '@/lib/format'
import { CATEGORY_LABELS, UNIT_LABELS } from '@/lib/labels'
import type { ProcurementRequest } from '@/types/procurement'
import { PriorityBadge, RequestStatusBadge } from './RequestBadges'

function Item({ label, children, wide }: { label: string; children: ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? 'pw-summary__item pw-summary__item--wide' : 'pw-summary__item'}>
      <dt className="pw-summary__label">{label}</dt>
      <dd className="pw-summary__value">{children}</dd>
    </div>
  )
}

export function RequestSummary({ request }: { request: ProcurementRequest }) {
  return (
    <Tile className="pw-tile">
      <dl className="pw-summary">
        <Item label="Material">
          {request.material_code} - {request.material_name}
          <span className="pw-caption pw-block">{CATEGORY_LABELS[request.material_category]}</span>
        </Item>
        <Item label="Jumlah">
          <span className="pw-numeric">
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
            {request.notes}
          </Item>
        )}
      </dl>
    </Tile>
  )
}
