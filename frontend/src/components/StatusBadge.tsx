import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const TONES = {
  success: 'bg-success-soft text-success-soft-foreground',
  warning: 'bg-warning-soft text-warning-soft-foreground',
  neutral: 'bg-muted text-muted-foreground',
} as const

type StatusBadgeProps = {
  tone: keyof typeof TONES
  label: string
}

export function StatusBadge({ tone, label }: StatusBadgeProps) {
  return <Badge className={cn('border-transparent font-medium', TONES[tone])}>{label}</Badge>
}
