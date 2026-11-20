import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import type { FeatureFactor } from '@/types/recommendation'

/** faktor dengan kontribusi TreeSHAP terbesar, arah panah menunjukkan menaikkan atau menurunkan peringkat */
export function FactorList({ factors }: { factors: FeatureFactor[] }) {
  return (
    <ul className="flex flex-col gap-1.5">
      {factors.map((factor) => {
        const raises = factor.contribution >= 0
        const Icon = raises ? ArrowUpRight : ArrowDownRight
        return (
          <li key={factor.feature} className="flex items-start gap-1.5">
            <Icon
              className={raises ? 'mt-0.5 size-4 shrink-0 text-success' : 'mt-0.5 size-4 shrink-0 text-destructive'}
              aria-label={raises ? 'menaikkan peringkat' : 'menurunkan peringkat'}
            />
            <span>{factor.label}</span>
          </li>
        )
      })}
    </ul>
  )
}
