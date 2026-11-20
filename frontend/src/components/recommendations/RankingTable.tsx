import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { VENDOR_METRICS } from '@/lib/vendorMetrics'
import type { RankedVendor } from '@/types/recommendation'

export function RankingTable({ vendors }: { vendors: RankedVendor[] }) {
  return (
    <Card className="gap-0 overflow-hidden py-0 shadow-card">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/60 hover:bg-muted/60">
              <TableHead className="text-caption font-medium text-muted-foreground">Peringkat</TableHead>
              <TableHead className="text-caption font-medium text-muted-foreground">Vendor</TableHead>
              {VENDOR_METRICS.map((metric) => (
                <TableHead
                  key={metric.id}
                  className="text-right text-caption font-medium whitespace-normal text-muted-foreground"
                >
                  {metric.label}
                </TableHead>
              ))}
              <TableHead className="text-right text-caption font-medium text-muted-foreground">Transaksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {vendors.map((vendor) => (
              <TableRow key={vendor.vendor_id}>
                <TableCell className="font-semibold tabular-nums">{vendor.rank}</TableCell>
                <TableCell>
                  <p className="min-w-40 font-medium text-foreground">{vendor.vendor_name}</p>
                  <p className="text-caption text-muted-foreground">{vendor.vendor_city}</p>
                </TableCell>
                {VENDOR_METRICS.map((metric) => {
                  const value = metric.value(vendor)
                  return (
                    <TableCell
                      key={metric.id}
                      className={cn(
                        'text-right whitespace-nowrap tabular-nums',
                        metric.id === 'slack' && value < 0 && 'text-destructive',
                        metric.fromHistory && !vendor.history.has_history && 'text-muted-foreground',
                      )}
                    >
                      {metric.format(value)}
                    </TableCell>
                  )
                })}
                <TableCell className="text-right whitespace-nowrap text-muted-foreground tabular-nums">
                  {vendor.history.has_history ? vendor.history.n_transactions : 'Belum ada'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}
