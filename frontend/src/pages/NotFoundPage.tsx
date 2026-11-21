import { Button } from '@carbon/react'
import { useNavigate } from 'react-router'

export function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <div className="pw-empty-state">
      <p className="pw-empty-state__title">Halaman tidak ditemukan</p>
      <p>Alamat yang dibuka tidak tersedia di ProcureWise.</p>
      <Button kind="tertiary" onClick={() => navigate('/kebutuhan')}>
        Kembali ke daftar kebutuhan
      </Button>
    </div>
  )
}
