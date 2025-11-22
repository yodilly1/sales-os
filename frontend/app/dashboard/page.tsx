'use client'

import {
  Phone,
  FileText,
  Users,
  Target,
  TrendingUp,
  DollarSign,
} from 'lucide-react'
import { MetricCard, ActivityFeed, QuickActions, WelcomeBanner } from '@/components/dashboard'

// Mock metrics data - in production this would come from API
const metrics = {
  callsProcessed: { value: 247, change: 12.5 },
  contentGenerated: { value: 89, change: 8.3 },
  prospectsEnriched: { value: 156, change: 23.1 },
  pipelineValue: { value: 2450000, change: 5.7 },
  dealsClosed: { value: 34, change: -2.1 },
  conversionRate: { value: 24, change: 3.2 },
}

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Welcome Banner */}
      <WelcomeBanner userName="Alex" pendingCalls={3} />

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
