import { useState } from 'react'
import { Button, IconButton, Tag } from '@carbon/react'
import { Add, Edit, Power } from '@carbon/icons-react'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { DataTable, type Column } from '@/components/data-table/DataTable'
import { FilterSelect } from '@/components/FilterSelect'
import { PageHeader } from '@/components/PageHeader'
import { VendorFormDialog } from '@/components/vendors/VendorFormDialog'
import { useSetVendorActive, useVendors } from '@/hooks/useVendors'
import { handleMutationError } from '@/lib/feedback'
import { formatDateTime } from '@/lib/format'
import { CATEGORY_LABELS, PAYMENT_TERMS_LABELS, toOptions } from '@/lib/labels'
import { toast } from '@/lib/toast'
import type { Vendor } from '@/types/vendor'

const ALL = 'all'
const CATEGORY_FILTER_OPTIONS = [{ value: ALL, label: 'Semua kategori' }, ...toOptions(CATEGORY_LABELS)]
const STATUS_FILTER_OPTIONS = [
  { value: ALL, label: 'Semua status' },
  { value: 'active', label: 'Aktif' },
  { value: 'inactive', label: 'Nonaktif' },
]

export function VendorsPage() {
  const vendors = useVendors()
  const setActive = useSetVendorActive()
  const [category, setCategory] = useState(ALL)
  const [status, setStatus] = useState(ALL)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Vendor>()
  const [deactivating, setDeactivating] = useState<Vendor>()

  const rows = vendors.data?.filter(
    (v) => (category === ALL || v.category === category) && (status === ALL || v.is_active === (status === 'active')),
  )

  const openForm = (vendor?: Vendor) => {
    setEditing(vendor)
    setFormOpen(true)
  }

  const changeActive = (vendor: Vendor, active: boolean) =>
    setActive.mutate(
      { id: vendor.id, active },
      {
        onSuccess: (response) => {
          toast.success(response.message)
          setDeactivating(undefined)
        },
        onError: (error) => handleMutationError(error),
      },
    )

  const columns: Column<Vendor>[] = [
    {
      id: 'name',
      header: 'Nama vendor',
      sortValue: (v) => v.name,
      cell: (v) => (
        <div className="pw-cell-stack pw-cell-wide">
          <span>{v.name}</span>
          <span className="pw-caption">{v.contact ?? 'Kontak belum diisi'}</span>
        </div>
      ),
    },
    {
      id: 'category',
      header: 'Kategori',
      sortValue: (v) => CATEGORY_LABELS[v.category],
      cell: (v) => CATEGORY_LABELS[v.category],
    },
    { id: 'city', header: 'Kota', sortValue: (v) => v.city, cell: (v) => v.city },
    {
      id: 'payment_terms',
      header: 'Termin pembayaran',
      sortValue: (v) => PAYMENT_TERMS_LABELS[v.payment_terms],
      cell: (v) => PAYMENT_TERMS_LABELS[v.payment_terms],
    },
    {
      id: 'status',
      header: 'Status',
      sortValue: (v) => (v.is_active ? 0 : 1),
      cell: (v) => (
        <Tag type={v.is_active ? 'green' : 'gray'} size="sm">
          {v.is_active ? 'Aktif' : 'Nonaktif'}
        </Tag>
      ),
    },
    {
      id: 'updated_at',
      header: 'Diperbarui',
      className: 'pw-nowrap pw-text-secondary',
      sortValue: (v) => v.updated_at,
      cell: (v) => formatDateTime(v.updated_at),
    },
    {
      id: 'actions',
      header: 'Aksi',
      className: 'pw-cell-actions',
      cell: (v) => (
        <div className="pw-row-actions">
          <IconButton kind="ghost" size="sm" label="Ubah" onClick={() => openForm(v)} aria-label={`Ubah ${v.name}`}>
            <Edit />
          </IconButton>
          {v.is_active ? (
            <IconButton
              kind="ghost"
              size="sm"
              label="Nonaktifkan"
              onClick={() => setDeactivating(v)}
              aria-label={`Nonaktifkan ${v.name}`}
            >
              <Power />
            </IconButton>
          ) : (
            <IconButton
              kind="ghost"
              size="sm"
              label="Aktifkan"
              onClick={() => changeActive(v, true)}
              disabled={setActive.isPending}
              aria-label={`Aktifkan ${v.name}`}
            >
              <Power />
            </IconButton>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="pw-page">
      <PageHeader
        title="Vendor"
        description="Kelola vendor bahan produk, jasa bordir dan printing, serta packaging."
        actions={
          <Button renderIcon={Add} onClick={() => openForm()}>
            Tambah vendor
          </Button>
        }
      />
      <DataTable
        rows={rows}
        columns={columns}
        getRowKey={(v) => v.id}
        searchText={(v) => `${v.name} ${v.city} ${v.contact ?? ''}`}
        searchPlaceholder="Cari nama, kota, atau kontak"
        emptyMessage="Belum ada vendor. Tambahkan vendor pertama."
        isLoading={vendors.isPending}
        error={vendors.error}
        onRetry={() => vendors.refetch()}
        initialSort={{ columnId: 'name', direction: 'asc' }}
        toolbar={
          <>
            <FilterSelect
              id="vendor-category-filter"
              label="Filter kategori"
              value={category}
              onChange={setCategory}
              options={CATEGORY_FILTER_OPTIONS}
            />
            <FilterSelect
              id="vendor-status-filter"
              label="Filter status"
              value={status}
              onChange={setStatus}
              options={STATUS_FILTER_OPTIONS}
            />
          </>
        }
      />
      <VendorFormDialog open={formOpen} onOpenChange={setFormOpen} vendor={editing} />
      <ConfirmDialog
        open={!!deactivating}
        onOpenChange={(open) => !open && setDeactivating(undefined)}
        title="Nonaktifkan vendor?"
        description={`${deactivating?.name ?? ''} tidak akan muncul sebagai kandidat rekomendasi. Histori transaksinya tetap tersimpan dan vendor bisa diaktifkan lagi kapan saja.`}
        confirmLabel="Nonaktifkan"
        isPending={setActive.isPending}
        onConfirm={() => deactivating && changeActive(deactivating, false)}
      />
    </div>
  )
}
