'use client'

import { useState } from 'react'
import { Phone, Clock, Award, TrendingUp } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart, DataTable, Column } from '@/components/charts'
import { formatDuration, formatDate, formatScore } from '@/lib/utils/format'
import type { DateRange } from '@/lib/types/analytics'

// Mock data
const callVolumeData = [
  { date: '2024-01-01', calls: 45, answered: 42, missed: 3 },
  { date: '2024-01-02', calls: 52, answered: 48, missed: 4 },
  { date: '2024-01-03', calls: 48, answered: 45, missed: 3 },
  { date: '2024-01-04', calls: 61, answered: 58, missed: 3 },
  { date: '2024-01-05', calls: 55, answered: 50, missed: 5 },
  { date: '2024-01-06', calls: 43, answered: 40, missed: 3 },
  { date: '2024-01-07', calls: 58, answered: 55, missed: 3 },
  { date: '2024-01-08', calls: 65, answered: 62, missed: 3 },
  { date: '2024-01-09', calls: 70, answered: 66, missed: 4 },
  { date: '2024-01-10', calls: 63, answered: 60, missed: 3 },
]

const callDurationData = [
  { date: '2024-01-01', avgDuration: 24, minDuration: 5, maxDuration: 45 },
  { date: '2024-01-02', avgDuration: 28, minDuration: 8, maxDuration: 52 },
  { date: '2024-01-03', avgDuration: 26, minDuration: 6, maxDuration: 48 },
  { date: '2024-01-04', avgDuration: 30, minDuration: 10, maxDuration: 55 },
  { date: '2024-01-05', avgDuration: 25, minDuration: 5, maxDuration: 42 },
  { date: '2024-01-06', avgDuration: 27, minDuration: 7, maxDuration: 50 },
  { date: '2024-01-07', avgDuration: 32, minDuration: 12, maxDuration: 58 },
]

const spicedScoreData = [
  { date: '2024-01-01', situation: 7.5, pain: 6.8, impact: 7.2, criticalEvent: 6.5, decision: 7.0, overall: 7.0 },
  { date: '2024-01-02', situation: 7.8, pain: 7.2, impact: 7.5, criticalEvent: 6.8, decision: 7.3, overall: 7.3 },
  { date: '2024-01-03', situation: 8.0, pain: 7.5, impact: 7.8, criticalEvent: 7.0, decision: 7.5, overall: 7.6 },
  { date: '2024-01-04', situation: 7.6, pain: 7.0, impact: 7.4, criticalEvent: 6.9, decision: 7.2, overall: 7.2 },
  { date: '2024-01-05', situation: 8.2, pain: 7.8, impact: 8.0, criticalEvent: 7.2, decision: 7.8, overall: 7.8 },
  { date: '2024-01-06', situation: 7.9, pain: 7.4, impact: 7.6, criticalEvent: 7.1, decision: 7.4, overall: 7.5 },
  { date: '2024-01-07', situation: 8.1, pain: 7.6, impact: 7.9, criticalEvent: 7.3, decision: 7.6, overall: 7.7 },
]

const spicedDistribution = [
  { name: 'Excellent (8-10)', value: 25, color: '#22c55e' },
  { name: 'Good (6-8)', value: 45, color: '#0ea5e9' },
  { name: 'Average (4-6)', value: 20, color: '#f59e0b' },
  { name: 'Needs Work (0-4)', value: 10, color: '#ef4444' },
]

const spicedByCategory = [
  { category: 'Situation', score: 7.8 },
  { category: 'Pain', score: 7.2 },
  { category: 'Impact', score: 7.5 },
  { category: 'Critical Event', score: 6.9 },
  { category: 'Decision', score: 7.3 },
]

interface CallRecord {
  id: string
  date: string
  prospect: string
  duration: number
  spicedScore: number
  outcome: string
  rep: string
}

const recentCalls: CallRecord[] = [
  { id: '1', date: '2024-01-10', prospect: 'Acme Corp', duration: 32, spicedScore: 8.2, outcome: 'Meeting Scheduled', rep: 'Sarah J.' },
  { id: '2', date: '2024-01-10', prospect: 'TechStart Inc', duration: 18, spicedScore: 6.5, outcome: 'Follow-up', rep: 'Michael C.' },
  { id: '3', date: '2024-01-09', prospect: 'Global Solutions', duration: 45, spicedScore: 9.1, outcome: 'Proposal Sent', rep: 'Emily D.' },
  { id: '4', date: '2024-01-09', prospect: 'DataFlow Systems', duration: 28, spicedScore: 7.4, outcome: 'Qualified', rep: 'David W.' },
  { id: '5', date: '2024-01-08', prospect: 'CloudNet Pro', duration: 22, spicedScore: 5.8, outcome: 'Not Qualified', rep: 'Sarah J.' },
  { id: '6', date: '2024-01-08', prospect: 'InnovateTech', duration: 38, spicedScore: 8.5, outcome: 'Meeting Scheduled', rep: 'Michael C.' },
  { id: '7', date: '2024-01-07', prospect: 'SmartBiz Ltd', duration: 25, spicedScore: 7.1, outcome: 'Follow-up', rep: 'Emily D.' },
  { id: '8', date: '2024-01-07', prospect: 'Enterprise Plus', duration: 52, spicedScore: 9.3, outcome: 'Closed Won', rep: 'David W.' },
]

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

  const handleExport = async (exportFormat: 'csv' | 'pdf') => {
    console.log('Exporting calls as', exportFormat)
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
          value="560"
          metric={{ value: 560, change: 48, changePercent: 9.4, trend: 'up' }}
          icon={<Phone className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Duration"
          value="27m"
          metric={{ value: 27, change: 3, changePercent: 12.5, trend: 'up' }}
          icon={<Clock className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg SPICED Score"
          value="7.5/10"
          metric={{ value: 7.5, change: 0.4, changePercent: 5.6, trend: 'up' }}
          icon={<Award className="w-6 h-6" />}
        />
        <MetricCard
          title="Answer Rate"
          value="94.2%"
          metric={{ value: 94.2, change: 1.3, changePercent: 1.4, trend: 'up' }}
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Call Volume Trend" description="Daily call volume over time">
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
        </ChartCard>

        <ChartCard title="Call Duration Trend" description="Average call duration in minutes">
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
        </ChartCard>
      </div>

      {/* Charts Row 2 - SPICED Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="SPICED Score Trend"
          description="Overall methodology scores over time"
          className="lg:col-span-2"
        >
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
        </ChartCard>

        <ChartCard title="Score Distribution" description="SPICED score ranges">
          <PieChart
            data={spicedDistribution}
            height={300}
            innerRadius={50}
            outerRadius={90}
          />
        </ChartCard>
      </div>

      {/* SPICED by Category */}
      <ChartCard title="SPICED by Category" description="Average scores per methodology component">
        <BarChart
          data={spicedByCategory}
          xAxisKey="category"
          bars={[{ dataKey: 'score', name: 'Score', color: '#0ea5e9' }]}
          yAxisFormatter={(value) => value.toFixed(1)}
          height={250}
          colorByValue
          colors={['#22c55e', '#0ea5e9', '#8b5cf6', '#f59e0b', '#06b6d4']}
        />
      </ChartCard>

      {/* Recent Calls Table */}
      <ChartCard title="Recent Calls" description="Detailed breakdown of recent call activity">
        <DataTable
          data={recentCalls}
          columns={callColumns}
          keyField="id"
          maxHeight="400px"
          stickyHeader
        />
      </ChartCard>
    </div>
  )
}
