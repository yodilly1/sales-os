'use client'

import { cn } from '@/lib/utils/cn'

export interface ChartCardProps {
  title: string
  description?: string
  actions?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function ChartCard({ title, description, actions, children, className }: ChartCardProps) {
  return (
    <div className={cn('card', className)}>
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-base font-semibold text-gray-900">{title}</h3>
            {description && (
              <p className="mt-1 text-sm text-gray-500">{description}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      </div>
      <div className="p-6">{children}</div>
    </div>
  )
}
