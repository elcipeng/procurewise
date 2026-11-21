import { useSyncExternalStore } from 'react'
import { ToastNotification } from '@carbon/react'
import { dismissToast, getToasts, subscribeToasts } from '@/lib/toast'

// pesan sukses cepat hilang, pesan error ditahan lebih lama supaya sempat dibaca
const TIMEOUT_MS = { success: 5000, error: 10000 } as const

export function ToastRegion() {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts)
  return (
    <div className="pw-toast-region" aria-live="polite">
      {toasts.map((t) => (
        <ToastNotification
          key={t.id}
          kind={t.kind}
          title={t.title}
          subtitle={t.subtitle}
          timeout={TIMEOUT_MS[t.kind]}
          onClose={() => {
            dismissToast(t.id)
            return true
          }}
          lowContrast
        />
      ))}
    </div>
  )
}
