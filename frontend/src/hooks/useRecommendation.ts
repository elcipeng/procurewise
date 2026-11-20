import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { getRecommendation, runRecommendation } from '@/api/recommendations'
import { PROCUREMENT_REQUESTS_KEY } from './useProcurementRequests'

const recommendationKey = (requestId: number) => ['recommendation', requestId] as const
const NOT_FOUND = 404

export const useRecommendation = (requestId: number) =>
  useQuery({
    queryKey: recommendationKey(requestId),
    queryFn: async () => {
      try {
        return (await getRecommendation(requestId)).data
      } catch (error) {
        // kebutuhan yang belum diranking dijawab 404 oleh backend, itu keadaan normal, bukan error
        if (error instanceof ApiError && error.status === NOT_FOUND) return null
        throw error
      }
    },
  })

export function useRunRecommendation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (requestId: number) => runRecommendation(requestId),
    onSuccess: (response, requestId) => {
      queryClient.setQueryData(recommendationKey(requestId), response.data)
      // status kebutuhan berubah menjadi recommended setelah ranking dibuat
      return queryClient.invalidateQueries({ queryKey: PROCUREMENT_REQUESTS_KEY })
    },
  })
}
