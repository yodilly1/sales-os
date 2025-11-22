'use client'

import { useState } from 'react'
import { Users, Phone, FileText, Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, DataTable, Column } from '@/components/charts'
import { formatCurrency, formatNumber, formatScore } from '@/lib/utils/format'
import { cn } from '@/lib/utils/cn'
import type { DateRange } from '@/lib/types/analytics'

// Mock data
const teamTrendData = [
  { date: '2024-01-01', calls: 145, content: 42, deals: 8 },
  { date: '2024-01-02', calls: 168, content: 48, deals: 10 },
  { date: '2024-01-03', calls: 152, content: 45, deals: 7 },
  { date: '2024-01-04', calls: 178, content: 52, deals: 12 },
  { date: '2024-01-05', calls: 165, content: 50, deals: 9 },
  { date: '2024-01-06', calls: 142, content: 38, deals: 6 },
  { date: '2024-01-07', calls: 175, content: 55, deals: 11 },
  { date: '2024-01-08', calls: 188, content: 58, deals: 14 },
  { date: '2024-01-09', calls: 172, content: 52, deals: 10 },
  { date: '2024-01-10', calls: 195, content: 62, deals: 15 },
]

interface TeamMember {
  id: string
  name: string
  avatar: string
  calls: number
  contentGenerated: number
  prospectsEnriched: number
  dealsWon: number
  dealValue: number
  spicedScore: number
  rank: number
  previousRank: number
  trend: 'up' | 'down' | 'stable'
}

const teamPerformance: TeamMember[] = [
  { id: '1', name: 'Sarah Johnson', avatar: 'SJ', calls: 125, contentGenerated: 45, prospectsEnriched: 82, dealsWon: 8, dealValue: 245000, spicedScore: 8.5, rank: 1, previousRank: 2, trend: 'up' },
  { id: '2', name: 'Michael Chen', avatar: 'MC', calls: 118, contentGenerated: 38, prospectsEnriched: 75, dealsWon: 7, dealValue: 218000, spicedScore: 8.2, rank: 2, previousRank: 1, trend: 'down' },
  { id: '3', name: 'Emily Davis', avatar: 'ED', calls: 105, contentGenerated: 52, prospectsEnriched: 68, dealsWon: 6, dealValue: 185000, spicedScore: 7.9, rank: 3, previousRank: 3, trend: 'stable' },
  { id: '4', name: 'David Wilson', avatar: 'DW', calls: 98, contentGenerated: 35, prospectsEnriched: 62, dealsWon: 5, dealValue: 162000, spicedScore: 7.6, rank: 4, previousRank: 5, trend: 'up' },
  { id: '5', name: 'Jessica Martinez', avatar: 'JM', calls: 92, contentGenerated: 42, prospectsEnriched: 58, dealsWon: 5, dealValue: 148000, spicedScore: 7.8, rank: 5, previousRank: 4, trend: 'down' },
  { id: '6', name: 'James Brown', avatar: 'JB', calls: 88, contentGenerated: 32, prospectsEnriched: 52, dealsWon: 4, dealValue: 125000, spicedScore: 7.4, rank: 6, previousRank: 7, trend: 'up' },
  { id: '7', name: 'Amanda Taylor', avatar: 'AT', calls: 82, contentGenerated: 28, prospectsEnriched: 48, dealsWon: 4, dealValue: 112000, spicedScore: 7.2, rank: 7, previousRank: 6, trend: 'down' },
  { id: '8', name: 'Robert Lee', avatar: 'RL', calls: 78, contentGenerated: 25, prospectsEnriched: 45, dealsWon: 3, dealValue: 95000, spicedScore: 7.0, rank: 8, previousRank: 8, trend: 'stable' },
]

