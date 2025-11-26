'use client'

import { useState, useEffect } from 'react'
import { Phone, FileText, Users, DollarSign, TrendingUp, Activity, Loader2, AlertCircle } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart } from '@/components/charts'
import type { DateRange, MetricValue } from '@/lib/types/analytics'

interface OverviewMetrics {
  totalCalls: MetricValue
  contentGenerated: MetricValue
  prospectsEnriched: MetricValue
  pipelineValue: MetricValue
}

interface TrendDataPoint {
  date: string
  calls: number
  content: number
  deals: number
}

interface DistributionDataPoint {
  name: string
  value: number
  color: string
}

interface PerformerData {
  name: string
  calls: number
  deals: number
  value: number
}

const defaultMetrics: OverviewMetrics = {
  totalCalls: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  contentGenerated: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  prospectsEnriched: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  pipelineValue: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
}

export default function AnalyticsOverviewPage() {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd'),
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<OverviewMetrics>(defaultMetrics)
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([])
  const [distributionData, setDistributionData] = useState<DistributionDataPoint[]>([])
  const [performerData, setPerformerData] = useState<PerformerData[]>([])
  const [quickStats, setQuickStats] = useState({
    avgSpicedScore: 0,
    spicedChange: 0,
    conversionRate: 0,
    conversionChange: 0,
    avgCallDuration: 0,
    contentEngagement: 0,
    engagementChange: 0,
  })

  useEffect(() => {
    loadOverviewData()
  }, [dateRange])

  const loadOverviewData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
      })

      // Fetch all overview data in parallel
      const [callsRes, contentRes, pipelineRes, teamRes] = await Promise.all([
        fetch(`/api/v1/analytics/calls/metrics?${params}`),
        fetch(`/api/v1/analytics/content/metrics?${params}`),
        fetch(`/api/v1/analytics/pipeline/metrics?${params}`),
        fetch(`/api/v1/analytics/team/trends?${params}`),
      ])

      // Process responses
      if (callsRes.ok) {
        const callsData = await callsRes.json()
        setMetrics(prev => ({
          ...prev,
          totalCalls: callsData.data?.total_calls || callsData.data?.totalCalls || prev.totalCalls,
        }))
        setQuickStats(prev => ({
          ...prev,
          avgSpicedScore: callsData.data?.avg_spiced_score?.value || callsData.data?.avgSpicedScore?.value || 0,
          spicedChange: callsData.data?.avg_spiced_score?.change || callsData.data?.avgSpicedScore?.change || 0,
          avgCallDuration: callsData.data?.avg_duration?.value || callsData.data?.avgDuration?.value || 0,
          conversionRate: callsData.data?.conversion_rate?.value || callsData.data?.conversionRate?.value || 0,
          conversionChange: callsData.data?.conversion_rate?.change_percent || callsData.data?.conversionRate?.changePercent || 0,
        }))
      }

      if (contentRes.ok) {
        const contentData = await contentRes.json()
        setMetrics(prev => ({
          ...prev,
          contentGenerated: contentData.data?.total_generated || contentData.data?.totalGenerated || prev.contentGenerated,
        }))
        setQuickStats(prev => ({
          ...prev,
          contentEngagement: contentData.data?.engagement_rate?.value || contentData.data?.engagementRate?.value || 0,
          engagementChange: contentData.data?.engagement_rate?.change_percent || contentData.data?.engagementRate?.changePercent || 0,
        }))
      }

      if (pipelineRes.ok) {
        const pipelineData = await pipelineRes.json()
        setMetrics(prev => ({
          ...prev,
          prospectsEnriched: pipelineData.data?.prospects_enriched || pipelineData.data?.prospectsEnriched || prev.prospectsEnriched,
          pipelineValue: pipelineData.data?.pipeline_value || pipelineData.data?.pipelineValue || prev.pipelineValue,
        }))
      }

      if (teamRes.ok) {
        const teamData = await teamRes.json()
        if (Array.isArray(teamData.data)) {
          setTrendData(teamData.data.map((d: { date: string; calls: number; content: number; deals: number }) => ({
            date: d.date,
            calls: d.calls,
            content: d.content,
            deals: d.deals,
          })))
        }
      }

      // Set default distribution data (this would ideally come from backend)
      setDistributionData([
        { name: 'Calls', value: metrics.totalCalls.value || 45, color: '#0ea5e9' },
        { name: 'Content', value: metrics.contentGenerated.value || 30, color: '#22c55e' },
        { name: 'Enrichment', value: metrics.prospectsEnriched.value || 15, color: '#f59e0b' },
        { name: 'Coaching', value: 10, color: '#8b5cf6' },
      ])

      // Fetch top performers from leaderboard
      const leaderboardRes = await fetch(`/api/v1/analytics/team/leaderboard?${params}&metric=deals`)
      if (leaderboardRes.ok) {
        const leaderboardData = await leaderboardRes.json()
        if (Array.isArray(leaderboardData.data)) {
          setPerformerData(leaderboardData.data.slice(0, 4).map((d: { name: string; metric: number }) => ({
            name: d.name,
            calls: 0,
            deals: 0,
            value: d.metric,
          })))
        }
      }

    } catch (err) {
      console.error('Failed to load analytics overview:', err)
      setError('Failed to load analytics data. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async (exportFormat: 'csv' | 'pdf') => {
    try {
      const params = new URLSearchParams({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
        format: exportFormat,
      })

      window.open(`/api/v1/analytics/calls/export?${params}`, '_blank')
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-neutral-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-neutral-600 mb-4">{error}</p>
          <button
            onClick={loadOverviewData}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Overview</h2>
          <p className="mt-1 text-sm text-gray-500">
            High-level insights into your sales performance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <DateRangePicker value={dateRange} onChange={setDateRange} />
          <ExportButton onExport={handleExport} />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Calls"
          value={metrics.totalCalls.value.toLocaleString()}
          metric={metrics.totalCalls}
          icon={<Phone className="w-6 h-6" />}
        />
        <MetricCard
          title="Content Generated"
          value={metrics.contentGenerated.value.toLocaleString()}
          metric={metrics.contentGenerated}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          title="Prospects Enriched"
          value={metrics.prospectsEnriched.value.toLocaleString()}
          metric={metrics.prospectsEnriched}
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          title="Pipeline Value"
          value={`$${(metrics.pipelineValue.value / 1000000).toFixed(1)}M`}
          metric={metrics.pipelineValue}
          icon={<DollarSign className="w-6 h-6" />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Activity Trends"
          description="Daily activity across all categories"
          className="lg:col-span-2"
        >
          {trendData.length > 0 ? (
            <LineChart
              data={trendData}
              xAxisKey="date"
              xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
              lines={[
                { dataKey: 'calls', name: 'Calls', color: '#0ea5e9' },
                { dataKey: 'content', name: 'Content', color: '#22c55e' },
                { dataKey: 'deals', name: 'Deals', color: '#f59e0b' },
              ]}
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No trend data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Activity Distribution" description="Breakdown by category">
          {distributionData.length > 0 ? (
            <PieChart
              data={distributionData}
              height={300}
              innerRadius={60}
              outerRadius={100}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No distribution data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Top Performers" description="By deal value this period">
          {performerData.length > 0 ? (
            <BarChart
              data={performerData}
              xAxisKey="name"
              layout="vertical"
              bars={[{ dataKey: 'value', name: 'Deal Value', color: '#0ea5e9' }]}
              yAxisFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              height={280}
            />
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-500">
              No performer data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Quick Stats" description="Performance highlights">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">Avg SPICED Score</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{quickStats.avgSpicedScore.toFixed(1)}/10</p>
              <p className={`text-sm ${quickStats.spicedChange >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {quickStats.spicedChange >= 0 ? '+' : ''}{quickStats.spicedChange.toFixed(1)} vs last period
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Activity className="w-4 h-4" />
                <span className="text-sm">Conversion Rate</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{quickStats.conversionRate.toFixed(1)}%</p>
              <p className={`text-sm ${quickStats.conversionChange >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {quickStats.conversionChange >= 0 ? '+' : ''}{quickStats.conversionChange.toFixed(1)}% vs last period
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Phone className="w-4 h-4" />
                <span className="text-sm">Avg Call Duration</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{Math.round(quickStats.avgCallDuration)}m</p>
              <p className="text-sm text-gray-500">No change</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <FileText className="w-4 h-4" />
                <span className="text-sm">Content Engagement</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{quickStats.contentEngagement.toFixed(0)}%</p>
              <p className={`text-sm ${quickStats.engagementChange >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {quickStats.engagementChange >= 0 ? '+' : ''}{quickStats.engagementChange.toFixed(0)}% vs last period
              </p>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
