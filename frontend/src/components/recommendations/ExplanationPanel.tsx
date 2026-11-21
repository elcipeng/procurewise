import { Button, InlineLoading, InlineNotification, SkeletonText, Tag, Tile } from '@carbon/react'
import { Checkmark, Renew, Scales, Subtract } from '@carbon/icons-react'
import { useExplanation } from '@/hooks/useExplanation'
import { formatDateTime } from '@/lib/format'
import type { Explanation, FallbackReason } from '@/types/explanation'

const FALLBACK_NOTES: Record<FallbackReason, string> = {
  api_key_kosong: 'Gemini belum dikonfigurasi di server, jadi penjelasan disusun otomatis dari data peringkat.',
  api_gagal: 'Gemini sedang tidak dapat dihubungi, jadi penjelasan disusun otomatis dari data peringkat.',
  batas_pemakaian: 'Batas pemakaian Gemini sedang tercapai, jadi penjelasan disusun otomatis dari data peringkat.',
  angka_tidak_cocok:
    'Jawaban Gemini memuat angka yang tidak cocok dengan data, jadi diganti penjelasan otomatis dari data peringkat.',
}

function SourceNote({ explanation }: { explanation: Explanation }) {
  const note =
    explanation.source === 'gemini'
      ? `Dibuat oleh Gemini (${explanation.model}) dari data peringkat, dan setiap angka sudah dicek cocok dengan data.`
      : FALLBACK_NOTES[explanation.fallback_reason ?? 'api_gagal']
  return (
    <p className="pw-caption">
      {note} Disusun {formatDateTime(explanation.generated_at)}.
    </p>
  )
}

function ExplanationContent({ explanation }: { explanation: Explanation }) {
  return (
    <div className="pw-explanation">
      <p className="pw-explanation__summary">{explanation.ringkasan}</p>

      {explanation.per_vendor.length > 0 && (
        <div className="pw-compare">
          {explanation.per_vendor.map((vendor) => (
            <div key={vendor.vendor_id} className="pw-explanation__vendor">
              <p className="pw-strong">{vendor.nama_vendor}</p>
              <ul className="pw-icon-list" aria-label={`Kelebihan ${vendor.nama_vendor}`}>
                {vendor.kelebihan.map((item) => (
                  <li key={item}>
                    <Checkmark className="pw-icon--success" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <ul className="pw-icon-list pw-text-secondary" aria-label={`Kekurangan ${vendor.nama_vendor}`}>
                {vendor.kekurangan.map((item) => (
                  <li key={item}>
                    <Subtract className="pw-icon--error" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="pw-explanation__tradeoff">
        <Scales className="pw-icon--interactive" aria-hidden />
        <div>
          <p className="pw-strong">Trade-off</p>
          <p className="pw-text-secondary">{explanation.trade_off}</p>
        </div>
      </div>

      <InlineNotification
        kind="warning"
        title="Catatan risiko"
        hideCloseButton
        lowContrast
        className="pw-notification pw-notification--stacked"
      >
        <ul className="pw-risk-list">
          {explanation.catatan_risiko.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </InlineNotification>

      <SourceNote explanation={explanation} />
    </div>
  )
}

export function ExplanationPanel({ requestId, rankedAt }: { requestId: number; rankedAt: string }) {
  const explanation = useExplanation(requestId, rankedAt)
  const data = explanation.data

  return (
    <Tile className="pw-tile" aria-busy={explanation.isPending}>
      <div className="pw-tile__header">
        <h3 className="pw-section__subtitle">Penjelasan dan trade-off</h3>
        {data && (
          <Tag type={data.source === 'gemini' ? 'blue' : 'gray'} size="sm">
            {data.source === 'gemini' ? 'Gemini' : 'Penjelasan otomatis'}
          </Tag>
        )}
      </div>
      {explanation.isPending ? (
        <div className="pw-explanation">
          <InlineLoading description="Menyusun penjelasan rekomendasi..." />
          <SkeletonText paragraph lineCount={4} />
        </div>
      ) : explanation.error ? (
        <div className="pw-explanation">
          <p className="pw-text-secondary">{explanation.error.message}</p>
          <div>
            <Button kind="tertiary" size="sm" renderIcon={Renew} onClick={() => explanation.refetch()}>
              Coba lagi
            </Button>
          </div>
        </div>
      ) : (
        data && <ExplanationContent explanation={data} />
      )}
    </Tile>
  )
}
