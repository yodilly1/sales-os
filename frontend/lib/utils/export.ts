import { format } from 'date-fns'
import type { DateRange } from '@/lib/types/analytics'

export interface ExportColumn<T> {
  key: keyof T | string
  header: string
  format?: (value: unknown, row: T) => string
}

export function exportToCSV<T extends Record<string, unknown>>(
  data: T[],
  columns: ExportColumn<T>[],
  filename: string
): void {
  // Create header row
  const headers = columns.map((col) => `"${col.header}"`).join(',')

  // Create data rows
  const rows = data.map((row) => {
    return columns
      .map((col) => {
        const key = String(col.key)
        let value: unknown

        // Handle nested keys
        if (key.includes('.')) {
          value = key.split('.').reduce((obj: unknown, k) => {
            if (obj && typeof obj === 'object') {
              return (obj as Record<string, unknown>)[k]
            }
            return undefined
          }, row)
        } else {
          value = row[key as keyof T]
        }

        // Format value if formatter provided
        if (col.format) {
          value = col.format(value, row)
        }

        // Handle different value types
        if (value === null || value === undefined) {
          return ''
        }
        if (typeof value === 'string') {
          // Escape quotes and wrap in quotes
          return `"${value.replace(/"/g, '""')}"`
        }
        if (typeof value === 'number') {
          return value.toString()
        }
        if (typeof value === 'boolean') {
          return value ? 'Yes' : 'No'
        }
        if (value instanceof Date) {
          return `"${format(value, 'yyyy-MM-dd HH:mm:ss')}"`
        }

        return `"${String(value)}"`
      })
      .join(',')
  })

  // Combine into CSV content
  const csvContent = [headers, ...rows].join('\n')

  // Create and trigger download
  downloadFile(csvContent, `${filename}.csv`, 'text/csv;charset=utf-8;')
}

export function downloadFile(content: string | Blob, filename: string, mimeType?: string): void {
  const blob = typeof content === 'string' ? new Blob([content], { type: mimeType }) : content
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function generateExportFilename(
  type: string,
  dateRange: DateRange,
  format: 'csv' | 'pdf'
): string {
  const startDate = dateRange.startDate.replace(/-/g, '')
  const endDate = dateRange.endDate.replace(/-/g, '')
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  return `sales-os-${type}-${startDate}-${endDate}-${timestamp}.${format}`
}

// Helper to format common analytics data for export
export const formatters = {
  currency: (value: unknown): string => {
    const num = Number(value)
    if (isNaN(num)) return ''
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num)
  },

  percent: (value: unknown): string => {
    const num = Number(value)
    if (isNaN(num)) return ''
    return `${num.toFixed(1)}%`
  },

  number: (value: unknown): string => {
    const num = Number(value)
    if (isNaN(num)) return ''
    return new Intl.NumberFormat('en-US').format(num)
  },

  date: (value: unknown): string => {
    if (!value) return ''
    try {
      const date = typeof value === 'string' ? new Date(value) : value as Date
      return format(date, 'yyyy-MM-dd')
    } catch {
      return String(value)
    }
  },

  datetime: (value: unknown): string => {
    if (!value) return ''
    try {
      const date = typeof value === 'string' ? new Date(value) : value as Date
      return format(date, 'yyyy-MM-dd HH:mm:ss')
    } catch {
      return String(value)
    }
  },

  duration: (value: unknown): string => {
    const minutes = Number(value)
    if (isNaN(minutes)) return ''
    if (minutes < 60) return `${Math.round(minutes)}m`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  },

  score: (value: unknown): string => {
    const num = Number(value)
    if (isNaN(num)) return ''
    return `${num.toFixed(1)}/10`
  },
}
