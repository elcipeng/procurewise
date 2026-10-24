import { useState } from 'react'
import { Pencil, Plus, Power, PowerOff } from 'lucide-react'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { DataTable, type Column } from '@/components/data-table/DataTable'
import { OptionSelect } from '@/components/OptionSelect'
import { PageHeader } from '@/components/PageHeader'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { VendorFormDialog } from '@/components/vendors/VendorFormDialog'
import { useSetVendorActive, useVendors } from '@/hooks/useVendors'
import { handleMutationError } from '@/lib/feedback'
import { formatDateTime } from '@/lib/format'
import { CATEGORY_LABELS, PAYMENT_TERMS_LABELS, toOptions } from '@/lib/labels'
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
    (v) =>
      (category === ALL || v.category === category) &&
      (status === ALL || v.is_active === (status === 'active')),
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
        <div className="min-w-48">
          <p className="font-medium text-foreground">{v.name}</p>
          <p className="text-caption text-muted-foreground">{v.contact ?? 'Kontak belum diisi'}</p>
        </div>
      ),
    },
    { id: 'category', header: 'Kategori', sortValue: (v) => CATEGORY_LABELS[v.category], cell: (v) => CATEGORY_LABELS[v.category] },
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
      cell: (v) => <StatusBadge tone={v.is_active ? 'success' : 'neutral'} label={v.is_active ? 'Aktif' : 'Nonaktif'} />,
    },
    {
      id: 'updated_at',
      header: 'Diperbarui',
      sortValue: (v) => v.updated_at,
      cell: (v) => <span className="whitespace-nowrap text-muted-foreground">{formatDateTime(v.updated_at)}</span>,
    },
    {
      id: 'actions',
      header: 'Aksi',
      className: 'w-24 text-right',
      cell: (v) => (
        <div className="flex justify-end gap-1">
          <Button variant="ghost" size="icon-sm" onClick={() => openForm(v)} aria-label={`Ubah ${v.name}`} title="Ubah">
            <Pencil />
          </Button>
          {v.is_active ? (
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              onClick={() => setDeactivating(v)}
              aria-label={`Nonaktifkan ${v.name}`}
              title="Nonaktifkan"
            >
              <PowerOff />
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => changeActive(v, true)}
              disabled={setActive.isPending}
              aria-label={`Aktifkan ${v.name}`}
              title="Aktifkan"
            >
              <Power />
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Vendor"
        description="Kelola vendor bahan produk, jasa bordir dan printing, serta packaging."
        actions={
          <Button onClick={() => openForm()}>
            <Plus />
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
            <OptionSelect
              value={category}
              onValueChange={setCategory}
              options={CATEGORY_FILTER_OPTIONS}
              aria-label="Filter kategori"
              className="sm:w-52"
            />
            <OptionSelect
              value={status}
              onValueChange={setStatus}
              options={STATUS_FILTER_OPTIONS}
              aria-label="Filter status"
              className="sm:w-36"
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
