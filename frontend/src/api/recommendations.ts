import type { RecommendationResult } from '@/types/recommendation'
import { http, unwrap } from './client'

// menjalankan ulang untuk request yang sama menggantikan ranking sebelumnya di backend
export const runRecommendation = (requestId: number) =>
  unwrap<RecommendationResult>(http.post('/recommendations', { request_id: requestId }))

export const getRecommendation = (requestId: number) =>
  unwrap<RecommendationResult>(http.get(`/recommendations/${requestId}`))
