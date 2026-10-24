import type { Unit } from '@/types/material'
import type { Category, PaymentTerms } from '@/types/vendor'

// nilai enum di DB berbahasa inggris atau kode, label bahasa indonesia hanya untuk tampilan
export const CATEGORY_LABELS: Record<Category, string> = {
  bahan: 'Bahan produk',
  jasa: 'Jasa bordir dan printing',
  packaging: 'Packaging',
}

export const PAYMENT_TERMS_LABELS: Record<PaymentTerms, string> = {
  cash: 'Tunai',
  dp_50: 'DP 50%',
  tempo_14: 'Tempo 14 hari',
  tempo_30: 'Tempo 30 hari',
}

export const UNIT_LABELS: Record<Unit, string> = {
  pcs: 'pcs',
  lembar: 'lembar',
  kg: 'kg',
}

export const toOptions = <T extends string>(labels: Record<T, string>) =>
  (Object.entries(labels) as [T, string][]).map(([value, label]) => ({ value, label }))
