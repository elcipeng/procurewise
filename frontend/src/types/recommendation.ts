import type { ProcurementRequest } from './procurement'

export type OfferSnapshot = {
  unit_price: number
  moq: number
  quoted_lead_time_days: number
  weekly_capacity: number
  is_available: boolean
}

export type VendorHistory = {
  on_time_rate: number
  avg_delay_days: number
  defect_rate: number
  avg_rating: number
  n_transactions: number
  has_history: boolean
}

export type FeatureFactor = {
  feature: string
  label: string
  value: number
  contribution: number
}

export type RankedVendor = {
  vendor_id: number
  vendor_name: string
  vendor_city: string
  rank: number
  score: number
  offer: OfferSnapshot
  total_cost: number
  slack_days: number
  history: VendorHistory
  top_factors: FeatureFactor[]
}

export type RejectedVendor = {
  vendor_id: number
  vendor_name: string
  vendor_city: string
  offer: OfferSnapshot
  total_cost: number
  reasons: { code: string; message: string }[]
}

export type RecommendationResult = {
  request: ProcurementRequest
  model_version: string
  is_fallback: boolean
  ranked_at: string
  ranked: RankedVendor[]
  rejected: RejectedVendor[]
}
