import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

type Health = {
  status: string
  database: string
}

function App() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.get<Health>('/health')).data,
    retry: false,
  })

  let statusText = 'Memeriksa koneksi backend...'
  if (health.isError) statusText = 'Backend tidak dapat dihubungi'
  if (health.data) statusText = `Backend: ${health.data.status}, database: ${health.data.database}`

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2 p-6">
      <h1 className="text-2xl font-semibold">ProcureWise</h1>
      <p className="text-sm text-muted-foreground">{statusText}</p>
    </main>
  )
}

export default App
