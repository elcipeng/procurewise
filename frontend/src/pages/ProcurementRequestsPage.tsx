import { useState } from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { DEFAULT_PAGE_SIZE } from '@/components/data-table/DataTable'
import { DataTableView, type Column } from '@/components/data-table/DataTableView'
import { OptionSelect } from '@/components/OptionSelect'
import { PageHeader } from '@/components/PageHeader'
import { PriorityBadge, RequestStatusBadge } from '@/components/procurement/RequestBadges'
import { ProcurementRequestFormDialog } from '@/components/procurement/ProcurementRequestFormDialog'
import { Button } from '@/components/ui/button'
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
    cell: (r) => <span className="text-muted-foreground tabular-nums">#{r.id}</span>,
  },
  {
    id: 'material',
    header: 'Material',
    cell: (r) => (
      <div className="min-w-48">
        <p className="font-medium text-foreground">{r.material_name}</p>
        <p className="text-caption text-muted-foreground">{r.material_code}</p>
      </div>
    ),
  },
  {
    id: 'qty',
    header: 'Jumlah',
    cell: (r) => (
      <span className="whitespace-nowrap tabular-nums">
        {r.qty.toLocaleString('id-ID')} {UNIT_LABELS[r.material_unit]}
      </span>
    ),
  },
  {
    id: 'needed_by',
    header: 'Dibutuhkan paling lambat',
    cell: (r) => <span className="whitespace-nowrap">{formatDate(r.needed_by)}</span>,
  },
  { id: 'priority', header: 'Prioritas', cell: (r) => <PriorityBadge priority={r.priority} /> },
  { id: 'status', header: 'Status', cell: (r) => <RequestStatusBadge status={r.status} /> },
  {
    id: 'request_date',
    header: 'Dibuat',
    cell: (r) => <span className="whitespace-nowrap text-muted-foreground">{formatDate(r.request_date)}</span>,
  },
  {
    id: 'actions',
    header: 'Aksi',
    className: 'text-right',
    cell: (r) => (
      <Button asChild variant="ghost" size="sm">
        <Link to={`/kebutuhan/${r.id}`} aria-label={`Lihat kebutuhan nomor ${r.id}`}>
          Lihat
          <ArrowRight />
        </Link>
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
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Kebutuhan procurement"
        description="Catat kebutuhan pembelian, lalu bandingkan vendor yang direkomendasikan model."
        actions={
          <Button onClick={() => setFormOpen(true)}>
            <Plus />
            Tambah kebutuhan
          </Button>
        }
      />
      <div className="grid grid-cols-2 gap-2 sm:flex">
        <OptionSelect
          value={status}
          onValueChange={(value) => {
            setStatus(value)
            setPage(1)
          }}
          options={STATUS_FILTER_OPTIONS}
          aria-label="Filter status"
          className="sm:w-56"
        />
      </div>
      <DataTableView
        rows={requests.data?.data ?? []}
        columns={columns}
        getRowKey={(r) => r.id}
        emptyMessage="Belum ada kebutuhan procurement dengan status ini."
        isLoading={requests.isPending}
        error={requests.error}
        onRetry={() => requests.refetch()}
        pagination={{
          page,
          pageCount: Math.max(1, Math.ceil(total / pageSize)),
          pageSize,
          total,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
        }}
      />
      <ProcurementRequestFormDialog open={formOpen} onOpenChange={setFormOpen} onCreated={openDetail} />
    </div>
  )
}
