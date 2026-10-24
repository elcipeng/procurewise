import { useState, type FormEvent } from 'react'
import { toast } from 'sonner'
import { FormField } from '@/components/FormField'
import { OptionSelect } from '@/components/OptionSelect'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useSaveMaterial } from '@/hooks/useMaterials'
import { fieldErrorId, handleMutationError, type FieldErrors } from '@/lib/feedback'
import { CATEGORY_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
import type { Material, Unit } from '@/types/material'
import type { Category } from '@/types/vendor'

const FORM_FIELDS = ['code', 'name', 'category', 'unit'] as const
const CATEGORY_OPTIONS = toOptions(CATEGORY_LABELS)
const UNIT_OPTIONS = toOptions(UNIT_LABELS)

type FormState = {
  code: string
  name: string
  category: Category | ''
  unit: Unit | ''
}

const toFormState = (material?: Material): FormState => ({
  code: material?.code ?? '',
  name: material?.name ?? '',
  category: material?.category ?? '',
  unit: material?.unit ?? '',
})

type MaterialFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  material?: Material
}

export function MaterialFormDialog({ open, onOpenChange, material }: MaterialFormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{material ? 'Ubah material' : 'Tambah material'}</DialogTitle>
          <DialogDescription>Material adalah bahan, jasa, atau packaging yang dibeli dari vendor.</DialogDescription>
        </DialogHeader>
        {open && <MaterialForm material={material} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function MaterialForm({ material, onDone }: { material?: Material; onDone: () => void }) {
  const [form, setForm] = useState(() => toFormState(material))
  const [errors, setErrors] = useState<FieldErrors>({})
  const save = useSaveMaterial()

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setErrors((current) => ({ ...current, [key]: '' }))
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    // pilihan kosong dicek di sini supaya pesan error tidak menampilkan kode enum dari backend
    const missing: FieldErrors = {}
    if (!form.category) missing.category = 'Pilih kategori material'
    if (!form.unit) missing.unit = 'Pilih satuan'
    if (!form.category || !form.unit) {
      setErrors(missing)
      return
    }

    const input = { code: form.code, name: form.name, category: form.category, unit: form.unit }
    save.mutate(
      { id: material?.id, input },
      {
        onSuccess: (response) => {
          toast.success(response.message)
          onDone()
        },
        onError: (error) => setErrors(handleMutationError(error, FORM_FIELDS)),
      },
    )
  }

  const describe = (field: keyof FormState) => (errors[field] ? fieldErrorId(`material-${field}`) : undefined)

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-[8rem_1fr]">
        <FormField id="material-code" label="Kode" hint="Contoh: B01" error={errors.code}>
          <Input
            id="material-code"
            value={form.code}
            onChange={(e) => set('code', e.target.value.toUpperCase())}
            aria-invalid={!!errors.code || undefined}
            aria-describedby={describe('code')}
            className="uppercase tabular-nums"
            autoFocus
          />
        </FormField>
        <FormField id="material-name" label="Nama material" error={errors.name}>
          <Input
            id="material-name"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            aria-invalid={!!errors.name || undefined}
            aria-describedby={describe('name')}
          />
        </FormField>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField id="material-category" label="Kategori" error={errors.category}>
          <OptionSelect
            id="material-category"
            value={form.category}
            onValueChange={(value) => set('category', value as Category)}
            options={CATEGORY_OPTIONS}
            placeholder="Pilih kategori"
            invalid={!!errors.category}
            describedBy={describe('category')}
          />
        </FormField>
        <FormField id="material-unit" label="Satuan" error={errors.unit}>
          <OptionSelect
            id="material-unit"
            value={form.unit}
            onValueChange={(value) => set('unit', value as Unit)}
            options={UNIT_OPTIONS}
            placeholder="Pilih satuan"
            invalid={!!errors.unit}
            describedBy={describe('unit')}
          />
        </FormField>
      </div>
      <DialogFooter className="mt-2">
        <Button type="button" variant="outline" onClick={onDone} disabled={save.isPending}>
          Batal
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? 'Menyimpan...' : 'Simpan'}
        </Button>
      </DialogFooter>
    </form>
  )
}
