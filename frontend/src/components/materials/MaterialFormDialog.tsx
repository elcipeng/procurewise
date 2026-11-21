import { useState, type FormEvent } from 'react'
import { Select, SelectItem, TextInput } from '@carbon/react'
import { FormModal } from '@/components/FormModal'
import { useSaveMaterial } from '@/hooks/useMaterials'
import { handleMutationError, type FieldErrors } from '@/lib/feedback'
import { toast } from '@/lib/toast'
import { CATEGORY_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
import type { Material, Unit } from '@/types/material'
import type { Category } from '@/types/vendor'

const FORM_ID = 'material-form'
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
  // form dipasang ulang setiap modal dibuka supaya isian dan error lama tidak tersisa
  return open ? <MaterialForm material={material} onDone={() => onOpenChange(false)} /> : null
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

  return (
    <FormModal
      open
      onClose={onDone}
      formId={FORM_ID}
      title={material ? 'Ubah material' : 'Tambah material'}
      description="Material adalah bahan, jasa, atau packaging yang dibeli dari vendor."
      submitLabel="Simpan"
      isPending={save.isPending}
      onSubmit={submit}
    >
      <div className="pw-form__row pw-form__row--code">
        <TextInput
          id="material-code"
          labelText="Kode"
          helperText="Contoh: B01"
          className="pw-mono"
          value={form.code}
          onChange={(e) => set('code', e.target.value.toUpperCase())}
          invalid={!!errors.code}
          invalidText={errors.code}
          data-modal-primary-focus
        />
        <TextInput
          id="material-name"
          labelText="Nama material"
          value={form.name}
          onChange={(e) => set('name', e.target.value)}
          invalid={!!errors.name}
          invalidText={errors.name}
        />
      </div>
      <div className="pw-form__row">
        <Select
          id="material-category"
          labelText="Kategori"
          value={form.category}
          onChange={(e) => set('category', e.target.value as Category)}
          invalid={!!errors.category}
          invalidText={errors.category}
        >
          <SelectItem value="" text="Pilih kategori" disabled hidden />
          {CATEGORY_OPTIONS.map((o) => (
            <SelectItem key={o.value} value={o.value} text={o.label} />
          ))}
        </Select>
        <Select
          id="material-unit"
          labelText="Satuan"
          value={form.unit}
          onChange={(e) => set('unit', e.target.value as Unit)}
          invalid={!!errors.unit}
          invalidText={errors.unit}
        >
          <SelectItem value="" text="Pilih satuan" disabled hidden />
          {UNIT_OPTIONS.map((o) => (
            <SelectItem key={o.value} value={o.value} text={o.label} />
          ))}
        </Select>
      </div>
    </FormModal>
  )
}
