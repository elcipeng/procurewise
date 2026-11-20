import { Loader2 } from 'lucide-react'
import { useSlowServer } from '@/hooks/useSlowServer'

export function SlowServerNotice() {
  if (!useSlowServer()) return null
  return (
    <div
      role="status"
      className="flex items-center gap-2 border-b bg-warning-soft px-4 py-2 text-warning-soft-foreground sm:px-6 lg:px-8"
    >
      <Loader2 className="size-4 shrink-0 animate-spin" aria-hidden />
      Server sedang disiapkan, mohon tunggu sebentar
    </div>
  )
}
