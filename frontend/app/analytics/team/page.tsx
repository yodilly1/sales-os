'use client'

import { useState, useEffect } from 'react'
import { Users, Phone, FileText, Trophy, TrendingUp, TrendingDown, Minus, Loader2, AlertCircle } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, DataTable, Column } from '@/components/charts'
import { formatCurrency, formatNumber, formatScore } from '@/lib/utils/format'
import { cn } from '@/lib/utils/cn'
import type { DateRange, MetricValue, TeamMemberPerformance, TeamTrendData, LeaderboardEntry } from '@/lib/types/analytics'

interface TeamMetricsData {
  totalMembers: number
  avgCallsPerRep: MetricValue
  avgContentPerRep: MetricValue
  avgDealValue: MetricValue
}

const defaultMetrics: TeamMetricsData = {
  totalMembers: 0,
  avgCallsPerRep: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  avgContentPerRep: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  avgDealValue: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
}

const teamColumns: Column<TeamMemberPerformance>[] = [
  {
    key: 'rank',
    header: '#',
    width: '50px',
    align: 'center',
    render: (value, row) => {
      const TrendIcon = row.trend === 'up' ? TrendingUp : row.trend === 'down' ? TrendingDown : Minus
      const trendColor = row.trend === 'up' ? 'text-success-600' : row.trend === 'down' ? 'text-danger-600' : 'text-gray-400'
      return (
        <div className="flex items-center gap-1">
          <span className="font-bold text-gray-900">{value as number}</span>
          <TrendIcon className={cn('w-3 h-3', trendColor)} />
        </div>
      )
    },
  },
  {
    key: 'name',
    header: 'Team Member',
    sortable: true,
    render: (value, row) => (
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
          <span className="text-xs font-medium text-primary-700">{row.avatar}</span>
        </div>
        <span className="font-medium text-gray-900">{value as string}</span>
      </div>
    ),
  },
  {
    key: 'calls',
    header: 'Calls',
    width: '80px',
    align: 'right',
    sortable: true,
    render: (value) => formatNumber(value as number),
  },
  {
    key: 'contentGenerated',
    header: 'Content',
    width: '80px',
    align: 'right',
    sortable: true,
    render: (value) => formatNumber(value as number),
  },
  {
    key: 'prospectsEnriched',
    header: 'Prospects',
    width: '90px',
    align: 'right',
    sortable: true,
    render: (value) => formatNumber(value as number),
  },
  {
    key: 'dealsWon',
    header: 'Deals',
    width: '70px',
    align: 'right',
    sortable: true,
    render: (value) => formatNumber(value as number),
  },
  {
    key: 'dealValue',
    header: 'Value',
    width: '100px',
    align: 'right',
    sortable: true,
    render: (value) => formatCurrency(value as number),
  },
  {
    key: 'spicedScore',
    header: 'SPICED',
    width: '80px',
    align: 'right',
    sortable: true,
    render: (value) => {
      const score = value as number
      const color = score >= 8 ? 'text-success-600' : score >= 7 ? 'text-primary-600' : 'text-warning-600'
      return <span className={`font-medium ${color}`}>{formatScore(score)}</span>
    },
  },
]

interface LeaderboardProps {
  title: string
  data: LeaderboardEntry[]
  icon: React.ReactNode
  formatValue: (entry: LeaderboardEntry) => string
}

