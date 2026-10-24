import type { Vendor, VendorInput } from '@/types/vendor'
import { http, unwrap } from './client'

export const listVendors = () => unwrap<Vendor[]>(http.get('/vendors'))

export const createVendor = (input: VendorInput) => unwrap<Vendor>(http.post('/vendors', input))

export const updateVendor = (id: number, input: Partial<VendorInput>) =>
  unwrap<Vendor>(http.patch(`/vendors/${id}`, input))

// soft delete di backend, vendor hanya dinonaktifkan supaya histori transaksi tetap utuh
export const deactivateVendor = (id: number) => unwrap<Vendor>(http.delete(`/vendors/${id}`))
