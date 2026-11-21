import type { ReactNode } from 'react'
import {
  Button,
  DataTableSkeleton,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react'
import { Renew } from '@carbon/icons-react'

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
  pageSize: number
  total: number
  onChange: (page: number, pageSize: number) => void
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
  toolbar?: ReactNode
  // tanpa onSortChange, header tampil biasa (misalnya untuk tabel yang diurutkan di server)
  sort?: SortState
  onSortChange?: (sort: SortState) => void
}

const PAGE_SIZES = [10, 20, 50]
const SKELETON_ROWS = 5
const SORT_DIRECTION = { asc: 'ASC', desc: 'DESC' } as const

export function DataTableView<T>({
  rows,
  columns,
  getRowKey,
  emptyMessage,
  isLoading,
  error,
  onRetry,
  pagination,
  toolbar,
  sort,
  onSortChange,
}: DataTableViewProps<T>) {
  const toggleSort = (columnId: string) =>
    onSortChange?.(
      sort?.columnId === columnId && sort.direction === 'asc'
        ? { columnId, direction: 'desc' }
        : { columnId, direction: 'asc' },
    )

  if (isLoading) {
    return (
      <DataTableSkeleton
        columnCount={columns.length}
        rowCount={SKELETON_ROWS}
        headers={columns.map((c) => ({ key: c.id, header: c.header }))}
        showToolbar={!!toolbar}
        showHeader={false}
      />
    )
  }

  return (
    <TableContainer className="pw-table">
      {toolbar}
      <div className="pw-table__scroll">
        <Table size="lg" useZebraStyles={false}>
          <TableHead>
            <TableRow>
              {columns.map((column) => {
                const sortable = !!column.sortValue && !!onSortChange
                const active = sort?.columnId === column.id
                return (
                  <TableHeader
                    key={column.id}
                    className={column.className}
                    isSortable={sortable}
                    isSortHeader={active}
                    sortDirection={active ? SORT_DIRECTION[sort.direction] : 'NONE'}
                    onClick={sortable ? () => toggleSort(column.id) : undefined}
                  >
                    {column.header}
                  </TableHeader>
                )
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {error ? (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <div className="pw-table__message">
                    <p>{error.message}</p>
                    <Button kind="tertiary" size="sm" renderIcon={Renew} onClick={onRetry}>
                      Coba lagi
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <p className="pw-table__message">{emptyMessage}</p>
                </TableCell>
              </TableRow>
            ) : (
              rows.map((row) => (
                <TableRow key={getRowKey(row)}>
                  {columns.map((column) => (
                    <TableCell key={column.id} className={column.className}>
                      {column.cell(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      {!error && pagination.total > 0 && (
        <Pagination
          page={pagination.page}
          pageSize={pagination.pageSize}
          pageSizes={PAGE_SIZES}
          totalItems={pagination.total}
          onChange={({ page, pageSize }) => pagination.onChange(page, pageSize)}
          itemsPerPageText="Baris per halaman"
          itemRangeText={(min, max, total) => `${min} sampai ${max} dari ${total} data`}
          pageRangeText={(_current, total) => `dari ${total} halaman`}
          pageText={(page) => `Halaman ${page}`}
          backwardText="Halaman sebelumnya"
          forwardText="Halaman berikutnya"
          pageNumberText="Nomor halaman"
        />
      )}
    </TableContainer>
  )
}
