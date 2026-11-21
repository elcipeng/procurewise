import { Tag, Tile } from '@carbon/react'
import { VENDOR_METRICS, bestVendorIds } from '@/lib/vendorMetrics'
import type { RankedVendor } from '@/types/recommendation'
import { FactorList } from './FactorList'

const COMPARED_VENDORS = 3

export function TopVendorComparison({ vendors }: { vendors: RankedVendor[] }) {
  const top = vendors.slice(0, COMPARED_VENDORS)
  const best = new Map(VENDOR_METRICS.map((metric) => [metric.id, bestVendorIds(top, metric)]))

  return (
    <div className="pw-compare">
      {top.map((vendor) => (
        <Tile key={vendor.vendor_id} className={vendor.rank === 1 ? 'pw-tile pw-compare__tile--first' : 'pw-tile'}>
          <div className="pw-compare__tags">
            <Tag type={vendor.rank === 1 ? 'high-contrast' : 'gray'} size="sm">
              Peringkat {vendor.rank}
            </Tag>
            {!vendor.history.has_history && (
              <Tag type="warm-gray" size="sm">
                Data terbatas
              </Tag>
            )}
          </div>
          <h4 className="pw-compare__name">{vendor.vendor_name}</h4>
          <p className="pw-caption">{vendor.vendor_city}</p>
          <dl className="pw-metrics">
            {VENDOR_METRICS.map((metric) => {
              const isBest = best.get(metric.id)?.has(vendor.vendor_id)
              return (
                <div key={metric.id} className={isBest ? 'pw-metrics__row pw-metrics__row--best' : 'pw-metrics__row'}>
                  <dt>{metric.label}</dt>
                  <dd className="pw-numeric">{metric.format(metric.value(vendor))}</dd>
                </div>
              )
            })}
          </dl>
          {/* metode cadangan weighted sum tidak punya kontribusi fitur, jadi bagian ini disembunyikan */}
          {vendor.top_factors.length > 0 && (
            <div>
              <p className="pw-label">Faktor utama peringkat</p>
              <FactorList factors={vendor.top_factors} />
            </div>
          )}
        </Tile>
      ))}
    </div>
  )
}
