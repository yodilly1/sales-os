'use client'

import { useState, useEffect } from 'react'
import { Phone, Clock, Award, TrendingUp, Loader2, AlertCircle } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart, DataTable, Column } from '@/components/charts'
import { formatDuration, formatDate, formatScore } from '@/lib/utils/format'
import type { DateRange, MetricValue, CallVolumeData, CallDurationData, SpicedScoreData } from '@/lib/types/analytics'

interface CallMetricsData {
  totalCalls: MetricValue
  avgDuration: MetricValue
  avgSpicedScore: MetricValue
  answerRate: MetricValue
}

interface SpicedDistributionData {
  name: string
  value: number
  color: string
}

interface SpicedByCategory {
  category: string
  score: number
}

interface CallRecord {
  id: string
  date: string
  prospect: string
  duration: number
  spicedScore: number
  outcome: string
  rep: string
}

const defaultMetrics: CallMetricsData = {
  totalCalls: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  avgDuration: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  avgSpicedScore: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  answerRate: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
}

const callColumns: Column<CallRecord>[] = [
  {
    key: 'date',
    header: 'Date',
    width: '100px',
    sortable: true,
    render: (value) => formatDate(value as string, 'MMM d'),
  },
  {
    key: 'prospect',
    header: 'Prospect',
    sortable: true,
  },
  {
    key: 'rep',
    header: 'Rep',
    width: '100px',
  },
  {
    key: 'duration',
    header: 'Duration',
    width: '90px',
    align: 'right',
    sortable: true,
    render: (value) => formatDuration(value as number),
  },
  {
    key: 'spicedScore',
    header: 'SPICED',
    width: '80px',
    align: 'right',
    sortable: true,
    render: (value) => {
      const score = value as number
      const color = score >= 8 ? 'text-success-600' : score >= 6 ? 'text-primary-600' : score >= 4 ? 'text-warning-600' : 'text-danger-600'
      return <span className={`font-medium ${color}`}>{formatScore(score)}</span>
    },
  },
  {
    key: 'outcome',
    header: 'Outcome',
    render: (value) => {
      const outcome = value as string
      const colors: Record<string, string> = {
        'Meeting Scheduled': 'bg-success-50 text-success-700',
        'Proposal Sent': 'bg-primary-50 text-primary-700',
        'Qualified': 'bg-primary-50 text-primary-700',
        'Follow-up': 'bg-warning-50 text-warning-700',
        'Not Qualified': 'bg-gray-100 text-gray-600',
        'Closed Won': 'bg-success-50 text-success-700',
      }
      return (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[outcome] || 'bg-gray-100 text-gray-600'}`}>
          {outcome}
        </span>
      )
    },
  },
]

export default function CallAnalyticsPage() {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd'),
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<CallMetricsData>(defaultMetrics)
  const [callVolumeData, setCallVolumeData] = useState<CallVolumeData[]>([])
  const [callDurationData, setCallDurationData] = useState<CallDurationData[]>([])
  const [spicedScoreData, setSpicedScoreData] = useState<SpicedScoreData[]>([])
  const [spicedDistribution, setSpicedDistribution] = useState<SpicedDistributionData[]>([])
  const [spicedByCategory, setSpicedByCategory] = useState<SpicedByCategory[]>([])
  const [recentCalls, setRecentCalls] = useState<CallRecord[]>([])

  useEffect(() => {
    loadCallsData()
  }, [dateRange])

  const loadCallsData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
      })

      // Fetch all call data in parallel
      const [metricsRes, volumeRes, durationRes, spicedRes, distributionRes] = await Promise.all([
        fetch(`/api/v1/analytics/calls/metrics?${params}`),
        fetch(`/api/v1/analytics/calls/volume?${params}`),
        fetch(`/api/v1/analytics/calls/duration?${params}`),
        fetch(`/api/v1/analytics/calls/spiced-scores?${params}`),
        fetch(`/api/v1/analytics/calls/spiced-distribution?${params}`),
      ])

      // Process metrics
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics({
          totalCalls: data.data?.total_calls || data.data?.totalCalls || defaultMetrics.totalCalls,
          avgDuration: data.data?.avg_duration || data.data?.avgDuration || defaultMetrics.avgDuration,
          avgSpicedScore: data.data?.avg_spiced_score || data.data?.avgSpicedScore || defaultMetrics.avgSpicedScore,
          answerRate: data.data?.conversion_rate || data.data?.conversionRate || defaultMetrics.answerRate,
        })
      }

      // Process volume data
      if (volumeRes.ok) {
        const data = await volumeRes.json()
        if (Array.isArray(data.data)) {
          setCallVolumeData(data.data)
        }
      }

      // Process duration data
      if (durationRes.ok) {
        const data = await durationRes.json()
        if (Array.isArray(data.data)) {
          setCallDurationData(data.data.map((d: { date: string; avg_duration?: number; avgDuration?: number; min_duration?: number; minDuration?: number; max_duration?: number; maxDuration?: number }) => ({
            date: d.date,
            avgDuration: d.avg_duration || d.avgDuration || 0,
            minDuration: d.min_duration || d.minDuration || 0,
            maxDuration: d.max_duration || d.maxDuration || 0,
          })))
        }
      }

      // Process SPICED scores
      if (spicedRes.ok) {
        const data = await spicedRes.json()
        if (Array.isArray(data.data)) {
          setSpicedScoreData(data.data.map((d: { date: string; situation: number; pain: number; impact: number; critical_event?: number; criticalEvent?: number; decision: number; overall: number }) => ({
            date: d.date,
            situation: d.situation,
            pain: d.pain,
            impact: d.impact,
            criticalEvent: d.critical_event || d.criticalEvent || 0,
            decision: d.decision,
            overall: d.overall,
          })))

          // Calculate average by category from the data
          if (data.data.length > 0) {
            const avgSituation = data.data.reduce((sum: number, d: { situation: number }) => sum + d.situation, 0) / data.data.length
            const avgPain = data.data.reduce((sum: number, d: { pain: number }) => sum + d.pain, 0) / data.data.length
            const avgImpact = data.data.reduce((sum: number, d: { impact: number }) => sum + d.impact, 0) / data.data.length
            const avgCriticalEvent = data.data.reduce((sum: number, d: { critical_event?: number; criticalEvent?: number }) => sum + (d.critical_event || d.criticalEvent || 0), 0) / data.data.length
            const avgDecision = data.data.reduce((sum: number, d: { decision: number }) => sum + d.decision, 0) / data.data.length

            setSpicedByCategory([
              { category: 'Situation', score: Math.round(avgSituation * 10) / 10 },
              { category: 'Pain', score: Math.round(avgPain * 10) / 10 },
              { category: 'Impact', score: Math.round(avgImpact * 10) / 10 },
              { category: 'Critical Event', score: Math.round(avgCriticalEvent * 10) / 10 },
              { category: 'Decision', score: Math.round(avgDecision * 10) / 10 },
            ])
          }
        }
      }

      // Process distribution
      if (distributionRes.ok) {
        const data = await distributionRes.json()
        if (Array.isArray(data.data)) {
          const colors = ['#22c55e', '#0ea5e9', '#f59e0b', '#ef4444']
          setSpicedDistribution(data.data.map((d: { range: string; percentage: number }, i: number) => ({
            name: d.range,
            value: d.percentage,
            color: colors[i] || '#6b7280',
          })))
        }
      }

      // For recent calls, we don't have a specific endpoint yet, so show empty
      setRecentCalls([])

    } catch (err) {
      console.error('Failed to load call analytics:', err)
      setError('Failed to load call analytics data. Please try again.')
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
          <p className="text-neutral-600">Loading call analytics...</p>
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
            onClick={loadCallsData}
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
          <h2 className="text-2xl font-bold text-gray-900">Call Analytics</h2>
          <p className="mt-1 text-sm text-gray-500">
            Track call volume, duration, and SPICED methodology scores
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
          title="Avg Duration"
          value={`${Math.round(metrics.avgDuration.value)}m`}
          metric={metrics.avgDuration}
          icon={<Clock className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg SPICED Score"
          value={`${metrics.avgSpicedScore.value.toFixed(1)}/10`}
          metric={metrics.avgSpicedScore}
          icon={<Award className="w-6 h-6" />}
        />
        <MetricCard
          title="Answer Rate"
          value={`${metrics.answerRate.value.toFixed(1)}%`}
          metric={metrics.answerRate}
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Call Volume Trend" description="Daily call volume over time">
          {callVolumeData.length > 0 ? (
            <LineChart
              data={callVolumeData}
              xAxisKey="date"
              xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
              lines={[
                { dataKey: 'calls', name: 'Total Calls', color: '#0ea5e9' },
                { dataKey: 'answered', name: 'Answered', color: '#22c55e' },
                { dataKey: 'missed', name: 'Missed', color: '#ef4444', dashed: true },
              ]}
              height={280}
            />
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-500">
              No call volume data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Call Duration Trend" description="Average call duration in minutes">
          {callDurationData.length > 0 ? (
            <LineChart
              data={callDurationData}
              xAxisKey="date"
              xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
              yAxisFormatter={(value) => `${value}m`}
              lines={[
                { dataKey: 'avgDuration', name: 'Average', color: '#0ea5e9' },
                { dataKey: 'maxDuration', name: 'Max', color: '#22c55e', dashed: true },
                { dataKey: 'minDuration', name: 'Min', color: '#f59e0b', dashed: true },
              ]}
              height={280}
            />
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-500">
              No duration data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* Charts Row 2 - SPICED Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="SPICED Score Trend"
          description="Overall methodology scores over time"
          className="lg:col-span-2"
        >
          {spicedScoreData.length > 0 ? (
            <LineChart
              data={spicedScoreData}
              xAxisKey="date"
              xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
              yAxisFormatter={(value) => value.toFixed(1)}
              lines={[
                { dataKey: 'overall', name: 'Overall', color: '#0ea5e9', strokeWidth: 3 },
                { dataKey: 'situation', name: 'Situation', color: '#22c55e' },
                { dataKey: 'pain', name: 'Pain', color: '#f59e0b' },
                { dataKey: 'impact', name: 'Impact', color: '#8b5cf6' },
                { dataKey: 'criticalEvent', name: 'Critical Event', color: '#ec4899' },
                { dataKey: 'decision', name: 'Decision', color: '#06b6d4' },
              ]}
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No SPICED score data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Score Distribution" description="SPICED score ranges">
          {spicedDistribution.length > 0 ? (
            <PieChart
              data={spicedDistribution}
              height={300}
              innerRadius={50}
              outerRadius={90}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No distribution data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* SPICED by Category */}
      <ChartCard title="SPICED by Category" description="Average scores per methodology component">
        {spicedByCategory.length > 0 ? (
          <BarChart
            data={spicedByCategory}
            xAxisKey="category"
            bars={[{ dataKey: 'score', name: 'Score', color: '#0ea5e9' }]}
            yAxisFormatter={(value) => value.toFixed(1)}
            height={250}
            colorByValue
            colors={['#22c55e', '#0ea5e9', '#8b5cf6', '#f59e0b', '#06b6d4']}
          />
        ) : (
          <div className="flex items-center justify-center h-[250px] text-gray-500">
            No category data available
          </div>
        )}
      </ChartCard>

      {/* Recent Calls Table */}
      <ChartCard title="Recent Calls" description="Detailed breakdown of recent call activity">
        {recentCalls.length > 0 ? (
          <DataTable
            data={recentCalls}
            columns={callColumns}
            keyField="id"
            maxHeight="400px"
            stickyHeader
          />
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            No recent calls to display. Upload transcripts to see call data here.
          </div>
        )}
      </ChartCard>
    </div>
  )
}
