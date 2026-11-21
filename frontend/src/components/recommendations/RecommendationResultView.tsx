import type { ReactNode } from 'react'
import { InlineNotification } from '@carbon/react'
import { formatDateTime } from '@/lib/format'
import type { RecommendationResult } from '@/types/recommendation'
import { ExplanationPanel } from './ExplanationPanel'
import { RankingTable } from './RankingTable'
import { RejectedVendorList } from './RejectedVendorList'
import { TopVendorComparison } from './TopVendorComparison'

function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return (
    <section className="pw-section">
      <div>
        <h3 className="pw-section__subtitle">{title}</h3>
        {description && <p className="pw-section__description">{description}</p>}
      </div>
      {children}
    </section>
  )
}

export function RecommendationResultView({ result }: { result: RecommendationResult }) {
  const { ranked, rejected } = result
  const hasLimitedHistory = ranked.some((v) => !v.history.has_history)

  return (
    <div className="pw-page">
      <p className="pw-section__description">
        Disusun {formatDateTime(result.ranked_at)} dengan model {result.model_version}. {ranked.length} vendor memenuhi
        syarat dan {rejected.length} vendor tidak memenuhi syarat.
      </p>

      {result.is_fallback && (
        <InlineNotification
          kind="warning"
          title="Model LightGBM tidak dapat dimuat, jadi peringkat ini disusun dengan metode cadangan weighted sum (harga, lead time, tepat waktu, cacat, dan rating)."
          hideCloseButton
          lowContrast
          className="pw-notification"
        />
      )}

      <ExplanationPanel requestId={result.request.id} rankedAt={result.ranked_at} />

      {ranked.length === 0 ? (
        <div className="pw-empty-state pw-empty-state--bordered">
          Tidak ada vendor yang memenuhi syarat. Periksa alasan di bawah, lalu buat kebutuhan baru dengan jumlah,
          tanggal, atau budget yang disesuaikan.
        </div>
      ) : (
        <>
          <Section
            title="Perbandingan vendor teratas"
            description={
              result.is_fallback
                ? 'Nilai terbaik di antara vendor teratas ditandai hijau.'
                : 'Nilai terbaik di antara vendor teratas ditandai hijau. Faktor utama berasal dari kontribusi fitur model.'
            }
          >
            <TopVendorComparison vendors={ranked} />
          </Section>
          <Section title="Peringkat lengkap">
            <RankingTable vendors={ranked} />
            {hasLimitedHistory && (
              <p className="pw-caption">
                Vendor dengan data terbatas belum punya transaksi selesai, jadi metrik tepat waktu, cacat, dan rating
                memakai rata-rata vendor sekategori.
              </p>
            )}
          </Section>
        </>
      )}

      {rejected.length > 0 && (
        <Section
          title={`Tidak memenuhi syarat (${rejected.length})`}
          description="Vendor berikut menawarkan material ini, tetapi gugur di pengecekan awal."
        >
          <RejectedVendorList vendors={rejected} />
        </Section>
      )}

      <p className="pw-caption">
        Peringkat adalah rekomendasi dari penawaran dan histori transaksi. Keputusan pemilihan vendor tetap di tangan
        Anda.
      </p>
    </div>
  )
}
