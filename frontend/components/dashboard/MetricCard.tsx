'use client'

import { cn, formatNumber, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: number | string
  change?: number
  changeLabel?: string
  icon: React.ComponentType<{ className?: string }>
  iconColor?: 'primary' | 'success' | 'warning' | 'accent'
  format?: 'number' | 'currency' | 'percentage' | 'none'
  loading?: boolean
}

const iconColorClasses = {
  primary: 'bg-primary-100 text-primary-600',
  success: 'bg-success-100 text-success-600',
  warning: 'bg-warning-100 text-warning-600',
  accent: 'bg-accent-100 text-accent-600',
}

export function MetricCard({
  title,
  value,
  change,
  changeLabel = 'vs last period',
  icon: Icon,
  iconColor = 'primary',
  format = 'number',
  loading = false,
}: MetricCardProps) {
  const formattedValue = () => {
    if (typeof value === 'string') return value
    switch (format) {
      case 'currency':
        return `$${formatNumber(value)}`
      case 'percentage':
        return `${value}%`
      case 'number':
        return formatNumber(value)
      default:
        return value
    }
  }

  const getTrendIcon = () => {
    if (change === undefined) return null
    if (change > 0) return <TrendingUp className="w-3.5 h-3.5" />
    if (change < 0) return <TrendingDown className="w-3.5 h-3.5" />
    return <Minus className="w-3.5 h-3.5" />
  }

  const getTrendColor = () => {
    if (change === undefined) return 'text-slate-500'
    if (change > 0) return 'text-success-600'
    if (change < 0) return 'text-danger-600'
    return 'text-slate-500'
  }

  if (loading) {
    return (
      <div className="metric-card animate-pulse">
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1">
            <div className="h-4 bg-slate-200 rounded w-24" />
            <div className="h-8 bg-slate-200 rounded w-20" />
          </div>
          <div className="w-10 h-10 bg-slate-200 rounded-lg" />
        </div>
        <div className="mt-4 h-4 bg-slate-200 rounded w-32" />
      </div>
    )
  }

  return (
    <div className="metric-card group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">
            {formattedValue()}
          </p>
        </div>
        <div className={cn(
          'w-10 h-10 rounded-lg flex items-center justify-center transition-transform group-hover:scale-110',
          iconColorClasses[iconColor]
        )}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {change !== undefined && (
        <div className="flex items-center gap-1.5 mt-4">
          <span className={cn('flex items-center gap-0.5 text-sm font-medium', getTrendColor())}>
            {getTrendIcon()}
            {formatPercentage(change)}
          </span>
          <span className="text-sm text-slate-400">{changeLabel}</span>
        </div>
      )}
    </div>
  )
}
