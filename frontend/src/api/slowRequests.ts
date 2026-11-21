import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'

// server hosting gratis tidur saat sepi, request pertama setelahnya bisa makan puluhan detik
const SLOW_THRESHOLD_MS = 5000
// penjelasan Gemini memang lama dan sudah punya state loading sendiri di panelnya
const EXCLUDED_SUFFIXES = ['/explanation']

type Tracked = { timer: ReturnType<typeof setTimeout>; slow: boolean }

const tracked = new WeakMap<InternalAxiosRequestConfig, Tracked>()
const listeners = new Set<() => void>()
let slowCount = 0

function setSlowCount(next: number) {
  slowCount = next
  listeners.forEach((listener) => listener())
}

function finish(config: InternalAxiosRequestConfig | undefined) {
  const entry = config && tracked.get(config)
  if (!entry || !config) return
  clearTimeout(entry.timer)
  tracked.delete(config)
  if (entry.slow) setSlowCount(slowCount - 1)
}

export const subscribeSlowRequests = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export const getSlowRequestCount = () => slowCount

/** menandai request yang belum selesai setelah beberapa detik supaya UI bisa menampilkan pesan server sedang disiapkan */
export function trackSlowRequests(instance: AxiosInstance) {
  instance.interceptors.request.use((config) => {
    if (EXCLUDED_SUFFIXES.some((suffix) => config.url?.endsWith(suffix))) return config
    const entry: Tracked = {
      slow: false,
      timer: setTimeout(() => {
        entry.slow = true
        setSlowCount(slowCount + 1)
      }, SLOW_THRESHOLD_MS),
    }
    tracked.set(config, entry)
    return config
  })
  instance.interceptors.response.use(
    (response) => {
      finish(response.config)
      return response
    },
    (error) => {
      finish(error?.config)
      return Promise.reject(error)
    },
  )
}
