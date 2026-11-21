import { InlineNotification } from '@carbon/react'
import { useSlowServer } from '@/hooks/useSlowServer'

export function SlowServerNotice() {
  if (!useSlowServer()) return null
  return (
    <InlineNotification
      kind="info"
      title="Server sedang disiapkan, mohon tunggu sebentar"
      hideCloseButton
      lowContrast
      className="pw-slow-notice"
    />
  )
}
