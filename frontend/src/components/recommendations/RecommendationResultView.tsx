import type { ReactNode } from 'react'
import { TriangleAlert } from 'lucide-react'
import { formatDateTime } from '@/lib/format'
import type { RecommendationResult } from '@/types/recommendation'
import { ExplanationPanel } from './ExplanationPanel'
import { RankingTable } from './RankingTable'
import { RejectedVendorList } from './RejectedVendorList'
import { TopVendorComparison } from './TopVendorComparison'

function Section({ title, description, children }: { title: string; description?: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="text-heading text-foreground">{title}</h2>
        {description && <p className="text-muted-foreground">{description}</p>}
      </div>
      {children}
    </section>
  )
}

export function RecommendationResultView({ result }: { result: RecommendationResult }) {
  const { ranked, rejected } = result
  const hasLimitedHistory = ranked.some((v) => !v.history.has_history)

  return (
    <div className="flex flex-col gap-8">
      <p className="text-muted-foreground">
        Disusun {formatDateTime(result.ranked_at)} dengan model {result.model_version}. {ranked.length} vendor memenuhi
        syarat dan {rejected.length} vendor tidak memenuhi syarat.
      </p>

      {result.is_fallback && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-lg bg-warning-soft px-4 py-3 text-warning-soft-foreground"
        >
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          <p>
            Model LightGBM tidak dapat dimuat, jadi peringkat ini disusun dengan metode cadangan weighted sum (harga,
            lead time, tepat waktu, cacat, dan rating).
          </p>
        </div>
      )}

      <ExplanationPanel requestId={result.request.id} rankedAt={result.ranked_at} />

      {ranked.length === 0 ? (
        <div className="rounded-lg border border-dashed px-4 py-8 text-center text-muted-foreground">
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
              <p className="text-caption text-muted-foreground">
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

      <p className="text-caption text-muted-foreground">
        Peringkat adalah rekomendasi dari penawaran dan histori transaksi. Keputusan pemilihan vendor tetap di tangan
        Anda.
      </p>
    </div>
  )
}
