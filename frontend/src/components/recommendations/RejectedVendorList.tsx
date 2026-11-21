import {
  StructuredListBody,
  StructuredListCell,
  StructuredListHead,
  StructuredListRow,
  StructuredListWrapper,
} from '@carbon/react'
import { MisuseOutline } from '@carbon/icons-react'
import { formatRupiah } from '@/lib/format'
import type { RejectedVendor } from '@/types/recommendation'

export function RejectedVendorList({ vendors }: { vendors: RejectedVendor[] }) {
  return (
    <StructuredListWrapper className="pw-structured-list" aria-label="Vendor yang tidak memenuhi syarat">
      <StructuredListHead>
        <StructuredListRow head>
          <StructuredListCell head>Vendor</StructuredListCell>
          <StructuredListCell head>Alasan</StructuredListCell>
        </StructuredListRow>
      </StructuredListHead>
      <StructuredListBody>
        {vendors.map((vendor) => (
          <StructuredListRow key={vendor.vendor_id}>
            <StructuredListCell>
              <div className="pw-cell-stack">
                <span>{vendor.vendor_name}</span>
                <span className="pw-caption">
                  {vendor.vendor_city}, {formatRupiah(vendor.offer.unit_price)} per satuan
                </span>
              </div>
            </StructuredListCell>
            <StructuredListCell>
              <ul className="pw-icon-list">
                {vendor.reasons.map((reason) => (
                  <li key={reason.code}>
                    <MisuseOutline className="pw-icon--error" aria-hidden />
                    <span>{reason.message}</span>
                  </li>
                ))}
              </ul>
            </StructuredListCell>
          </StructuredListRow>
        ))}
      </StructuredListBody>
    </StructuredListWrapper>
  )
}
