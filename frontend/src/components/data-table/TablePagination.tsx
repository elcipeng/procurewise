import { ChevronLeft, ChevronRight } from 'lucide-react'
import { OptionSelect } from '@/components/OptionSelect'
import { Button } from '@/components/ui/button'

const PAGE_SIZE_OPTIONS = [10, 20, 50].map((size) => ({ value: String(size), label: String(size) }))

type TablePaginationProps = {
  page: number
  pageCount: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export function TablePagination({ page, pageCount, pageSize, total, onPageChange, onPageSizeChange }: TablePaginationProps) {
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-col gap-3 border-t px-4 py-3 text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
      <p className="text-caption">
        Menampilkan {first} sampai {last} dari {total} data
      </p>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="flex items-center gap-2 text-caption">
          <span id="page-size-label">Baris per halaman</span>
          <OptionSelect
            value={String(pageSize)}
            onValueChange={(value) => onPageSizeChange(Number(value))}
            options={PAGE_SIZE_OPTIONS}
            aria-labelledby="page-size-label"
            className="w-18"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-caption">
            Halaman {page} dari {pageCount}
          </span>
          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            aria-label="Halaman sebelumnya"
          >
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= pageCount}
            aria-label="Halaman berikutnya"
          >
            <ChevronRight />
          </Button>
        </div>
      </div>
    </div>
  )
}
