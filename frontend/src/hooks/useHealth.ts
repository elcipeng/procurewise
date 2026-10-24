import { useQuery } from '@tanstack/react-query'
import { getHealth } from '@/api/health'

const HEALTH_REFRESH_MS = 60_000

export const useHealth = () =>
  useQuery({
    queryKey: ['health'],
    queryFn: async () => (await getHealth()).data,
    refetchInterval: HEALTH_REFRESH_MS,
    retry: false,
  })
