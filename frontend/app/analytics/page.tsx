'use client'

import { useState } from 'react'
import { Phone, FileText, Users, DollarSign, TrendingUp, Activity } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart } from '@/components/charts'
import type { DateRange } from '@/lib/types/analytics'

// Mock data for demonstration
const overviewTrendData = [
  { date: '2024-01-01', calls: 45, content: 12, deals: 3 },
  { date: '2024-01-02', calls: 52, content: 15, deals: 4 },
  { date: '2024-01-03', calls: 48, content: 18, deals: 2 },
  { date: '2024-01-04', calls: 61, content: 14, deals: 5 },
  { date: '2024-01-05', calls: 55, content: 20, deals: 3 },
  { date: '2024-01-06', calls: 43, content: 11, deals: 4 },
  { date: '2024-01-07', calls: 58, content: 16, deals: 6 },
]

const activityDistribution = [
  { name: 'Calls', value: 45, color: '#0ea5e9' },
  { name: 'Content', value: 30, color: '#22c55e' },
  { name: 'Enrichment', value: 15, color: '#f59e0b' },
  { name: 'Coaching', value: 10, color: '#8b5cf6' },
]

const topPerformers = [
  { name: 'Sarah Johnson', calls: 125, deals: 8, value: 45000 },
  { name: 'Michael Chen', calls: 118, deals: 7, value: 42000 },
  { name: 'Emily Davis', calls: 105, deals: 6, value: 38000 },
  { name: 'David Wilson', calls: 98, deals: 5, value: 35000 },
]

export default function AnalyticsOverviewPage() {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd'),
  })

  const handleExport = async (exportFormat: 'csv' | 'pdf') => {
    console.log('Exporting overview as', exportFormat)
    // TODO: Implement actual export
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
          value="1,247"
          metric={{ value: 1247, change: 125, changePercent: 11.2, trend: 'up' }}
          icon={<Phone className="w-6 h-6" />}
        />
        <MetricCard
          title="Content Generated"
          value="384"
          metric={{ value: 384, change: 42, changePercent: 12.3, trend: 'up' }}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          title="Prospects Enriched"
          value="892"
          metric={{ value: 892, change: -23, changePercent: -2.5, trend: 'down' }}
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          title="Pipeline Value"
          value="$2.4M"
          metric={{ value: 2400000, change: 280000, changePercent: 13.2, trend: 'up' }}
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
          <LineChart
            data={overviewTrendData}
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

        <ChartCard title="Activity Distribution" description="Breakdown by category">
          <PieChart
            data={activityDistribution}
            height={300}
            innerRadius={60}
            outerRadius={100}
          />
        </ChartCard>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Top Performers" description="By deal value this period">
          <BarChart
            data={topPerformers}
            xAxisKey="name"
            layout="vertical"
            bars={[{ dataKey: 'value', name: 'Deal Value', color: '#0ea5e9' }]}
            yAxisFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            height={280}
          />
        </ChartCard>

        <ChartCard title="Quick Stats" description="Performance highlights">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">Avg SPICED Score</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">7.8/10</p>
              <p className="text-sm text-success-600">+0.4 vs last period</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Activity className="w-4 h-4" />
                <span className="text-sm">Conversion Rate</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">24.5%</p>
              <p className="text-sm text-success-600">+2.1% vs last period</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <Phone className="w-4 h-4" />
                <span className="text-sm">Avg Call Duration</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">28m</p>
              <p className="text-sm text-gray-500">No change</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-gray-600 mb-2">
                <FileText className="w-4 h-4" />
                <span className="text-sm">Content Engagement</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">68%</p>
              <p className="text-sm text-success-600">+5% vs last period</p>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
