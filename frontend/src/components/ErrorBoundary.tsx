import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

type ErrorBoundaryProps = { children: ReactNode }
type ErrorBoundaryState = { hasError: boolean }

// error render di satu halaman tidak boleh membuat seluruh aplikasi kosong
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info.componentStack)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-center">
        <p className="text-title">Tampilan gagal dimuat</p>
        <p className="text-muted-foreground">Data tetap aman. Muat ulang halaman untuk mencoba lagi.</p>
        <Button variant="outline" className="mt-2" onClick={() => window.location.reload()}>
          Muat ulang
        </Button>
      </div>
    )
  }
}
