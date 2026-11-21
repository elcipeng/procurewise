import { useState, type FormEvent } from 'react'
import { DatePicker, DatePickerInput, NumberInput, Select, SelectItem, TextArea } from '@carbon/react'
import { FormModal } from '@/components/FormModal'
import { useMaterials } from '@/hooks/useMaterials'
import { useCreateProcurementRequest } from '@/hooks/useProcurementRequests'
import { handleMutationError, type FieldErrors } from '@/lib/feedback'
import { toast } from '@/lib/toast'
import { todayInJakarta, toIsoDate } from '@/lib/format'
import { PRIORITY_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
import type { Priority, ProcurementRequest } from '@/types/procurement'

const FORM_ID = 'procurement-request-form'
const FORM_FIELDS = ['material_id', 'qty', 'needed_by', 'priority', 'max_budget', 'notes'] as const
const PRIORITY_OPTIONS = toOptions(PRIORITY_LABELS)
const NOTES_MAX_LENGTH = 1000
// tampilan tanggal format indonesia, nilai yang dikirim ke API tetap yyyy-mm-dd
const DISPLAY_DATE_FORMAT = 'd/m/Y'

type FormState = {
  material_id: string
  qty: string
  needed_by: string
  priority: Priority
  max_budget: string
  notes: string
}

const EMPTY_FORM: FormState = {
  material_id: '',
  qty: '',
  needed_by: '',
  priority: 'normal',
  max_budget: '',
  notes: '',
}

type ProcurementRequestFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: (request: ProcurementRequest) => void
}

export function ProcurementRequestFormDialog({ open, onOpenChange, onCreated }: ProcurementRequestFormDialogProps) {
  // form dipasang ulang setiap modal dibuka supaya isian dan error lama tidak tersisa
  return open ? <RequestForm onCancel={() => onOpenChange(false)} onCreated={onCreated} /> : null
}

function RequestForm({
  onCancel,
  onCreated,
}: {
  onCancel: () => void
  onCreated: (request: ProcurementRequest) => void
}) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState<FieldErrors>({})
  const materials = useMaterials()
  const create = useCreateProcurementRequest()
  const today = todayInJakarta()

  const selectedMaterial = materials.data?.find((m) => String(m.id) === form.material_id)

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setErrors((current) => ({ ...current, [key]: '' }))
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const missing: FieldErrors = {}
    if (!form.material_id) missing.material_id = 'Pilih material yang dibutuhkan'
    if (!form.qty.trim()) missing.qty = 'Isi jumlah kebutuhan'
    else if (!Number.isFinite(Number(form.qty))) missing.qty = 'Jumlah harus berupa angka'
    if (!form.needed_by) missing.needed_by = 'Isi tanggal paling lambat barang dibutuhkan'
    if (form.max_budget.trim() && !Number.isFinite(Number(form.max_budget)))
      missing.max_budget = 'Budget harus berupa angka'
    if (Object.keys(missing).length > 0) {
      setErrors(missing)
      return
    }

    const input = {
      material_id: Number(form.material_id),
      qty: Number(form.qty),
      needed_by: form.needed_by,
      priority: form.priority,
      max_budget: form.max_budget.trim() ? Number(form.max_budget) : null,
      notes: form.notes.trim() || null,
    }
    create.mutate(input, {
      onSuccess: (response) => {
        toast.success(response.message)
        onCreated(response.data)
      },
      onError: (error) => setErrors(handleMutationError(error, FORM_FIELDS)),
    })
  }

  return (
    <FormModal
      open
      onClose={onCancel}
      formId={FORM_ID}
      title="Tambah kebutuhan procurement"
      description="Setelah disimpan, sistem langsung menyusun peringkat vendor untuk kebutuhan ini."
      submitLabel="Simpan dan buat rekomendasi"
      isPending={create.isPending}
      onSubmit={submit}
    >
      <Select
        id="request-material_id"
        labelText="Material"
        value={form.material_id}
        onChange={(e) => set('material_id', e.target.value)}
        invalid={!!errors.material_id}
        invalidText={errors.material_id}
      >
        <SelectItem value="" text={materials.isPending ? 'Memuat material...' : 'Pilih material'} disabled hidden />
        {(materials.data ?? []).map((m) => (
          <SelectItem key={m.id} value={String(m.id)} text={`${m.code} - ${m.name}`} />
        ))}
      </Select>
      <div className="pw-form__row">
        <NumberInput
          id="request-qty"
          label={selectedMaterial ? `Jumlah (${UNIT_LABELS[selectedMaterial.unit]})` : 'Jumlah'}
          min={1}
          allowEmpty
          value={form.qty}
          onChange={(_event, { value }) => set('qty', String(value))}
          invalid={!!errors.qty}
          invalidText={errors.qty}
        />
        <DatePicker
          datePickerType="single"
          dateFormat={DISPLAY_DATE_FORMAT}
          minDate={new Date(`${today}T00:00:00`)}
          value={form.needed_by ? new Date(`${form.needed_by}T00:00:00`) : undefined}
          onChange={([date]) => set('needed_by', date ? toIsoDate(date) : '')}
        >
          <DatePickerInput
            id="request-needed_by"
            labelText="Dibutuhkan paling lambat"
            placeholder="hh/bb/tttt"
            invalid={!!errors.needed_by}
            invalidText={errors.needed_by}
          />
        </DatePicker>
      </div>
      <div className="pw-form__row">
        <Select
          id="request-priority"
          labelText="Prioritas"
          helperText="Tinggi berarti ketepatan waktu lebih penting dari harga"
          value={form.priority}
          onChange={(e) => set('priority', e.target.value as Priority)}
          invalid={!!errors.priority}
          invalidText={errors.priority}
        >
          {PRIORITY_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value} text={option.label} />
          ))}
        </Select>
        <NumberInput
          id="request-max_budget"
          label="Budget maksimal (Rp) (opsional)"
          min={0}
          allowEmpty
          hideSteppers
          value={form.max_budget}
          onChange={(_event, { value }) => set('max_budget', String(value))}
          invalid={!!errors.max_budget}
          invalidText={errors.max_budget}
        />
      </div>
      <TextArea
        id="request-notes"
        labelText="Catatan (opsional)"
        value={form.notes}
        maxCount={NOTES_MAX_LENGTH}
        enableCounter
        onChange={(e) => set('notes', e.target.value)}
        invalid={!!errors.notes}
        invalidText={errors.notes}
      />
    </FormModal>
  )
}
