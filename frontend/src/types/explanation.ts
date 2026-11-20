export type ExplanationSource = 'gemini' | 'template'
export type FallbackReason = 'api_key_kosong' | 'api_gagal' | 'batas_pemakaian' | 'angka_tidak_cocok'

export type VendorExplanation = {
  vendor_id: number
  nama_vendor: string
  kelebihan: string[]
  kekurangan: string[]
}

export type Explanation = {
  ringkasan: string
  per_vendor: VendorExplanation[]
  trade_off: string
  catatan_risiko: string[]
  source: ExplanationSource
  model: string | null
  fallback_reason: FallbackReason | null
  generated_at: string
}