function Leaderboard({ title, data, icon, formatValue }: LeaderboardProps) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
          <div className="text-primary-600">{icon}</div>
          <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
        </div>
        <div className="flex items-center justify-center h-[200px] text-gray-500">
          No data available
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
        <div className="text-primary-600">{icon}</div>
        <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
      </div>
      <div className="divide-y divide-gray-100">
        {data.map((entry, index) => (
          <div key={entry.userId} className="px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={cn(
                'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                index === 0 ? 'bg-yellow-100 text-yellow-700' :
                index === 1 ? 'bg-gray-100 text-gray-600' :
                index === 2 ? 'bg-orange-100 text-orange-700' :
                'bg-gray-50 text-gray-500'
              )}>
                {index + 1}
              </span>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-xs font-medium text-primary-700">{entry.avatar || entry.name.substring(0, 2)}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{entry.name}</span>
              </div>
            </div>
            <span className="text-sm font-semibold text-gray-900">{formatValue(entry)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function TeamAnalyticsPage() {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd'),
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<TeamMetricsData>(defaultMetrics)
  const [trendData, setTrendData] = useState<TeamTrendData[]>([])
  const [teamPerformance, setTeamPerformance] = useState<TeamMemberPerformance[]>([])
  const [leaderboards, setLeaderboards] = useState<{
    calls: LeaderboardEntry[]
    content: LeaderboardEntry[]
    deals: LeaderboardEntry[]
    spiced: LeaderboardEntry[]
  }>({
    calls: [],
    content: [],
    deals: [],
    spiced: [],
  })

  useEffect(() => {
    loadTeamData()
  }, [dateRange])

  const loadTeamData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
      })

      // Fetch all team data in parallel
      const [metricsRes, trendsRes, performanceRes, callsLbRes, contentLbRes, dealsLbRes, spicedLbRes] = await Promise.all([
        fetch(`/api/v1/analytics/team/metrics?${params}`),
        fetch(`/api/v1/analytics/team/trends?${params}`),
        fetch(`/api/v1/analytics/team/performance?${params}&sortBy=deals&pageSize=20`),
        fetch(`/api/v1/analytics/team/leaderboard?${params}&metric=calls`),
        fetch(`/api/v1/analytics/team/leaderboard?${params}&metric=content`),
        fetch(`/api/v1/analytics/team/leaderboard?${params}&metric=deals`),
        fetch(`/api/v1/analytics/team/leaderboard?${params}&metric=spiced`),
      ])

      // Process metrics
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics({
          totalMembers: data.data?.total_members || data.data?.totalMembers || 0,
          avgCallsPerRep: data.data?.avg_calls_per_rep || data.data?.avgCallsPerRep || defaultMetrics.avgCallsPerRep,
          avgContentPerRep: data.data?.avg_content_per_rep || data.data?.avgContentPerRep || defaultMetrics.avgContentPerRep,
          avgDealValue: data.data?.avg_deals_per_rep || data.data?.avgDealsPerRep || defaultMetrics.avgDealValue,
        })
      }

      // Process trends
      if (trendsRes.ok) {
        const data = await trendsRes.json()
        if (Array.isArray(data.data)) {
          setTrendData(data.data)
        }
      }

      // Process performance
      if (performanceRes.ok) {
        const data = await performanceRes.json()
        if (Array.isArray(data.data)) {
          setTeamPerformance(data.data.map((d: {
            id: string
            name: string
            avatar?: string
            calls: number
            content_generated?: number
            contentGenerated?: number
            prospects_enriched?: number
            prospectsEnriched?: number
            deals_won?: number
            dealsWon?: number
            deal_value?: number
            dealValue?: number
            spiced_score?: number
            spicedScore?: number
            rank: number
            trend: 'up' | 'down' | 'stable'
          }) => ({
            id: d.id,
            name: d.name,
            avatar: d.avatar,
            calls: d.calls,
            contentGenerated: d.content_generated || d.contentGenerated || 0,
            prospectsEnriched: d.prospects_enriched || d.prospectsEnriched || 0,
            dealsWon: d.deals_won || d.dealsWon || 0,
            dealValue: d.deal_value || d.dealValue || 0,
            spicedScore: d.spiced_score || d.spicedScore || 0,
            rank: d.rank,
            trend: d.trend,
          })))
        }
      }

      // Process leaderboards
      const processLeaderboard = async (res: Response): Promise<LeaderboardEntry[]> => {
        if (res.ok) {
          const data = await res.json()
          if (Array.isArray(data.data)) {
            return data.data.map((d: { rank: number; user_id?: string; userId?: string; name: string; avatar?: string; metric: number; change: number }) => ({
              rank: d.rank,
              userId: d.user_id || d.userId || d.name,
              name: d.name,
              avatar: d.avatar,
              metric: d.metric,
              change: d.change,
            }))
          }
        }
        return []
      }

      const [callsLb, contentLb, dealsLb, spicedLb] = await Promise.all([
        processLeaderboard(callsLbRes),
        processLeaderboard(contentLbRes),
        processLeaderboard(dealsLbRes),
        processLeaderboard(spicedLbRes),
      ])

      setLeaderboards({
        calls: callsLb,
        content: contentLb,
        deals: dealsLb,
        spiced: spicedLb,
      })

    } catch (err) {
      console.error('Failed to load team analytics:', err)
      setError('Failed to load team analytics data. Please try again.')
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
      window.open(`/api/v1/analytics/team/export?${params}`, '_blank')
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-neutral-600">Loading team analytics...</p>
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
            onClick={loadTeamData}
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
          <h2 className="text-2xl font-bold text-gray-900">Team Performance</h2>
          <p className="mt-1 text-sm text-gray-500">
            Track individual and team performance metrics
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
          title="Team Members"
          value={metrics.totalMembers.toString()}
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Calls/Rep"
          value={Math.round(metrics.avgCallsPerRep.value).toString()}
          metric={metrics.avgCallsPerRep}
          icon={<Phone className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Content/Rep"
          value={Math.round(metrics.avgContentPerRep.value).toString()}
          metric={metrics.avgContentPerRep}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Deal Value"
          value={formatCurrency(metrics.avgDealValue.value)}
          metric={metrics.avgDealValue}
          icon={<Trophy className="w-6 h-6" />}
        />
      </div>

      {/* Team Activity Trend */}
      <ChartCard title="Team Activity Trend" description="Combined team metrics over time">
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

      {/* Leaderboards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Leaderboard
          title="Top by Calls"
          data={leaderboards.calls}
          icon={<Phone className="w-4 h-4" />}
          formatValue={(entry) => formatNumber(entry.metric)}
        />
        <Leaderboard
          title="Top by Content"
          data={leaderboards.content}
          icon={<FileText className="w-4 h-4" />}
          formatValue={(entry) => formatNumber(entry.metric)}
        />
        <Leaderboard
          title="Top by Deal Value"
          data={leaderboards.deals}
          icon={<Trophy className="w-4 h-4" />}
          formatValue={(entry) => formatCurrency(entry.metric)}
        />
        <Leaderboard
          title="Top by SPICED"
          data={leaderboards.spiced}
          icon={<TrendingUp className="w-4 h-4" />}
          formatValue={(entry) => formatScore(entry.metric)}
        />
      </div>

      {/* Team Performance Bar Chart */}
      <ChartCard title="Performance Comparison" description="Deal value by team member">
        {teamPerformance.length > 0 ? (
          <BarChart
            data={teamPerformance}
            xAxisKey="name"
            bars={[{ dataKey: 'dealValue', name: 'Deal Value', color: '#0ea5e9' }]}
            yAxisFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            height={280}
            colorByValue
            colors={['#22c55e', '#0ea5e9', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4', '#f97316', '#84cc16']}
          />
        ) : (
          <div className="flex items-center justify-center h-[280px] text-gray-500">
            No performance data available
          </div>
        )}
      </ChartCard>

      {/* Full Team Performance Table */}
      <ChartCard title="Team Leaderboard" description="Complete team performance breakdown">
        {teamPerformance.length > 0 ? (
          <DataTable
            data={teamPerformance}
            columns={teamColumns}
            keyField="id"
            maxHeight="500px"
            stickyHeader
          />
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            No team data to display.
          </div>
        )}
      </ChartCard>
    </div>
  )
}
