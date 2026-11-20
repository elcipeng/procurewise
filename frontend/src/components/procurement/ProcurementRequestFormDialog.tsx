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
import { Textarea } from '@/components/ui/textarea'
import { useMaterials } from '@/hooks/useMaterials'
import { useCreateProcurementRequest } from '@/hooks/useProcurementRequests'
import { fieldErrorId, handleMutationError, type FieldErrors } from '@/lib/feedback'
import { todayInJakarta } from '@/lib/format'
import { PRIORITY_LABELS, UNIT_LABELS, toOptions } from '@/lib/labels'
import type { Priority, ProcurementRequest } from '@/types/procurement'

const FORM_FIELDS = ['material_id', 'qty', 'needed_by', 'priority', 'max_budget', 'notes'] as const
const PRIORITY_OPTIONS = toOptions(PRIORITY_LABELS)
const NOTES_MAX_LENGTH = 1000

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
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Tambah kebutuhan procurement</DialogTitle>
          <DialogDescription>
            Setelah disimpan, sistem langsung menyusun peringkat vendor untuk kebutuhan ini.
          </DialogDescription>
        </DialogHeader>
        {open && <RequestForm onCancel={() => onOpenChange(false)} onCreated={onCreated} />}
      </DialogContent>
    </Dialog>
  )
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

  const materialOptions = (materials.data ?? []).map((m) => ({ value: String(m.id), label: `${m.code} - ${m.name}` }))
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

  const describe = (field: keyof FormState) => (errors[field] ? fieldErrorId(`request-${field}`) : undefined)

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <FormField id="request-material_id" label="Material" error={errors.material_id}>
        <OptionSelect
          id="request-material_id"
          value={form.material_id}
          onValueChange={(value) => set('material_id', value)}
          options={materialOptions}
          placeholder={materials.isPending ? 'Memuat material...' : 'Pilih material'}
          invalid={!!errors.material_id}
          describedBy={describe('material_id')}
        />
      </FormField>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          id="request-qty"
          label={selectedMaterial ? `Jumlah (${UNIT_LABELS[selectedMaterial.unit]})` : 'Jumlah'}
          error={errors.qty}
        >
          <Input
            id="request-qty"
            type="number"
            inputMode="numeric"
            min={1}
            value={form.qty}
            onChange={(e) => set('qty', e.target.value)}
            aria-invalid={!!errors.qty || undefined}
            aria-describedby={describe('qty')}
          />
        </FormField>
        <FormField id="request-needed_by" label="Dibutuhkan paling lambat" error={errors.needed_by}>
          <Input
            id="request-needed_by"
            type="date"
            min={today}
            value={form.needed_by}
            onChange={(e) => set('needed_by', e.target.value)}
            aria-invalid={!!errors.needed_by || undefined}
            aria-describedby={describe('needed_by')}
          />
        </FormField>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          id="request-priority"
          label="Prioritas"
          hint="Tinggi berarti ketepatan waktu lebih penting dari harga"
          error={errors.priority}
        >
          <OptionSelect
            id="request-priority"
            value={form.priority}
            onValueChange={(value) => set('priority', value as Priority)}
            options={PRIORITY_OPTIONS}
            invalid={!!errors.priority}
            describedBy={describe('priority')}
          />
        </FormField>
        <FormField id="request-max_budget" label="Budget maksimal (Rp)" optional error={errors.max_budget}>
          <Input
            id="request-max_budget"
            type="number"
            inputMode="decimal"
            min={0}
            value={form.max_budget}
            onChange={(e) => set('max_budget', e.target.value)}
            aria-invalid={!!errors.max_budget || undefined}
            aria-describedby={describe('max_budget')}
          />
        </FormField>
      </div>
      <FormField id="request-notes" label="Catatan" optional error={errors.notes}>
        <Textarea
          id="request-notes"
          value={form.notes}
          maxLength={NOTES_MAX_LENGTH}
          onChange={(e) => set('notes', e.target.value)}
          aria-invalid={!!errors.notes || undefined}
          aria-describedby={describe('notes')}
        />
      </FormField>
      <DialogFooter className="mt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={create.isPending}>
          Batal
        </Button>
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? 'Menyimpan...' : 'Simpan dan buat rekomendasi'}
        </Button>
      </DialogFooter>
    </form>
  )
}
