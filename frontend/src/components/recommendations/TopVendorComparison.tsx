import { StatusBadge } from '@/components/StatusBadge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { VENDOR_METRICS, bestVendorIds } from '@/lib/vendorMetrics'
import type { RankedVendor } from '@/types/recommendation'
import { FactorList } from './FactorList'

const COMPARED_VENDORS = 3

export function TopVendorComparison({ vendors }: { vendors: RankedVendor[] }) {
  const top = vendors.slice(0, COMPARED_VENDORS)
  const best = new Map(VENDOR_METRICS.map((metric) => [metric.id, bestVendorIds(top, metric)]))

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {top.map((vendor) => (
        <Card key={vendor.vendor_id} className={cn('gap-4 shadow-card', vendor.rank === 1 && 'border-primary')}>
          <CardHeader className="gap-1">
            <div className="flex items-center justify-between gap-2">
              <span
                className={cn(
                  'rounded-md px-2 py-0.5 text-caption font-semibold',
                  vendor.rank === 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
                )}
              >
                Peringkat {vendor.rank}
              </span>
              {!vendor.history.has_history && <StatusBadge tone="warning" label="Data terbatas" />}
            </div>
            <CardTitle className="text-heading">{vendor.vendor_name}</CardTitle>
            <p className="text-caption text-muted-foreground">{vendor.vendor_city}</p>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <dl className="flex flex-col gap-1">
              {VENDOR_METRICS.map((metric) => {
                const isBest = best.get(metric.id)?.has(vendor.vendor_id)
                return (
                  <div
                    key={metric.id}
                    className={cn(
                      'flex items-center justify-between gap-3 rounded-md px-2 py-1',
                      isBest && 'bg-success-soft text-success-soft-foreground',
                    )}
                  >
                    <dt className={cn(!isBest && 'text-muted-foreground')}>{metric.label}</dt>
                    <dd className="font-medium tabular-nums">{metric.format(metric.value(vendor))}</dd>
                  </div>
                )
              })}
            </dl>
            {/* metode cadangan weighted sum tidak punya kontribusi fitur, jadi bagian ini disembunyikan */}
            {vendor.top_factors.length > 0 && (
              <div>
                <p className="mb-2 text-caption font-medium text-muted-foreground">Faktor utama peringkat</p>
                <FactorList factors={vendor.top_factors} />
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
