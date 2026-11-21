import { useState } from 'react'
import { Button, IconButton } from '@carbon/react'
import { Add, Edit, TrashCan } from '@carbon/icons-react'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { DataTable, type Column } from '@/components/data-table/DataTable'
import { FilterSelect } from '@/components/FilterSelect'
import { MaterialFormDialog } from '@/components/materials/MaterialFormDialog'
import { PageHeader } from '@/components/PageHeader'
import { useDeleteMaterial, useMaterials } from '@/hooks/useMaterials'
import { handleMutationError } from '@/lib/feedback'
import { formatDateTime } from '@/lib/format'
import { CATEGORY_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
import { toast } from '@/lib/toast'
import type { Material } from '@/types/material'

const ALL = 'all'
const CATEGORY_FILTER_OPTIONS = [{ value: ALL, label: 'Semua kategori' }, ...toOptions(CATEGORY_LABELS)]

export function MaterialsPage() {
  const materials = useMaterials()
  const remove = useDeleteMaterial()
  const [category, setCategory] = useState(ALL)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Material>()
  const [deleting, setDeleting] = useState<Material>()

  const rows = materials.data?.filter((m) => category === ALL || m.category === category)

  const openForm = (material?: Material) => {
    setEditing(material)
    setFormOpen(true)
  }

  const confirmDelete = () => {
    if (!deleting) return
    remove.mutate(deleting.id, {
      onSuccess: (response) => toast.success(response.message),
      // 409 dari backend menjelaskan material masih dipakai di mana, dialog tetap ditutup
      onError: (error) => handleMutationError(error),
      onSettled: () => setDeleting(undefined),
    })
  }

  const columns: Column<Material>[] = [
    {
      id: 'code',
      header: 'Kode',
      sortValue: (m) => m.code,
      cell: (m) => <span className="pw-mono">{m.code}</span>,
    },
    {
      id: 'name',
      header: 'Nama material',
      sortValue: (m) => m.name,
      cell: (m) => <span className="pw-cell-wide">{m.name}</span>,
    },
    {
      id: 'category',
      header: 'Kategori',
      sortValue: (m) => CATEGORY_LABELS[m.category],
      cell: (m) => CATEGORY_LABELS[m.category],
    },
    { id: 'unit', header: 'Satuan', sortValue: (m) => m.unit, cell: (m) => UNIT_LABELS[m.unit] },
    {
      id: 'updated_at',
      header: 'Diperbarui',
      className: 'pw-nowrap pw-text-secondary',
      sortValue: (m) => m.updated_at,
      cell: (m) => formatDateTime(m.updated_at),
    },
    {
      id: 'actions',
      header: 'Aksi',
      className: 'pw-cell-actions',
      cell: (m) => (
        <div className="pw-row-actions">
          <IconButton kind="ghost" size="sm" label="Ubah" onClick={() => openForm(m)} aria-label={`Ubah ${m.code}`}>
            <Edit />
          </IconButton>
          <IconButton
            kind="ghost"
            size="sm"
            label="Hapus"
            onClick={() => setDeleting(m)}
            aria-label={`Hapus ${m.code}`}
          >
            <TrashCan />
          </IconButton>
        </div>
      ),
    },
  ]

  return (
    <div className="pw-page">
      <PageHeader
        title="Material"
        description="Daftar bahan produk, jasa, dan packaging yang dibeli dari vendor."
        actions={
          <Button renderIcon={Add} onClick={() => openForm()}>
            Tambah material
          </Button>
        }
      />
      <DataTable
        rows={rows}
        columns={columns}
        getRowKey={(m) => m.id}
        searchText={(m) => `${m.code} ${m.name}`}
        searchPlaceholder="Cari kode atau nama material"
        emptyMessage="Belum ada material. Tambahkan material pertama."
        isLoading={materials.isPending}
        error={materials.error}
        onRetry={() => materials.refetch()}
        initialSort={{ columnId: 'code', direction: 'asc' }}
        toolbar={
          <FilterSelect
            id="material-category-filter"
            label="Filter kategori"
            value={category}
            onChange={setCategory}
            options={CATEGORY_FILTER_OPTIONS}
          />
        }
      />
      <MaterialFormDialog open={formOpen} onOpenChange={setFormOpen} material={editing} />
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(undefined)}
        title="Hapus material?"
        description={`${deleting?.code ?? ''} ${deleting?.name ?? ''} akan dihapus permanen. Material yang sudah dipakai di penawaran, transaksi, atau kebutuhan procurement tidak bisa dihapus.`}
        confirmLabel="Hapus"
        isPending={remove.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  )
}
