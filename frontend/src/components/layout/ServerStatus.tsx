import { useHealth } from '@/hooks/useHealth'
import { cn } from '@/lib/utils'

export function ServerStatus() {
  const { data, isPending, isError } = useHealth()
  const connected = !isError && data?.database === 'ok'
  const label = isPending ? 'Memeriksa server' : connected ? 'Server terhubung' : 'Server tidak terhubung'

  return (
    <div className="flex items-center gap-2 text-caption text-muted-foreground" role="status">
      <span
        className={cn(
          'size-2 rounded-full',
          isPending ? 'bg-muted-foreground/40' : connected ? 'bg-success' : 'bg-destructive',
        )}
        aria-hidden
      />
      {label}
    </div>
  )
}
