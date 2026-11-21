import { CheckmarkFilled, CircleDash, ErrorFilled } from '@carbon/icons-react'
import { useHealth } from '@/hooks/useHealth'

export function ServerStatus() {
  const { data, isPending, isError } = useHealth()
  const connected = !isError && data?.database === 'ok'
  const label = isPending ? 'Memeriksa server' : connected ? 'Server terhubung' : 'Server tidak terhubung'
  const Icon = isPending ? CircleDash : connected ? CheckmarkFilled : ErrorFilled
  const tone = isPending ? '' : connected ? 'pw-server-status--ok' : 'pw-server-status--error'

  return (
    <div className={`pw-server-status ${tone}`} role="status">
      <Icon aria-hidden />
      <span className="pw-server-status__label">{label}</span>
    </div>
  )
}
