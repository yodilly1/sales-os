'use client'

import { useState, useEffect } from 'react'
import {
  Phone,
  FileText,
  Users,
  Target,
  TrendingUp,
  DollarSign,
  Loader2,
} from 'lucide-react'
import { MetricCard, ActivityFeed, QuickActions, WelcomeBanner } from '@/components/dashboard'

interface DashboardMetrics {
  callsProcessed: { value: number; change: number }
  contentGenerated: { value: number; change: number }
  prospectsEnriched: { value: number; change: number }
  pipelineValue: { value: number; change: number }
  dealsClosed: { value: number; change: number }
  conversionRate: { value: number; change: number }
}

const defaultMetrics: DashboardMetrics = {
  callsProcessed: { value: 0, change: 0 },
  contentGenerated: { value: 0, change: 0 },
  prospectsEnriched: { value: 0, change: 0 },
  pipelineValue: { value: 0, change: 0 },
  dealsClosed: { value: 0, change: 0 },
  conversionRate: { value: 0, change: 0 },
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics>(defaultMetrics)
  const [isLoading, setIsLoading] = useState(true)
  const [userName, setUserName] = useState('User')

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true)
      try {
        // Try to fetch from analytics API
        const response = await fetch('/api/v1/analytics/overview')
        if (response.ok) {
          const data = await response.json()
          setMetrics({
            callsProcessed: { value: data.overview?.total_transcripts || 0, change: 0 },
            contentGenerated: { value: data.overview?.total_content || 0, change: 0 },
            prospectsEnriched: { value: data.overview?.total_prospects || 0, change: 0 },
            pipelineValue: { value: 0, change: 0 },
            dealsClosed: { value: data.overview?.total_campaigns || 0, change: 0 },
            conversionRate: { value: 0, change: 0 },
          })
        }
      } catch (err) {
        console.log('Dashboard API not available, showing empty state')
        // Keep default metrics (zeros)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-neutral-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Welcome Banner */}
      <WelcomeBanner userName={userName} pendingCalls={0} />

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          title="Calls Processed"
          value={metrics.callsProcessed.value}
          change={metrics.callsProcessed.change}
          icon={Phone}
          iconColor="primary"
        />
        <MetricCard
          title="Content Generated"
          value={metrics.contentGenerated.value}
          change={metrics.contentGenerated.change}
          icon={FileText}
          iconColor="accent"
        />
        <MetricCard
          title="Prospects Enriched"
          value={metrics.prospectsEnriched.value}
          change={metrics.prospectsEnriched.change}
          icon={Users}
          iconColor="success"
        />
        <MetricCard
          title="Pipeline Value"
          value={metrics.pipelineValue.value}
          change={metrics.pipelineValue.change}
          icon={DollarSign}
          iconColor="success"
          format="currency"
        />
        <MetricCard
          title="Deals Closed"
          value={metrics.dealsClosed.value}
          change={metrics.dealsClosed.change}
          icon={Target}
          iconColor="warning"
        />
        <MetricCard
          title="Conversion Rate"
          value={metrics.conversionRate.value}
          change={metrics.conversionRate.change}
          icon={TrendingUp}
          iconColor="primary"
          format="percentage"
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Feed - takes 2 columns */}
        <div className="lg:col-span-2">
          <ActivityFeed />
        </div>

        {/* Quick Actions - takes 1 column */}
        <div>
          <QuickActions />
        </div>
      </div>
    </div>
  )
}
