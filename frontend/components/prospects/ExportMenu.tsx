'use client'

import { useState, useRef, useEffect } from 'react'
import { Download, FileText, FileSpreadsheet, FileJson, ChevronDown, Loader2 } from 'lucide-react'
import type { ExportFormat } from '@/types'
import { cn } from '@/lib/utils'

interface ExportMenuProps {
  selectedCount: number
  totalCount: number
  onExport: (format: ExportFormat, includeCompanyData: boolean, selectedOnly: boolean) => void
  isExporting?: boolean
  disabled?: boolean
}

export function ExportMenu({
  selectedCount,
  totalCount,
  onExport,
  isExporting,
  disabled,
}: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [includeCompanyData, setIncludeCompanyData] = useState(true)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleExport = (format: ExportFormat, selectedOnly: boolean) => {
    onExport(format, includeCompanyData, selectedOnly)
    setIsOpen(false)
  }

  const formats: { value: ExportFormat; label: string; icon: typeof FileText }[] = [
    { value: 'csv', label: 'CSV', icon: FileText },
    { value: 'xlsx', label: 'Excel', icon: FileSpreadsheet },
    { value: 'json', label: 'JSON', icon: FileJson },
  ]

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting || totalCount === 0}
        className={cn(
          'btn-secondary flex items-center gap-2',
          isOpen && 'bg-gray-100'
        )}
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        Export
        <ChevronDown className={cn('w-4 h-4 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-3 border-b border-gray-100">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeCompanyData}
                onChange={(e) => setIncludeCompanyData(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Include company data</span>
            </label>
          </div>

          <div className="p-2">
            <p className="px-2 py-1 text-xs text-gray-500 uppercase tracking-wider">Format</p>

            {formats.map((format) => (
              <div key={format.value} className="space-y-1">
                {/* Export Selected */}
                {selectedCount > 0 && (
                  <button
                    onClick={() => handleExport(format.value, true)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 rounded flex items-center gap-2"
                  >
                    <format.icon className="w-4 h-4 text-gray-400" />
                    <span className="flex-1">
                      Export Selected ({selectedCount}) as {format.label}
                    </span>
                  </button>
                )}

                {/* Export All */}
                <button
                  onClick={() => handleExport(format.value, false)}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 rounded flex items-center gap-2"
                >
                  <format.icon className="w-4 h-4 text-gray-400" />
                  <span className="flex-1">
                    Export All ({totalCount}) as {format.label}
                  </span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExportMenu
