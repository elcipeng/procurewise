import { Navigate, Route, Routes } from 'react-router'
import { AppLayout } from '@/components/layout/AppLayout'
import { MaterialsPage } from '@/pages/MaterialsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProcurementRequestDetailPage } from '@/pages/ProcurementRequestDetailPage'
import { ProcurementRequestsPage } from '@/pages/ProcurementRequestsPage'
import { VendorsPage } from '@/pages/VendorsPage'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/kebutuhan" replace />} />
        <Route path="kebutuhan" element={<ProcurementRequestsPage />} />
        <Route path="kebutuhan/:id" element={<ProcurementRequestDetailPage />} />
        <Route path="vendor" element={<VendorsPage />} />
        <Route path="material" element={<MaterialsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

export default App
