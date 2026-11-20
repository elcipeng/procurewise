import type { ProcurementRequest, ProcurementRequestInput, RequestListParams } from '@/types/procurement'
import { http, unwrap } from './client'

export const listProcurementRequests = ({ page, pageSize, status }: RequestListParams) =>
  unwrap<ProcurementRequest[]>(http.get('/procurement-requests', { params: { page, page_size: pageSize, status } }))

export const getProcurementRequest = (id: number) => unwrap<ProcurementRequest>(http.get(`/procurement-requests/${id}`))

export const createProcurementRequest = (input: ProcurementRequestInput) =>
  unwrap<ProcurementRequest>(http.post('/procurement-requests', input))
