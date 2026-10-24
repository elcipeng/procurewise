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
import { useSaveVendor } from '@/hooks/useVendors'
import { fieldErrorId, handleMutationError, type FieldErrors } from '@/lib/feedback'
import { CATEGORY_LABELS, PAYMENT_TERMS_LABELS, toOptions } from '@/lib/labels'
import type { Category, PaymentTerms, Vendor } from '@/types/vendor'

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
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{vendor ? 'Ubah vendor' : 'Tambah vendor'}</DialogTitle>
          <DialogDescription>
            {vendor ? 'Perbarui data vendor.' : 'Vendor baru langsung berstatus aktif.'}
          </DialogDescription>
        </DialogHeader>
        {open && <VendorForm vendor={vendor} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  )
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

  const describe = (field: keyof FormState) => (errors[field] ? fieldErrorId(`vendor-${field}`) : undefined)

  return (
    <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
      <FormField id="vendor-name" label="Nama vendor" error={errors.name}>
        <Input
          id="vendor-name"
          value={form.name}
          onChange={(e) => set('name', e.target.value)}
          aria-invalid={!!errors.name || undefined}
          aria-describedby={describe('name')}
          autoFocus
        />
      </FormField>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField id="vendor-category" label="Kategori" error={errors.category}>
          <OptionSelect
            id="vendor-category"
            value={form.category}
            onValueChange={(value) => set('category', value as Category)}
            options={CATEGORY_OPTIONS}
            placeholder="Pilih kategori"
            invalid={!!errors.category}
            describedBy={describe('category')}
          />
        </FormField>
        <FormField id="vendor-city" label="Kota" error={errors.city}>
          <Input
            id="vendor-city"
            value={form.city}
            onChange={(e) => set('city', e.target.value)}
            aria-invalid={!!errors.city || undefined}
            aria-describedby={describe('city')}
          />
        </FormField>
      </div>
      <FormField id="vendor-contact" label="Kontak" optional hint="Email atau nomor telepon" error={errors.contact}>
        <Input
          id="vendor-contact"
          value={form.contact}
          onChange={(e) => set('contact', e.target.value)}
          aria-invalid={!!errors.contact || undefined}
          aria-describedby={describe('contact')}
        />
      </FormField>
      <FormField id="vendor-payment_terms" label="Termin pembayaran" error={errors.payment_terms}>
        <OptionSelect
          id="vendor-payment_terms"
          value={form.payment_terms}
          onValueChange={(value) => set('payment_terms', value as PaymentTerms)}
          options={PAYMENT_TERMS_OPTIONS}
          placeholder="Pilih termin pembayaran"
          invalid={!!errors.payment_terms}
          describedBy={describe('payment_terms')}
        />
      </FormField>
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
