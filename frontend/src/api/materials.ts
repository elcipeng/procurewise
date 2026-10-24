import type { Material, MaterialInput } from '@/types/material'
import { http, unwrap } from './client'

export const listMaterials = () => unwrap<Material[]>(http.get('/materials'))

export const createMaterial = (input: MaterialInput) => unwrap<Material>(http.post('/materials', input))

export const updateMaterial = (id: number, input: Partial<MaterialInput>) =>
  unwrap<Material>(http.patch(`/materials/${id}`, input))

export const deleteMaterial = (id: number) => unwrap<null>(http.delete(`/materials/${id}`))
