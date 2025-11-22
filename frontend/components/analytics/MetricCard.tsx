'use client'

import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { formatPercent } from '@/lib/utils/format'
import type { MetricValue } from '@/lib/types/analytics'

export interface MetricCardProps {
  title: string
  value: string
  metric?: MetricValue
  icon?: React.ReactNode
  className?: string
}

export function MetricCard({ title, value, metric, icon, className }: MetricCardProps) {
  const getTrendIcon = () => {
    if (!metric) return null

    switch (metric.trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />
      case 'down':
        return <TrendingDown className="w-4 h-4" />
      default:
        return <Minus className="w-4 h-4" />
    }
  }

  const getTrendColor = () => {
    if (!metric) return 'text-gray-500'

    switch (metric.trend) {
      case 'up':
        return 'text-success-600'
      case 'down':
        return 'text-danger-600'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <div className={cn('card p-6', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          {metric && (
            <div className={cn('mt-2 flex items-center gap-1', getTrendColor())}>
              {getTrendIcon()}
              <span className="text-sm font-medium">
                {formatPercent(metric.changePercent)}
              </span>
              <span className="text-sm text-gray-500">vs last period</span>
            </div>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-primary-50 rounded-lg text-primary-600">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
