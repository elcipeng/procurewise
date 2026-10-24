import { useState } from 'react'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { DataTable, type Column } from '@/components/data-table/DataTable'
import { MaterialFormDialog } from '@/components/materials/MaterialFormDialog'
import { OptionSelect } from '@/components/OptionSelect'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { useDeleteMaterial, useMaterials } from '@/hooks/useMaterials'
import { handleMutationError } from '@/lib/feedback'
import { formatDateTime } from '@/lib/format'
import { CATEGORY_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
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
      cell: (m) => <span className="font-medium text-foreground tabular-nums">{m.code}</span>,
    },
    {
      id: 'name',
      header: 'Nama material',
      sortValue: (m) => m.name,
      cell: (m) => <span className="block min-w-48">{m.name}</span>,
    },
    { id: 'category', header: 'Kategori', sortValue: (m) => CATEGORY_LABELS[m.category], cell: (m) => CATEGORY_LABELS[m.category] },
    { id: 'unit', header: 'Satuan', sortValue: (m) => m.unit, cell: (m) => UNIT_LABELS[m.unit] },
    {
      id: 'updated_at',
      header: 'Diperbarui',
      sortValue: (m) => m.updated_at,
      cell: (m) => <span className="whitespace-nowrap text-muted-foreground">{formatDateTime(m.updated_at)}</span>,
    },
    {
      id: 'actions',
      header: 'Aksi',
      className: 'w-24 text-right',
      cell: (m) => (
        <div className="flex justify-end gap-1">
          <Button variant="ghost" size="icon-sm" onClick={() => openForm(m)} aria-label={`Ubah ${m.code}`} title="Ubah">
            <Pencil />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            onClick={() => setDeleting(m)}
            aria-label={`Hapus ${m.code}`}
            title="Hapus"
          >
            <Trash2 />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Material"
        description="Daftar bahan produk, jasa, dan packaging yang dibeli dari vendor."
        actions={
          <Button onClick={() => openForm()}>
            <Plus />
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
          <OptionSelect
            value={category}
            onValueChange={setCategory}
            options={CATEGORY_FILTER_OPTIONS}
            aria-label="Filter kategori"
            className="sm:w-52"
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
