'use client'

import { formatTimeAgo } from '@/lib/utils'
import {
  Phone,
  FileText,
  UserPlus,
  CheckCircle,
  AlertCircle,
  Sparkles,
  MessageSquare,
} from 'lucide-react'

type ActivityType =
  | 'call_processed'
  | 'content_generated'
  | 'prospect_enriched'
  | 'deal_updated'
  | 'coaching_complete'
  | 'alert'
  | 'ai_insight'

interface Activity {
  id: string
  type: ActivityType
  title: string
  description: string
  timestamp: Date
  metadata?: Record<string, string>
}

interface ActivityFeedProps {
  activities?: Activity[]
  loading?: boolean
  maxItems?: number
}

const activityConfig: Record<ActivityType, {
  icon: React.ComponentType<{ className?: string }>
  iconBg: string
  iconColor: string
}> = {
  call_processed: {
    icon: Phone,
    iconBg: 'bg-primary-100',
    iconColor: 'text-primary-600',
  },
  content_generated: {
    icon: FileText,
    iconBg: 'bg-accent-100',
    iconColor: 'text-accent-600',
  },
  prospect_enriched: {
    icon: UserPlus,
    iconBg: 'bg-success-100',
    iconColor: 'text-success-600',
  },
  deal_updated: {
    icon: CheckCircle,
    iconBg: 'bg-success-100',
    iconColor: 'text-success-600',
  },
  coaching_complete: {
    icon: MessageSquare,
    iconBg: 'bg-warning-100',
    iconColor: 'text-warning-600',
  },
  alert: {
    icon: AlertCircle,
    iconBg: 'bg-danger-100',
    iconColor: 'text-danger-600',
  },
  ai_insight: {
    icon: Sparkles,
    iconBg: 'bg-accent-100',
    iconColor: 'text-accent-600',
  },
}

// Mock data for demonstration
const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'call_processed',
    title: 'Call with Acme Corp analyzed',
    description: 'SPICED methodology score: 85/100. Key objection: Budget timing.',
    timestamp: new Date(Date.now() - 10 * 60 * 1000),
  },
  {
    id: '2',
    type: 'content_generated',
    title: 'Proposal deck created',
    description: 'Enterprise pricing proposal for TechStart Inc.',
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
  },
  {
    id: '3',
    type: 'prospect_enriched',
    title: 'New prospect data available',
    description: 'Updated org chart and decision-maker contacts for Global Industries.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
  },
  {
    id: '4',
    type: 'ai_insight',
    title: 'Deal velocity alert',
    description: 'MegaCorp deal has been in current stage 40% longer than average.',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
  },
  {
    id: '5',
    type: 'coaching_complete',
    title: 'Coaching session completed',
    description: 'Reviewed 3 discovery calls with improvement suggestions.',
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
  },
]

export function ActivityFeed({
  activities = mockActivities,
  loading = false,
  maxItems = 5,
}: ActivityFeedProps) {
  const displayActivities = activities.slice(0, maxItems)

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-slate-100 shadow-card">
        <div className="px-5 py-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">Recent Activity</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="px-5 py-4 animate-pulse">
              <div className="flex gap-3">
                <div className="w-9 h-9 bg-slate-200 rounded-lg flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-200 rounded w-3/4" />
                  <div className="h-3 bg-slate-200 rounded w-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-card">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <h3 className="font-semibold text-slate-900">Recent Activity</h3>
        <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          View all
        </button>
      </div>
      <div className="divide-y divide-slate-100">
        {displayActivities.map((activity) => {
          const config = activityConfig[activity.type]
          const Icon = config.icon

          return (
            <div
              key={activity.id}
              className="px-5 py-4 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <div className="flex gap-3">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${config.iconBg}`}>
                  <Icon className={`w-4 h-4 ${config.iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {activity.title}
                    </p>
                    <span className="text-xs text-slate-400 whitespace-nowrap">
                      {formatTimeAgo(activity.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 mt-0.5 line-clamp-2">
                    {activity.description}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
