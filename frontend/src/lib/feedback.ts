import { toast } from 'sonner'
import { ApiError } from '@/api/client'

export type FieldErrors = Record<string, string>

export const fieldErrorId = (id: string) => `${id}-error`

const UNKNOWN_ERROR_MESSAGE = 'Terjadi kesalahan yang tidak terduga'

/**
 * error 422 untuk field yang ada di form dikembalikan supaya tampil di bawah field.
 * error lain (404, 409, 422 di luar field form, jaringan) ditampilkan sebagai toast.
 */
export function handleMutationError(error: unknown, formFields: readonly string[] = []): FieldErrors {
  if (!(error instanceof ApiError)) {
    toast.error(UNKNOWN_ERROR_MESSAGE)
    return {}
  }
  const fieldErrors: FieldErrors = {}
  const otherErrors: string[] = []
  for (const { field, error: message } of error.fieldErrors) {
    if (formFields.includes(field)) fieldErrors[field] = message
    else otherErrors.push(message)
  }
  if (Object.keys(fieldErrors).length === 0 || otherErrors.length > 0) {
    toast.error(error.message, otherErrors.length ? { description: otherErrors.join(', ') } : undefined)
  }
  return fieldErrors
}