const topByMetric = {
  calls: teamPerformance.slice().sort((a, b) => b.calls - a.calls).slice(0, 5),
  content: teamPerformance.slice().sort((a, b) => b.contentGenerated - a.contentGenerated).slice(0, 5),
  deals: teamPerformance.slice().sort((a, b) => b.dealValue - a.dealValue).slice(0, 5),
  spiced: teamPerformance.slice().sort((a, b) => b.spicedScore - a.spicedScore).slice(0, 5),
}

const teamColumns: Column<TeamMember>[] = [
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
  metric: 'calls' | 'content' | 'deals' | 'spiced'
  icon: React.ReactNode
  formatValue: (member: TeamMember) => string
}

function Leaderboard({ title, metric, icon, formatValue }: LeaderboardProps) {
  const data = topByMetric[metric]

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center gap-2">
        <div className="text-primary-600">{icon}</div>
        <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
      </div>
      <div className="divide-y divide-gray-100">
        {data.map((member, index) => (
          <div key={member.id} className="px-4 py-3 flex items-center justify-between">
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
                  <span className="text-xs font-medium text-primary-700">{member.avatar}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{member.name}</span>
              </div>
            </div>
            <span className="text-sm font-semibold text-gray-900">{formatValue(member)}</span>
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

  const handleExport = async (exportFormat: 'csv' | 'pdf') => {
    console.log('Exporting team as', exportFormat)
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
          value="8"
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Calls/Rep"
          value="98"
          metric={{ value: 98, change: 8, changePercent: 8.9, trend: 'up' }}
          icon={<Phone className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Content/Rep"
          value="37"
          metric={{ value: 37, change: 5, changePercent: 15.6, trend: 'up' }}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Deal Value"
          value="$161K"
          metric={{ value: 161250, change: 12500, changePercent: 8.4, trend: 'up' }}
          icon={<Trophy className="w-6 h-6" />}
        />
      </div>

      {/* Team Activity Trend */}
      <ChartCard title="Team Activity Trend" description="Combined team metrics over time">
        <LineChart
          data={teamTrendData}
          xAxisKey="date"
          xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
          lines={[
            { dataKey: 'calls', name: 'Calls', color: '#0ea5e9' },
            { dataKey: 'content', name: 'Content', color: '#22c55e' },
            { dataKey: 'deals', name: 'Deals', color: '#f59e0b' },
          ]}
          height={300}
        />
      </ChartCard>

      {/* Leaderboards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Leaderboard
          title="Top by Calls"
          metric="calls"
          icon={<Phone className="w-4 h-4" />}
          formatValue={(m) => formatNumber(m.calls)}
        />
        <Leaderboard
          title="Top by Content"
          metric="content"
          icon={<FileText className="w-4 h-4" />}
          formatValue={(m) => formatNumber(m.contentGenerated)}
        />
        <Leaderboard
          title="Top by Deal Value"
          metric="deals"
          icon={<Trophy className="w-4 h-4" />}
          formatValue={(m) => formatCurrency(m.dealValue)}
        />
        <Leaderboard
          title="Top by SPICED"
          metric="spiced"
          icon={<TrendingUp className="w-4 h-4" />}
          formatValue={(m) => formatScore(m.spicedScore)}
        />
      </div>

      {/* Team Performance Bar Chart */}
      <ChartCard title="Performance Comparison" description="Deal value by team member">
        <BarChart
          data={teamPerformance}
          xAxisKey="name"
          bars={[{ dataKey: 'dealValue', name: 'Deal Value', color: '#0ea5e9' }]}
          yAxisFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          height={280}
          colorByValue
          colors={['#22c55e', '#0ea5e9', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4', '#f97316', '#84cc16']}
        />
      </ChartCard>

      {/* Full Team Performance Table */}
      <ChartCard title="Team Leaderboard" description="Complete team performance breakdown">
        <DataTable
          data={teamPerformance}
          columns={teamColumns}
          keyField="id"
          maxHeight="500px"
          stickyHeader
        />
      </ChartCard>
    </div>
  )
}
