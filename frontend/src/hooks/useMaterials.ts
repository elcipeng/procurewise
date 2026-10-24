import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createMaterial, deleteMaterial, listMaterials, updateMaterial } from '@/api/materials'
import type { MaterialInput } from '@/types/material'

const MATERIALS_KEY = ['materials'] as const

export const useMaterials = () =>
  useQuery({ queryKey: MATERIALS_KEY, queryFn: async () => (await listMaterials()).data })

function useInvalidateMaterials() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: MATERIALS_KEY })
}

export function useSaveMaterial() {
  const invalidate = useInvalidateMaterials()
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: MaterialInput }) =>
      id === undefined ? createMaterial(input) : updateMaterial(id, input),
    onSuccess: invalidate,
  })
}

export function useDeleteMaterial() {
  const invalidate = useInvalidateMaterials()
  return useMutation({ mutationFn: (id: number) => deleteMaterial(id), onSuccess: invalidate })
}
