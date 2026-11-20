import { useSyncExternalStore } from 'react'
import { getSlowRequestCount, subscribeSlowRequests } from '@/api/slowRequests'

export const useSlowServer = () => useSyncExternalStore(subscribeSlowRequests, getSlowRequestCount) > 0
