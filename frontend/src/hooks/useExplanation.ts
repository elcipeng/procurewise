import { useQuery } from '@tanstack/react-query'
import { getExplanation } from '@/api/recommendations'

// ranked_at ikut di key supaya penjelasan dimuat ulang setiap kali peringkat disusun ulang
export const useExplanation = (requestId: number, rankedAt: string) =>
  useQuery({
    queryKey: ['explanation', requestId, rankedAt],
    queryFn: async () => (await getExplanation(requestId)).data,
    staleTime: Infinity,
    retry: false,
  })
