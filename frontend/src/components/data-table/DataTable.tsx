import { useMemo, useState, type ReactNode } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, RotateCw, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { TablePagination } from './TablePagination'

export type Column<T> = {
  id: string
  header: string
  cell: (row: T) => ReactNode
  sortValue?: (row: T) => string | number
  className?: string
}

type SortState = { columnId: string; direction: 'asc' | 'desc' }

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

const DEFAULT_PAGE_SIZE = 10
const SKELETON_ROWS = 5

function compare(a: string | number, b: string | number) {
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), 'id', { sensitivity: 'base', numeric: true })
}

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

  const toggleSort = (columnId: string) => {
    setSort((current) =>
      current?.columnId === columnId && current.direction === 'asc'
        ? { columnId, direction: 'desc' }
        : { columnId, direction: 'asc' },
    )
  }

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

      <Card className="gap-0 overflow-hidden py-0 shadow-card">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/60 hover:bg-muted/60">
                {columns.map((column) => {
                  const active = sort?.columnId === column.id
                  const SortIcon = !active ? ArrowUpDown : sort.direction === 'asc' ? ArrowUp : ArrowDown
                  return (
                    <TableHead
                      key={column.id}
                      className={cn('text-caption font-medium text-muted-foreground', column.className)}
                      aria-sort={active ? (sort.direction === 'asc' ? 'ascending' : 'descending') : undefined}
                    >
                      {column.sortValue ? (
                        <button
                          type="button"
                          onClick={() => toggleSort(column.id)}
                          className="inline-flex items-center gap-1 rounded-sm hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:outline-none"
                        >
                          {column.header}
                          <SortIcon className={cn('size-3.5', !active && 'opacity-50')} />
                        </button>
                      ) : (
                        column.header
                      )}
                    </TableHead>
                  )
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: SKELETON_ROWS }, (_, i) => (
                  <TableRow key={i}>
                    {columns.map((column) => (
                      <TableCell key={column.id}>
                        <Skeleton className="h-4 w-full max-w-32" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}

              {!isLoading && error && (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={columns.length} className="py-10 text-center">
                    <p className="text-muted-foreground">{error.message}</p>
                    <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
                      <RotateCw />
                      Coba lagi
                    </Button>
                  </TableCell>
                </TableRow>
              )}

              {!isLoading && !error && pageRows.length === 0 && (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={columns.length} className="py-10 text-center text-muted-foreground">
                    {query.trim() ? 'Tidak ada data yang cocok dengan pencarian.' : emptyMessage}
                  </TableCell>
                </TableRow>
              )}

              {!isLoading &&
                !error &&
                pageRows.map((row) => (
                  <TableRow key={getRowKey(row)}>
                    {columns.map((column) => (
                      <TableCell key={column.id} className={column.className}>
                        {column.cell(row)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </div>
        {!isLoading && !error && visibleRows.length > 0 && (
          <TablePagination
            page={currentPage}
            pageCount={pageCount}
            pageSize={pageSize}
            total={visibleRows.length}
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size)
              setPage(1)
            }}
          />
        )}
      </Card>
    </div>
  )
}
