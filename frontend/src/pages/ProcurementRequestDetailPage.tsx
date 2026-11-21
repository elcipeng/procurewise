import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Button, InlineLoading, SkeletonPlaceholder, SkeletonText } from '@carbon/react'
import { ArrowLeft, ListNumbered, Renew } from '@carbon/icons-react'
import { Link, useLocation, useNavigate, useParams } from 'react-router'
import { ApiError } from '@/api/client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { PageHeader } from '@/components/PageHeader'
import { RequestSummary } from '@/components/procurement/RequestSummary'
import { RecommendationResultView } from '@/components/recommendations/RecommendationResultView'
import { useProcurementRequest } from '@/hooks/useProcurementRequests'
import { useRecommendation, useRunRecommendation } from '@/hooks/useRecommendation'
import { handleMutationError } from '@/lib/feedback'
import { UNIT_LABELS } from '@/lib/labels'
import { toast } from '@/lib/toast'
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
    <Button as={Link} to="/kebutuhan" kind="secondary" renderIcon={ArrowLeft}>
      Kembali
    </Button>
  )
}

function MessageBox({ children }: { children: ReactNode }) {
  return <div className="pw-empty-state pw-empty-state--bordered">{children}</div>
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
      <div className="pw-page">
        <SkeletonText heading width="16rem" />
        <SkeletonPlaceholder className="pw-skeleton-block" />
      </div>
    )
  }

  if (request.error) {
    const notFound = request.error instanceof ApiError && request.error.status === 404
    return (
      <MessageBox>
        <p className="pw-empty-state__title">{notFound ? 'Kebutuhan tidak ditemukan' : 'Kebutuhan gagal dimuat'}</p>
        <p>{request.error.message}</p>
        <div className="pw-button-row">
          <BackButton />
          {!notFound && (
            <Button kind="tertiary" renderIcon={Renew} onClick={() => request.refetch()}>
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
    <div className="pw-page">
      <PageHeader
        title={`Kebutuhan #${data.id}`}
        description={`${data.material_name}, ${data.qty.toLocaleString('id-ID')} ${UNIT_LABELS[data.material_unit]}`}
        actions={
          <>
            <BackButton />
            {canRank && result && (
              <Button renderIcon={Renew} onClick={() => setConfirmOpen(true)} disabled={isRunning}>
                Susun ulang
              </Button>
            )}
          </>
        }
      />
      <RequestSummary request={data} />

      <section className="pw-section" aria-busy={isRunning || recommendation.isPending}>
        <h2 className="pw-section__title">Rekomendasi vendor</h2>

        {isRunning ? (
          <MessageBox>
            <InlineLoading description="Menyusun peringkat vendor dari penawaran dan histori transaksi..." />
          </MessageBox>
        ) : recommendation.isPending ? (
          <SkeletonPlaceholder className="pw-skeleton-block pw-skeleton-block--tall" />
        ) : recommendation.error ? (
          <MessageBox>
            <p>{recommendation.error.message}</p>
            <Button kind="tertiary" renderIcon={Renew} onClick={() => recommendation.refetch()}>
              Coba lagi
            </Button>
          </MessageBox>
        ) : result ? (
          <RecommendationResultView result={result} />
        ) : canRank ? (
          <MessageBox>
            <p>Belum ada rekomendasi untuk kebutuhan ini.</p>
            <Button renderIcon={ListNumbered} onClick={run}>
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
