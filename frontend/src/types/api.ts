export type FieldError = {
  field: string
  error: string
}

export type PageMeta = {
  page: number
  page_size: number
  total: number
}

export type ApiEnvelope<T> = {
  status: number
  message: string
  timestamp: string
  data: T
  meta?: PageMeta
}
