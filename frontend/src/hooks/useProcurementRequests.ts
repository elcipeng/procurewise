import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProcurementRequest, getProcurementRequest, listProcurementRequests } from '@/api/procurementRequests'
import type { ProcurementRequestInput, RequestListParams } from '@/types/procurement'

export const PROCUREMENT_REQUESTS_KEY = ['procurement-requests'] as const

export const useProcurementRequests = (params: RequestListParams) =>
  useQuery({
    queryKey: [...PROCUREMENT_REQUESTS_KEY, 'list', params],
    queryFn: () => listProcurementRequests(params),
    // halaman lama tetap tampil saat halaman berikutnya dimuat, supaya tabel tidak berkedip
    placeholderData: keepPreviousData,
  })

export const useProcurementRequest = (id: number) =>
  useQuery({
    queryKey: [...PROCUREMENT_REQUESTS_KEY, 'detail', id],
    queryFn: async () => (await getProcurementRequest(id)).data,
  })

export function useCreateProcurementRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProcurementRequestInput) => createProcurementRequest(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROCUREMENT_REQUESTS_KEY }),
  })
}
