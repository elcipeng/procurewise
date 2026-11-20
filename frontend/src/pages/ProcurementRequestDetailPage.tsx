import { useEffect, useRef, useState, type ReactNode } from 'react'
import { ArrowLeft, ListOrdered, Loader2, RefreshCw, RotateCw } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { ApiError } from '@/api/client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { PageHeader } from '@/components/PageHeader'
import { RequestSummary } from '@/components/procurement/RequestSummary'
import { RecommendationResultView } from '@/components/recommendations/RecommendationResultView'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useProcurementRequest } from '@/hooks/useProcurementRequests'
import { useRecommendation, useRunRecommendation } from '@/hooks/useRecommendation'
import { handleMutationError } from '@/lib/feedback'
import { UNIT_LABELS } from '@/lib/labels'
import type { RequestDetailState, RequestStatus } from '@/types/procurement'
import type { RecommendationResult } from '@/types/recommendation'
import type { ApiEnvelope } from '@/types/api'
import { NotFoundPage } from './NotFoundPage'

// sama dengan backend: kebutuhan historis yang sudah selesai atau batal tidak diranking ulang
const RANKABLE_STATUSES: RequestStatus[] = ['new', 'recommended']

const RUN_FEEDBACK = {
  onSuccess: (response: ApiEnvelope<RecommendationResult>) => toast.success(response.message),
  onError: (error: unknown) => handleMutationError(error),
}

export function ProcurementRequestDetailPage() {
  const requestId = Number(useParams().id)
  if (!Number.isInteger(requestId) || requestId < 1) return <NotFoundPage />
  return <RequestDetail key={requestId} requestId={requestId} />
}

function BackButton() {
  return (
    <Button asChild variant="outline">
      <Link to="/kebutuhan">
        <ArrowLeft />
        Kembali
      </Link>
    </Button>
  )
}

function MessageBox({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed px-4 py-10 text-center text-muted-foreground">
      {children}
    </div>
  )
}

function RequestDetail({ requestId }: { requestId: number }) {
  const request = useProcurementRequest(requestId)
  const recommendation = useRecommendation(requestId)
  const { mutate: runRecommendation, isPending: isRunning } = useRunRecommendation()
  const location = useLocation()
  const navigate = useNavigate()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const autoRunStarted = useRef(false)

  const run = () => runRecommendation(requestId, { ...RUN_FEEDBACK, onSettled: () => setConfirmOpen(false) })

  // kebutuhan baru dari form langsung diranking sekali, penanda dihapus supaya tidak terulang saat halaman dimuat ulang
  useEffect(() => {
    const state = location.state as RequestDetailState | null
    if (!state?.runRecommendation || autoRunStarted.current) return
    autoRunStarted.current = true
    navigate(location.pathname, { replace: true, state: null })
    runRecommendation(requestId, RUN_FEEDBACK)
  }, [location.state, location.pathname, navigate, runRecommendation, requestId])

  if (request.isPending) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (request.error) {
    const notFound = request.error instanceof ApiError && request.error.status === 404
    return (
      <MessageBox>
        <p className="text-title text-foreground">
          {notFound ? 'Kebutuhan tidak ditemukan' : 'Kebutuhan gagal dimuat'}
        </p>
        <p>{request.error.message}</p>
        <div className="flex gap-2">
          <BackButton />
          {!notFound && (
            <Button variant="outline" onClick={() => request.refetch()}>
              <RotateCw />
              Coba lagi
            </Button>
          )}
        </div>
      </MessageBox>
    )
  }

  const data = request.data
  const canRank = RANKABLE_STATUSES.includes(data.status)
  const result = recommendation.data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Kebutuhan #${data.id}`}
        description={`${data.material_name}, ${data.qty.toLocaleString('id-ID')} ${UNIT_LABELS[data.material_unit]}`}
        actions={
          <>
            <BackButton />
            {canRank && result && (
              <Button onClick={() => setConfirmOpen(true)} disabled={isRunning}>
                <RefreshCw />
                Susun ulang
              </Button>
            )}
          </>
        }
      />
      <RequestSummary request={data} />

      <section className="flex flex-col gap-4" aria-busy={isRunning || recommendation.isPending}>
        <h2 className="text-title text-foreground">Rekomendasi vendor</h2>

        {isRunning ? (
          <MessageBox>
            <Loader2 className="size-6 animate-spin text-primary" />
            <p>Menyusun peringkat vendor dari penawaran dan histori transaksi...</p>
          </MessageBox>
        ) : recommendation.isPending ? (
          <Skeleton className="h-64 w-full" />
        ) : recommendation.error ? (
          <MessageBox>
            <p>{recommendation.error.message}</p>
            <Button variant="outline" onClick={() => recommendation.refetch()}>
              <RotateCw />
              Coba lagi
            </Button>
          </MessageBox>
        ) : result ? (
          <RecommendationResultView result={result} />
        ) : canRank ? (
          <MessageBox>
            <p>Belum ada rekomendasi untuk kebutuhan ini.</p>
            <Button onClick={run}>
              <ListOrdered />
              Buat rekomendasi
            </Button>
          </MessageBox>
        ) : (
          <MessageBox>
            <p>
              Kebutuhan ini berasal dari histori transaksi yang sudah selesai atau dibatalkan, jadi tidak diranking
              ulang.
            </p>
          </MessageBox>
        )}
      </section>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Susun ulang rekomendasi?"
        description="Peringkat disusun ulang dari penawaran dan histori transaksi terbaru, lalu menggantikan peringkat sebelumnya."
        confirmLabel="Susun ulang"
        tone="default"
        isPending={isRunning}
        onConfirm={run}
      />
    </div>
  )
}
