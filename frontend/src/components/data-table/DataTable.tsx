import { useMemo, useState, type ReactNode } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { DataTableView, type Column, type SortState } from './DataTableView'

export type { Column } from './DataTableView'

type DataTableProps<T> = {
  rows: T[] | undefined
  columns: Column<T>[]
  getRowKey: (row: T) => string | number
  searchText: (row: T) => string
  searchPlaceholder: string
  emptyMessage: string
  isLoading: boolean
  error: Error | null
  onRetry: () => void
  toolbar?: ReactNode
  initialSort?: SortState
}

export const DEFAULT_PAGE_SIZE = 10

function compare(a: string | number, b: string | number) {
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), 'id', { sensitivity: 'base', numeric: true })
}

/** tabel dengan pencarian, sort, dan pagination di client, untuk daftar kecil yang dimuat utuh dari API */
export function DataTable<T>({
  rows,
  columns,
  getRowKey,
  searchText,
  searchPlaceholder,
  emptyMessage,
  isLoading,
  error,
  onRetry,
  toolbar,
  initialSort,
}: DataTableProps<T>) {
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState<SortState | undefined>(initialSort)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)

  const visibleRows = useMemo(() => {
    const keyword = query.trim().toLowerCase()
    const filtered = (rows ?? []).filter((row) => !keyword || searchText(row).toLowerCase().includes(keyword))
    const column = columns.find((c) => c.id === sort?.columnId)
    if (!sort || !column?.sortValue) return filtered
    const factor = sort.direction === 'asc' ? 1 : -1
    return [...filtered].sort((a, b) => factor * compare(column.sortValue!(a), column.sortValue!(b)))
  }, [rows, query, sort, columns, searchText])

  // filter dari luar bisa mengecilkan jumlah baris, jadi halaman aktif dijepit ke halaman terakhir
  const pageCount = Math.max(1, Math.ceil(visibleRows.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const pageRows = visibleRows.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative w-full sm:max-w-xs">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setPage(1)
            }}
            placeholder={searchPlaceholder}
            aria-label={searchPlaceholder}
            className="pl-8"
          />
        </div>
        {toolbar && <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">{toolbar}</div>}
      </div>

      <DataTableView
        rows={pageRows}
        columns={columns}
        getRowKey={getRowKey}
        emptyMessage={query.trim() ? 'Tidak ada data yang cocok dengan pencarian.' : emptyMessage}
        isLoading={isLoading}
        error={error}
        onRetry={onRetry}
        sort={sort}
        onSortChange={setSort}
        pagination={{
          page: currentPage,
          pageCount,
          pageSize,
          total: visibleRows.length,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
        }}
      />
    </div>
  )
}
