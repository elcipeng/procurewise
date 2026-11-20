import type { Explanation } from '@/types/explanation'
import type { RecommendationResult } from '@/types/recommendation'
import { http, unwrap } from './client'

// menjalankan ulang untuk request yang sama menggantikan ranking sebelumnya di backend
export const runRecommendation = (requestId: number) =>
  unwrap<RecommendationResult>(http.post('/recommendations', { request_id: requestId }))

export const getRecommendation = (requestId: number) =>
  unwrap<RecommendationResult>(http.get(`/recommendations/${requestId}`))

// dua percobaan Gemini masing-masing bisa sampai 20 detik di backend, jadi batas waktu axios bawaan tidak cukup
const EXPLANATION_TIMEOUT_MS = 60_000

export const getExplanation = (requestId: number) =>
  unwrap<Explanation>(http.post(`/recommendations/${requestId}/explanation`, null, { timeout: EXPLANATION_TIMEOUT_MS }))
