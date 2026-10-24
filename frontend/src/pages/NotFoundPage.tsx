import { Link } from 'react-router'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center gap-3 py-20 text-center">
      <p className="text-title">Halaman tidak ditemukan</p>
      <p className="text-muted-foreground">Alamat yang dibuka tidak tersedia di ProcureWise.</p>
      <Button asChild variant="outline" className="mt-2">
        <Link to="/vendor">Kembali ke daftar vendor</Link>
      </Button>
    </div>
  )
}
