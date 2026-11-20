import { Check, Loader2, MessageSquareText, Minus, RotateCw, Scale, TriangleAlert } from 'lucide-react'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
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
    <p className="text-caption text-muted-foreground">
      {note} Disusun {formatDateTime(explanation.generated_at)}.
    </p>
  )
}

function ExplanationContent({ explanation }: { explanation: Explanation }) {
  return (
    <div className="flex flex-col gap-5">
      <p className="text-foreground">{explanation.ringkasan}</p>

      {explanation.per_vendor.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          {explanation.per_vendor.map((vendor) => (
            <div key={vendor.vendor_id} className="flex flex-col gap-2 rounded-lg bg-muted/50 p-3">
              <p className="font-medium text-foreground">{vendor.nama_vendor}</p>
              <ul className="flex flex-col gap-1.5" aria-label={`Kelebihan ${vendor.nama_vendor}`}>
                {vendor.kelebihan.map((item) => (
                  <li key={item} className="flex items-start gap-1.5">
                    <Check className="mt-0.5 size-4 shrink-0 text-success" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <ul className="flex flex-col gap-1.5" aria-label={`Kekurangan ${vendor.nama_vendor}`}>
                {vendor.kekurangan.map((item) => (
                  <li key={item} className="flex items-start gap-1.5 text-muted-foreground">
                    <Minus className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-start gap-2">
        <Scale className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
        <div>
          <p className="font-medium text-foreground">Trade-off</p>
          <p className="text-muted-foreground">{explanation.trade_off}</p>
        </div>
      </div>

      <div className="rounded-lg bg-warning-soft px-4 py-3 text-warning-soft-foreground">
        <p className="mb-1.5 font-medium">Catatan risiko</p>
        <ul className="flex flex-col gap-1">
          {explanation.catatan_risiko.map((item) => (
            <li key={item} className="flex items-start gap-1.5">
              <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <SourceNote explanation={explanation} />
    </div>
  )
}

export function ExplanationPanel({ requestId, rankedAt }: { requestId: number; rankedAt: string }) {
  const explanation = useExplanation(requestId, rankedAt)
  const data = explanation.data

  return (
    <Card className="gap-4 shadow-card" aria-busy={explanation.isPending}>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2 text-heading">
          <MessageSquareText className="size-4 text-primary" aria-hidden />
          Penjelasan dan trade-off
        </CardTitle>
        {data && (
          <StatusBadge
            tone={data.source === 'gemini' ? 'success' : 'neutral'}
            label={data.source === 'gemini' ? 'Gemini' : 'Penjelasan otomatis'}
          />
        )}
      </CardHeader>
      <CardContent>
        {explanation.isPending ? (
          <div className="flex flex-col gap-3">
            <p className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="size-4 animate-spin text-primary" aria-hidden />
              Menyusun penjelasan rekomendasi...
            </p>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : explanation.error ? (
          <div className="flex flex-col items-start gap-3">
            <p className="text-muted-foreground">{explanation.error.message}</p>
            <Button variant="outline" size="sm" onClick={() => explanation.refetch()}>
              <RotateCw />
              Coba lagi
            </Button>
          </div>
        ) : (
          data && <ExplanationContent explanation={data} />
        )}
      </CardContent>
    </Card>
  )
}
