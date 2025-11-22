'use client'

import { useState, useRef, useEffect } from 'react'
import { Calendar, ChevronDown } from 'lucide-react'
import { format, subDays, subMonths, startOfMonth, endOfMonth, startOfQuarter, endOfQuarter, startOfYear, endOfYear } from 'date-fns'
import { cn } from '@/lib/utils/cn'
import type { DateRange } from '@/lib/types/analytics'

export interface DateRangePickerProps {
  value: DateRange
  onChange: (range: DateRange) => void
  className?: string
}

interface PresetRange {
  label: string
  getValue: () => DateRange
}

const presetRanges: PresetRange[] = [
  {
    label: 'Last 7 days',
    getValue: () => ({
      startDate: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
      endDate: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Last 14 days',
    getValue: () => ({
      startDate: format(subDays(new Date(), 14), 'yyyy-MM-dd'),
      endDate: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Last 30 days',
    getValue: () => ({
      startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      endDate: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Last 90 days',
    getValue: () => ({
      startDate: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
      endDate: format(new Date(), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'This month',
    getValue: () => ({
      startDate: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
      endDate: format(endOfMonth(new Date()), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'Last month',
    getValue: () => {
      const lastMonth = subMonths(new Date(), 1)
      return {
        startDate: format(startOfMonth(lastMonth), 'yyyy-MM-dd'),
        endDate: format(endOfMonth(lastMonth), 'yyyy-MM-dd'),
      }
    },
  },
  {
    label: 'This quarter',
    getValue: () => ({
      startDate: format(startOfQuarter(new Date()), 'yyyy-MM-dd'),
      endDate: format(endOfQuarter(new Date()), 'yyyy-MM-dd'),
    }),
  },
  {
    label: 'This year',
    getValue: () => ({
      startDate: format(startOfYear(new Date()), 'yyyy-MM-dd'),
      endDate: format(endOfYear(new Date()), 'yyyy-MM-dd'),
    }),
  },
]

export function DateRangePicker({ value, onChange, className }: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [customStart, setCustomStart] = useState(value.startDate)
  const [customEnd, setCustomEnd] = useState(value.endDate)
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

  const handlePresetSelect = (preset: PresetRange) => {
    const range = preset.getValue()
    onChange(range)
    setCustomStart(range.startDate)
    setCustomEnd(range.endDate)
    setIsOpen(false)
  }

  const handleCustomApply = () => {
    onChange({ startDate: customStart, endDate: customEnd })
    setIsOpen(false)
  }

  const formatDisplayDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d, yyyy')
    } catch {
      return dateStr
    }
  }

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-secondary flex items-center gap-2"
      >
        <Calendar className="w-4 h-4" />
        <span>
          {formatDisplayDate(value.startDate)} - {formatDisplayDate(value.endDate)}
        </span>
        <ChevronDown className={cn('w-4 h-4 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 z-50 bg-white rounded-lg shadow-lg border border-gray-200 p-4 w-80">
          <div className="space-y-1 mb-4">
            {presetRanges.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handlePresetSelect(preset)}
                className="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-gray-50 transition-colors"
              >
                {preset.label}
              </button>
            ))}
          </div>

          <div className="border-t border-gray-200 pt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Custom Range</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Start</label>
                <input
                  type="date"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="input"
                />
              </div>
              <div>
                <label className="label">End</label>
                <input
                  type="date"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="input"
                />
              </div>
            </div>
            <button
              onClick={handleCustomApply}
              className="btn-primary w-full mt-3"
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
