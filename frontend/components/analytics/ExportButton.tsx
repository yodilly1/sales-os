'use client'

import { useState, useRef, useEffect } from 'react'
import { Download, FileSpreadsheet, FileText, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export interface ExportButtonProps {
  onExport: (format: 'csv' | 'pdf') => Promise<void>
  disabled?: boolean
  className?: string
}

export function ExportButton({ onExport, disabled, className }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState<'csv' | 'pdf' | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleExport = async (format: 'csv' | 'pdf') => {
    setIsExporting(format)
    try {
      await onExport(format)
    } finally {
      setIsExporting(null)
      setIsOpen(false)
    }
  }

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting !== null}
        className="btn-secondary flex items-center gap-2"
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        Export
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[160px]">
          <button
            onClick={() => handleExport('csv')}
            disabled={isExporting !== null}
            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            {isExporting === 'csv' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="w-4 h-4 text-success-600" />
            )}
            Export as CSV
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={isExporting !== null}
            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            {isExporting === 'pdf' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileText className="w-4 h-4 text-danger-600" />
            )}
            Export as PDF
          </button>
        </div>
      )}
    </div>
  )
}
