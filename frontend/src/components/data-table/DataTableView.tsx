import type { ReactNode } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
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

export type SortState = { columnId: string; direction: 'asc' | 'desc' }

export type PaginationState = {
  page: number
  pageCount: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

type DataTableViewProps<T> = {
  rows: T[]
  columns: Column<T>[]
  getRowKey: (row: T) => string | number
  emptyMessage: string
  isLoading: boolean
  error: Error | null
  onRetry: () => void
  pagination: PaginationState
  // tanpa onSortChange, header tampil biasa (misalnya untuk tabel yang diurutkan di server)
  sort?: SortState
  onSortChange?: (sort: SortState) => void
}

const SKELETON_ROWS = 5

export function DataTableView<T>({
  rows,
  columns,
  getRowKey,
  emptyMessage,
  isLoading,
  error,
  onRetry,
  pagination,
  sort,
  onSortChange,
}: DataTableViewProps<T>) {
  const toggleSort = (columnId: string) =>
    onSortChange?.(
      sort?.columnId === columnId && sort.direction === 'asc'
        ? { columnId, direction: 'desc' }
        : { columnId, direction: 'asc' },
    )

  return (
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
                    {column.sortValue && onSortChange ? (
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

            {!isLoading && !error && rows.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={columns.length} className="py-10 text-center text-muted-foreground">
                  {emptyMessage}
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              !error &&
              rows.map((row) => (
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
      {!isLoading && !error && pagination.total > 0 && <TablePagination {...pagination} />}
    </Card>
  )
}
