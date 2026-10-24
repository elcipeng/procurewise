import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createVendor, deactivateVendor, listVendors, updateVendor } from '@/api/vendors'
import type { VendorInput } from '@/types/vendor'

const VENDORS_KEY = ['vendors'] as const

export const useVendors = () =>
  useQuery({ queryKey: VENDORS_KEY, queryFn: async () => (await listVendors()).data })

function useInvalidateVendors() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: VENDORS_KEY })
}

export function useSaveVendor() {
  const invalidate = useInvalidateVendors()
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: VendorInput }) =>
      id === undefined ? createVendor(input) : updateVendor(id, input),
    onSuccess: invalidate,
  })
}

export function useSetVendorActive() {
  const invalidate = useInvalidateVendors()
  return useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      active ? updateVendor(id, { is_active: true }) : deactivateVendor(id),
    onSuccess: invalidate,
  })
}
