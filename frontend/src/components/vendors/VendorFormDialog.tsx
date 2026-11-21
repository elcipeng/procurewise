import { useState, type FormEvent } from 'react'
import { Select, SelectItem, TextInput } from '@carbon/react'
import { FormModal } from '@/components/FormModal'
import { useSaveVendor } from '@/hooks/useVendors'
import { handleMutationError, type FieldErrors } from '@/lib/feedback'
import { toast } from '@/lib/toast'
import { CATEGORY_LABELS, PAYMENT_TERMS_LABELS, toOptions } from '@/lib/labels'
import type { Category, PaymentTerms, Vendor } from '@/types/vendor'

const FORM_ID = 'vendor-form'
const FORM_FIELDS = ['name', 'category', 'city', 'contact', 'payment_terms'] as const
const CATEGORY_OPTIONS = toOptions(CATEGORY_LABELS)
const PAYMENT_TERMS_OPTIONS = toOptions(PAYMENT_TERMS_LABELS)

type FormState = {
  name: string
  category: Category | ''
  city: string
  contact: string
  payment_terms: PaymentTerms | ''
}

const toFormState = (vendor?: Vendor): FormState => ({
  name: vendor?.name ?? '',
  category: vendor?.category ?? '',
  city: vendor?.city ?? '',
  contact: vendor?.contact ?? '',
  payment_terms: vendor?.payment_terms ?? '',
})

type VendorFormDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  vendor?: Vendor
}

export function VendorFormDialog({ open, onOpenChange, vendor }: VendorFormDialogProps) {
  // form dipasang ulang setiap modal dibuka supaya isian dan error lama tidak tersisa
  return open ? <VendorForm vendor={vendor} onDone={() => onOpenChange(false)} /> : null
}

function VendorForm({ vendor, onDone }: { vendor?: Vendor; onDone: () => void }) {
  const [form, setForm] = useState(() => toFormState(vendor))
  const [errors, setErrors] = useState<FieldErrors>({})
  const save = useSaveVendor()

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setErrors((current) => ({ ...current, [key]: '' }))
  }

  const submit = (event: FormEvent) => {
    event.preventDefault()
    // pilihan kosong dicek di sini supaya pesan error tidak menampilkan kode enum dari backend
    const missing: FieldErrors = {}
    if (!form.category) missing.category = 'Pilih kategori vendor'
    if (!form.payment_terms) missing.payment_terms = 'Pilih termin pembayaran'
    if (!form.category || !form.payment_terms) {
      setErrors(missing)
      return
    }

    const input = {
      name: form.name,
      category: form.category,
      city: form.city,
      contact: form.contact.trim() || null,
      payment_terms: form.payment_terms,
      is_active: vendor?.is_active ?? true,
    }
    save.mutate(
      { id: vendor?.id, input },
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
      title={vendor ? 'Ubah vendor' : 'Tambah vendor'}
      description={vendor ? 'Perbarui data vendor.' : 'Vendor baru langsung berstatus aktif.'}
      submitLabel="Simpan"
      isPending={save.isPending}
      onSubmit={submit}
    >
      <TextInput
        id="vendor-name"
        labelText="Nama vendor"
        value={form.name}
        onChange={(e) => set('name', e.target.value)}
        invalid={!!errors.name}
        invalidText={errors.name}
        data-modal-primary-focus
      />
      <div className="pw-form__row">
        <Select
          id="vendor-category"
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
        <TextInput
          id="vendor-city"
          labelText="Kota"
          value={form.city}
          onChange={(e) => set('city', e.target.value)}
          invalid={!!errors.city}
          invalidText={errors.city}
        />
      </div>
      <TextInput
        id="vendor-contact"
        labelText="Kontak (opsional)"
        helperText="Email atau nomor telepon"
        value={form.contact}
        onChange={(e) => set('contact', e.target.value)}
        invalid={!!errors.contact}
        invalidText={errors.contact}
      />
      <Select
        id="vendor-payment_terms"
        labelText="Termin pembayaran"
        value={form.payment_terms}
        onChange={(e) => set('payment_terms', e.target.value as PaymentTerms)}
        invalid={!!errors.payment_terms}
        invalidText={errors.payment_terms}
      >
        <SelectItem value="" text="Pilih termin pembayaran" disabled hidden />
        {PAYMENT_TERMS_OPTIONS.map((o) => (
          <SelectItem key={o.value} value={o.value} text={o.label} />
        ))}
      </Select>
    </FormModal>
  )
}
