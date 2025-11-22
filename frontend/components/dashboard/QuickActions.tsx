'use client'

import Link from 'next/link'
import {
  Phone,
  FileText,
  UserSearch,
  Target,
  Upload,
  Sparkles,
} from 'lucide-react'

interface QuickAction {
  label: string
  description: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  iconBg: string
  iconColor: string
}

const quickActions: QuickAction[] = [
  {
    label: 'Analyze Call',
    description: 'Process new recording',
    href: '/dashboard/calls/new',
    icon: Phone,
    iconBg: 'bg-primary-100 group-hover:bg-primary-200',
    iconColor: 'text-primary-600',
  },
  {
    label: 'Generate Content',
    description: 'Create sales deck',
    href: '/dashboard/content/new',
    icon: FileText,
    iconBg: 'bg-accent-100 group-hover:bg-accent-200',
    iconColor: 'text-accent-600',
  },
  {
    label: 'Enrich Prospect',
    description: 'Get company intel',
    href: '/dashboard/prospects/enrich',
    icon: UserSearch,
    iconBg: 'bg-success-100 group-hover:bg-success-200',
    iconColor: 'text-success-600',
  },
  {
    label: 'Update Pipeline',
    description: 'Manage deals',
    href: '/dashboard/pipelines',
    icon: Target,
    iconBg: 'bg-warning-100 group-hover:bg-warning-200',
    iconColor: 'text-warning-600',
  },
  {
    label: 'Import Data',
    description: 'Sync from CRM',
    href: '/dashboard/import',
    icon: Upload,
    iconBg: 'bg-slate-100 group-hover:bg-slate-200',
    iconColor: 'text-slate-600',
  },
  {
    label: 'AI Assistant',
    description: 'Ask anything',
    href: '/dashboard/assistant',
    icon: Sparkles,
    iconBg: 'bg-gradient-to-br from-primary-100 to-accent-100 group-hover:from-primary-200 group-hover:to-accent-200',
    iconColor: 'text-primary-600',
  },
]

interface QuickActionsProps {
  loading?: boolean
}

export function QuickActions({ loading = false }: QuickActionsProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-100 shadow-card p-5">
        <div className="h-5 bg-slate-200 rounded w-28 mb-4 animate-pulse" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-card p-5">
      <h3 className="font-semibold text-slate-900 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {quickActions.map((action) => {
          const Icon = action.icon
          return (
            <Link
              key={action.label}
              href={action.href}
              className="quick-action-btn group"
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${action.iconBg}`}>
                <Icon className={`w-5 h-5 ${action.iconColor}`} />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-slate-900">{action.label}</p>
                <p className="text-xs text-slate-500">{action.description}</p>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
