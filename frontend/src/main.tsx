import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { ToastRegion } from '@/components/ToastRegion'
import '@ibm/plex-sans/css/ibm-plex-sans-default.min.css'
import '@ibm/plex-mono/css/ibm-plex-mono-default.min.css'
import './styles/index.scss'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    // data admin jarang berubah dari luar aplikasi, refetch saat pindah tab hanya menambah request
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
      <ToastRegion />
    </QueryClientProvider>
  </StrictMode>,
)
