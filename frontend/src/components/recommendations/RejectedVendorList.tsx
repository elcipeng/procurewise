import { CircleX } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { formatRupiah } from '@/lib/format'
import type { RejectedVendor } from '@/types/recommendation'

export function RejectedVendorList({ vendors }: { vendors: RejectedVendor[] }) {
  return (
    <Card className="gap-0 divide-y py-0 shadow-card">
      {vendors.map((vendor) => (
        <div key={vendor.vendor_id} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-start sm:gap-6">
          <div className="sm:w-64 sm:shrink-0">
            <p className="font-medium text-foreground">{vendor.vendor_name}</p>
            <p className="text-caption text-muted-foreground">
              {vendor.vendor_city}, {formatRupiah(vendor.offer.unit_price)} per satuan
            </p>
          </div>
          <ul className="flex flex-col gap-1">
            {vendor.reasons.map((reason) => (
              <li key={reason.code} className="flex items-start gap-1.5 text-muted-foreground">
                <CircleX className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden />
                <span>{reason.message}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </Card>
  )
}
