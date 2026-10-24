import type { Category } from './vendor'

export type Unit = 'pcs' | 'lembar' | 'kg'

export type Material = {
  id: number
  code: string
  name: string
  category: Category
  unit: Unit
  created_at: string
  updated_at: string
}

export type MaterialInput = {
  code: string
  name: string
  category: Category
  unit: Unit
}
