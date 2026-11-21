import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@carbon/react'
import { VENDOR_METRICS } from '@/lib/vendorMetrics'
import type { RankedVendor } from '@/types/recommendation'

function metricClass(vendor: RankedVendor, metricId: string, value: number, fromHistory?: boolean) {
  const classes = ['pw-numeric', 'pw-nowrap', 'pw-align-end']
  // sisa waktu negatif berarti janji lead time sudah melewati tanggal dibutuhkan
  if (metricId === 'slack' && value < 0) classes.push('pw-text-error')
  if (fromHistory && !vendor.history.has_history) classes.push('pw-text-secondary')
  return classes.join(' ')
}

export function RankingTable({ vendors }: { vendors: RankedVendor[] }) {
  return (
    <TableContainer className="pw-table">
      <div className="pw-table__scroll">
        <Table size="md">
          <TableHead>
            <TableRow>
              <TableHeader>Peringkat</TableHeader>
              <TableHeader>Vendor</TableHeader>
              {VENDOR_METRICS.map((metric) => (
                <TableHeader key={metric.id} className="pw-align-end">
                  {metric.label}
                </TableHeader>
              ))}
              <TableHeader className="pw-align-end">Transaksi</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {vendors.map((vendor) => (
              <TableRow key={vendor.vendor_id}>
                <TableCell className="pw-numeric pw-strong">{vendor.rank}</TableCell>
                <TableCell>
                  <div className="pw-cell-stack pw-cell-wide">
                    <span>{vendor.vendor_name}</span>
                    <span className="pw-caption">{vendor.vendor_city}</span>
                  </div>
                </TableCell>
                {VENDOR_METRICS.map((metric) => {
                  const value = metric.value(vendor)
                  return (
                    <TableCell key={metric.id} className={metricClass(vendor, metric.id, value, metric.fromHistory)}>
                      {metric.format(value)}
                    </TableCell>
                  )
                })}
                <TableCell className="pw-numeric pw-nowrap pw-align-end pw-text-secondary">
                  {vendor.history.has_history ? vendor.history.n_transactions : 'Belum ada'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </TableContainer>
  )
}
