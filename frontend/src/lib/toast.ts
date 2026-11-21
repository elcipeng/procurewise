export type ToastKind = 'success' | 'error'

export type ToastMessage = {
  id: number
  kind: ToastKind
  title: string
  subtitle?: string
}

type ToastOptions = { description?: string }

const listeners = new Set<() => void>()
let toasts: ToastMessage[] = []
let nextId = 1

function emit(next: ToastMessage[]) {
  toasts = next
  listeners.forEach((listener) => listener())
}

function push(kind: ToastKind, title: string, options?: ToastOptions) {
  emit([...toasts, { id: nextId++, kind, title, subtitle: options?.description }])
}

export const subscribeToasts = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export const getToasts = () => toasts

export const dismissToast = (id: number) => emit(toasts.filter((t) => t.id !== id))

/** antrean toast global supaya hook dan handler error bisa menampilkan pesan tanpa prop drilling */
export const toast = {
  success: (title: string, options?: ToastOptions) => push('success', title, options),
  error: (title: string, options?: ToastOptions) => push('error', title, options),
}
