import { formatNumber, formatPercent, formatRupiah } from '@/lib/format'
import type { RankedVendor } from '@/types/recommendation'

export type VendorMetric = {
  id: string
  label: string
  value: (vendor: RankedVendor) => number
  format: (value: number) => string
  // arah nilai yang lebih baik, dipakai untuk menandai vendor terbaik di perbandingan
  better: 'lower' | 'higher'
  fromHistory?: boolean
}

export const formatSlack = (days: number) => `${days > 0 ? '+' : ''}${formatNumber(days)} hari`

export const VENDOR_METRICS: VendorMetric[] = [
  { id: 'unit_price', label: 'Harga satuan', value: (v) => v.offer.unit_price, format: formatRupiah, better: 'lower' },
  { id: 'total_cost', label: 'Total biaya', value: (v) => v.total_cost, format: formatRupiah, better: 'lower' },
  {
    id: 'lead_time',
    label: 'Janji lead time',
    value: (v) => v.offer.quoted_lead_time_days,
    format: (d) => `${d} hari`,
    better: 'lower',
  },
  // sisa waktu negatif berarti janji lead time vendor sudah melewati tanggal dibutuhkan
  { id: 'slack', label: 'Sisa waktu', value: (v) => v.slack_days, format: formatSlack, better: 'higher' },
  {
    id: 'on_time',
    label: 'Tepat waktu',
    value: (v) => v.history.on_time_rate,
    format: formatPercent,
    better: 'higher',
    fromHistory: true,
  },
  {
    id: 'defect',
    label: 'Tingkat cacat',
    value: (v) => v.history.defect_rate,
    format: formatPercent,
    better: 'lower',
    fromHistory: true,
  },
  {
    id: 'rating',
    label: 'Rating kualitas',
    value: (v) => v.history.avg_rating,
    format: (r) => `${formatNumber(r)} dari 5`,
    better: 'higher',
    fromHistory: true,
  },
]

/**
 * vendor dengan nilai terbaik untuk satu metrik, nilai seri ikut ditandai semua.
 * untuk metrik histori, vendor tanpa histori tidak ikut dibandingkan karena nilainya hanya rata-rata kategori
 */
export function bestVendorIds(vendors: RankedVendor[], metric: VendorMetric): Set<number> {
  const compared = metric.fromHistory ? vendors.filter((v) => v.history.has_history) : vendors
  if (compared.length < 2) return new Set()
  const values = compared.map(metric.value)
  const best = metric.better === 'lower' ? Math.min(...values) : Math.max(...values)
  return new Set(compared.filter((v) => metric.value(v) === best).map((v) => v.vendor_id))
}
