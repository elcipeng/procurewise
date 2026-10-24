export type Category = 'bahan' | 'jasa' | 'packaging'
export type PaymentTerms = 'cash' | 'dp_50' | 'tempo_14' | 'tempo_30'

export type Vendor = {
  id: number
  name: string
  category: Category
  city: string
  contact: string | null
  payment_terms: PaymentTerms
  is_active: boolean
  created_at: string
  updated_at: string
}

export type VendorInput = {
  name: string
  category: Category
  city: string
  contact: string | null
  payment_terms: PaymentTerms
  is_active: boolean
}
