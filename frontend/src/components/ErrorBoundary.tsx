import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@carbon/react'
import { Renew } from '@carbon/icons-react'

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
      <div className="pw-empty-state">
        <p className="pw-empty-state__title">Tampilan gagal dimuat</p>
        <p>Data tetap aman. Muat ulang halaman untuk mencoba lagi.</p>
        <Button kind="tertiary" renderIcon={Renew} onClick={() => window.location.reload()}>
          Muat ulang
        </Button>
      </div>
    )
  }
}
