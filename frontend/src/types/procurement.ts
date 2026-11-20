import type { Unit } from './material'
import type { Category } from './vendor'

export type Priority = 'high' | 'normal' | 'low'
export type RequestStatus = 'new' | 'recommended' | 'completed' | 'cancelled'

export type ProcurementRequest = {
  id: number
  material_id: number
  material_code: string
  material_name: string
  material_unit: Unit
  material_category: Category
  qty: number
  request_date: string
  needed_by: string
  priority: Priority
  max_budget: number | null
  notes: string | null
  status: RequestStatus
  created_at: string
}

export type ProcurementRequestInput = {
  material_id: number
  qty: number
  needed_by: string
  priority: Priority
  max_budget: number | null
  notes: string | null
}

export type RequestListParams = {
  page: number
  pageSize: number
  status?: RequestStatus
}

// penanda dari form tambah supaya halaman detail langsung menyusun rekomendasi
export type RequestDetailState = { runRecommendation?: boolean }
