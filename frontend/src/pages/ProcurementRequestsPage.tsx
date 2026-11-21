import { useState } from 'react'
import { Button, TableToolbar, TableToolbarContent } from '@carbon/react'
import { Add, ArrowRight } from '@carbon/icons-react'
import { Link, useNavigate } from 'react-router'
import { DEFAULT_PAGE_SIZE } from '@/components/data-table/DataTable'
import { DataTableView, type Column } from '@/components/data-table/DataTableView'
import { FilterSelect } from '@/components/FilterSelect'
import { PageHeader } from '@/components/PageHeader'
import { PriorityBadge, RequestStatusBadge } from '@/components/procurement/RequestBadges'
import { ProcurementRequestFormDialog } from '@/components/procurement/ProcurementRequestFormDialog'
import { useProcurementRequests } from '@/hooks/useProcurementRequests'
import { formatDate } from '@/lib/format'
import { REQUEST_STATUS_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
import type { ProcurementRequest, RequestDetailState, RequestStatus } from '@/types/procurement'

const ALL = 'all'
const STATUS_FILTER_OPTIONS = [{ value: ALL, label: 'Semua status' }, ...toOptions(REQUEST_STATUS_LABELS)]

const columns: Column<ProcurementRequest>[] = [
  {
    id: 'id',
    header: 'No.',
    cell: (r) => <span className="pw-mono pw-text-secondary">#{r.id}</span>,
  },
  {
    id: 'material',
    header: 'Material',
    cell: (r) => (
      <div className="pw-cell-stack pw-cell-wide">
        <span>{r.material_name}</span>
        <span className="pw-mono pw-caption">{r.material_code}</span>
      </div>
    ),
  },
  {
    id: 'qty',
    header: 'Jumlah',
    className: 'pw-nowrap',
    cell: (r) => (
      <span className="pw-numeric">
        {r.qty.toLocaleString('id-ID')} {UNIT_LABELS[r.material_unit]}
      </span>
    ),
  },
  {
    id: 'needed_by',
    header: 'Dibutuhkan paling lambat',
    className: 'pw-nowrap',
    cell: (r) => formatDate(r.needed_by),
  },
  { id: 'priority', header: 'Prioritas', cell: (r) => <PriorityBadge priority={r.priority} /> },
  { id: 'status', header: 'Status', cell: (r) => <RequestStatusBadge status={r.status} /> },
  {
    id: 'request_date',
    header: 'Dibuat',
    className: 'pw-nowrap pw-text-secondary',
    cell: (r) => formatDate(r.request_date),
  },
  {
    id: 'actions',
    header: 'Aksi',
    className: 'pw-cell-actions',
    cell: (r) => (
      <Button
        as={Link}
        to={`/kebutuhan/${r.id}`}
        kind="ghost"
        size="sm"
        renderIcon={ArrowRight}
        aria-label={`Lihat kebutuhan nomor ${r.id}`}
      >
        Lihat
      </Button>
    ),
  },
]

export function ProcurementRequestsPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [status, setStatus] = useState(ALL)
  const [formOpen, setFormOpen] = useState(false)

  const requests = useProcurementRequests({
    page,
    pageSize,
    status: status === ALL ? undefined : (status as RequestStatus),
  })
  const total = requests.data?.meta?.total ?? 0

  const openDetail = (request: ProcurementRequest) => {
    setFormOpen(false)
    const state: RequestDetailState = { runRecommendation: true }
    navigate(`/kebutuhan/${request.id}`, { state })
  }

  return (
    <div className="pw-page">
      <PageHeader
        title="Kebutuhan procurement"
        description="Catat kebutuhan pembelian, lalu bandingkan vendor yang direkomendasikan model."
        actions={
          <Button renderIcon={Add} onClick={() => setFormOpen(true)}>
            Tambah kebutuhan
          </Button>
        }
      />
      <DataTableView
        rows={requests.data?.data ?? []}
        columns={columns}
        getRowKey={(r) => r.id}
        emptyMessage="Belum ada kebutuhan procurement dengan status ini."
        isLoading={requests.isPending}
        error={requests.error}
        onRetry={() => requests.refetch()}
        toolbar={
          <TableToolbar aria-label="Filter kebutuhan">
            <TableToolbarContent className="pw-toolbar pw-toolbar--start">
              <FilterSelect
                id="request-status-filter"
                label="Filter status"
                value={status}
                onChange={(value) => {
                  setStatus(value)
                  setPage(1)
                }}
                options={STATUS_FILTER_OPTIONS}
              />
            </TableToolbarContent>
          </TableToolbar>
        }
        pagination={{
          page,
          pageSize,
          total,
          onChange: (nextPage, nextSize) => {
            setPage(nextSize === pageSize ? nextPage : 1)
            setPageSize(nextSize)
          },
        }}
      />
      <ProcurementRequestFormDialog open={formOpen} onOpenChange={setFormOpen} onCreated={openDetail} />
    </div>
  )
}
