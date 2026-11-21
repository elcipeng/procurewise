import { ArrowDownRight, ArrowUpRight } from '@carbon/icons-react'
import type { FeatureFactor } from '@/types/recommendation'

/** faktor dengan kontribusi TreeSHAP terbesar, arah panah menunjukkan menaikkan atau menurunkan peringkat */
export function FactorList({ factors }: { factors: FeatureFactor[] }) {
  return (
    <ul className="pw-icon-list">
      {factors.map((factor) => {
        const raises = factor.contribution >= 0
        const Icon = raises ? ArrowUpRight : ArrowDownRight
        return (
          <li key={factor.feature}>
            <Icon
              className={raises ? 'pw-icon--success' : 'pw-icon--error'}
              aria-label={raises ? 'menaikkan peringkat' : 'menurunkan peringkat'}
            />
            <span>{factor.label}</span>
          </li>
        )
      })}
    </ul>
  )
}
