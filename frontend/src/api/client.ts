import axios, { type AxiosResponse, isAxiosError } from 'axios'
import type { ApiEnvelope, FieldError } from '@/types/api'

const REQUEST_TIMEOUT_MS = 15000
const NETWORK_ERROR_MESSAGE = 'Server tidak dapat dihubungi. Periksa koneksi lalu coba lagi.'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: REQUEST_TIMEOUT_MS,
})

export class ApiError extends Error {
  readonly status: number
  readonly fieldErrors: FieldError[]

  constructor(status: number, message: string, fieldErrors: FieldError[] = []) {
    super(message)
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

function isEnvelope(value: unknown): value is ApiEnvelope<unknown> {
  return typeof value === 'object' && value !== null && 'status' in value && 'message' in value
}

// semua error backend memakai envelope yang sama, jadi cukup diubah sekali di sini menjadi ApiError
export async function unwrap<T>(request: Promise<AxiosResponse<ApiEnvelope<T>>>): Promise<ApiEnvelope<T>> {
  try {
    return (await request).data
  } catch (error) {
    if (isAxiosError(error) && isEnvelope(error.response?.data)) {
      const body = error.response.data
      const fieldErrors = body.status === 422 && Array.isArray(body.data) ? (body.data as FieldError[]) : []
      throw new ApiError(body.status, body.message, fieldErrors)
    }
    throw new ApiError(0, NETWORK_ERROR_MESSAGE)
  }
}
