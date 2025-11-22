'use client'

import { useState, useMemo } from 'react'
import { cn } from '@/lib/utils/cn'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'

export interface Column<T> {
  key: keyof T | string
  header: string
  width?: string
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  render?: (value: unknown, row: T, index: number) => React.ReactNode
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  keyField: keyof T
  className?: string
  emptyMessage?: string
  stickyHeader?: boolean
  striped?: boolean
  hoverable?: boolean
  compact?: boolean
  maxHeight?: string
  onRowClick?: (row: T) => void
}

type SortDirection = 'asc' | 'desc' | null

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  keyField,
  className,
  emptyMessage = 'No data available',
  stickyHeader = false,
  striped = true,
  hoverable = true,
  compact = false,
  maxHeight,
  onRowClick,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortKey(null)
        setSortDirection(null)
      }
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return data

    return [...data].sort((a, b) => {
      const aValue = a[sortKey as keyof T]
      const bValue = b[sortKey as keyof T]

      if (aValue === bValue) return 0
      if (aValue === null || aValue === undefined) return 1
      if (bValue === null || bValue === undefined) return -1

      const comparison = aValue < bValue ? -1 : 1
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [data, sortKey, sortDirection])

  const SortIcon = ({ column }: { column: Column<T> }) => {
    if (!column.sortable) return null

    const key = String(column.key)
    if (sortKey !== key) {
      return <ChevronsUpDown className="w-4 h-4 text-gray-400" />
    }
    if (sortDirection === 'asc') {
      return <ChevronUp className="w-4 h-4 text-primary-600" />
    }
    return <ChevronDown className="w-4 h-4 text-primary-600" />
  }

  const getCellValue = (row: T, column: Column<T>): unknown => {
    const key = String(column.key)
    if (key.includes('.')) {
      return key.split('.').reduce((obj: unknown, k) => {
        if (obj && typeof obj === 'object') {
          return (obj as Record<string, unknown>)[k]
        }
        return undefined
      }, row)
    }
    return row[key as keyof T]
  }

  return (
    <div
      className={cn(
        'w-full overflow-auto scrollbar-thin',
        maxHeight && 'overflow-y-auto',
        className
      )}
      style={{ maxHeight }}
    >
      <table className="w-full border-collapse">
        <thead className={cn(stickyHeader && 'sticky top-0 z-10')}>
          <tr className="bg-gray-50 border-b border-gray-200">
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={cn(
                  'text-left text-xs font-semibold text-gray-600 uppercase tracking-wider',
                  compact ? 'px-3 py-2' : 'px-4 py-3',
                  column.align === 'center' && 'text-center',
                  column.align === 'right' && 'text-right',
                  column.sortable && 'cursor-pointer select-none hover:bg-gray-100'
                )}
                style={{ width: column.width }}
                onClick={() => column.sortable && handleSort(String(column.key))}
              >
                <div
                  className={cn(
                    'flex items-center gap-1',
                    column.align === 'center' && 'justify-center',
                    column.align === 'right' && 'justify-end'
                  )}
                >
                  {column.header}
                  <SortIcon column={column} />
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className={cn(
                  'text-center text-gray-500',
                  compact ? 'px-3 py-8' : 'px-4 py-12'
                )}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedData.map((row, rowIndex) => (
              <tr
                key={String(row[keyField])}
                className={cn(
                  'border-b border-gray-100 transition-colors',
                  striped && rowIndex % 2 === 1 && 'bg-gray-50/50',
                  hoverable && 'hover:bg-gray-50',
                  onRowClick && 'cursor-pointer'
                )}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => {
                  const value = getCellValue(row, column)
                  return (
                    <td
                      key={String(column.key)}
                      className={cn(
                        'text-sm text-gray-900',
                        compact ? 'px-3 py-2' : 'px-4 py-3',
                        column.align === 'center' && 'text-center',
                        column.align === 'right' && 'text-right'
                      )}
                    >
                      {column.render
                        ? column.render(value, row, rowIndex)
                        : String(value ?? '-')}
                    </td>
                  )
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
