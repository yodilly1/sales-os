'use client'

import { useState } from 'react'
import { FileText, Download, Share2, Eye, TrendingUp } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart, DataTable, Column } from '@/components/charts'
import { formatNumber, formatDate, formatRelativeTime } from '@/lib/utils/format'
import type { DateRange } from '@/lib/types/analytics'

// Mock data
const contentTrendData = [
  { date: '2024-01-01', generated: 12, downloaded: 8, shared: 4 },
  { date: '2024-01-02', generated: 15, downloaded: 10, shared: 6 },
  { date: '2024-01-03', generated: 18, downloaded: 14, shared: 8 },
  { date: '2024-01-04', generated: 14, downloaded: 9, shared: 5 },
  { date: '2024-01-05', generated: 20, downloaded: 16, shared: 10 },
  { date: '2024-01-06', generated: 11, downloaded: 7, shared: 3 },
  { date: '2024-01-07', generated: 16, downloaded: 12, shared: 7 },
  { date: '2024-01-08', generated: 22, downloaded: 18, shared: 11 },
  { date: '2024-01-09', generated: 19, downloaded: 15, shared: 9 },
  { date: '2024-01-10', generated: 25, downloaded: 20, shared: 13 },
]

const contentByType = [
  { type: 'Sales Deck', generated: 85, downloaded: 72, shared: 45 },
  { type: 'Proposal', generated: 62, downloaded: 58, shared: 32 },
  { type: 'One-Pager', generated: 94, downloaded: 76, shared: 54 },
  { type: 'Case Study', generated: 48, downloaded: 42, shared: 28 },
  { type: 'Email Template', generated: 120, downloaded: 95, shared: 65 },
  { type: 'Battle Card', generated: 35, downloaded: 30, shared: 18 },
]

const contentTypeDistribution = [
  { name: 'Sales Deck', value: 85, color: '#0ea5e9' },
  { name: 'Proposal', value: 62, color: '#22c55e' },
  { name: 'One-Pager', value: 94, color: '#f59e0b' },
  { name: 'Case Study', value: 48, color: '#8b5cf6' },
  { name: 'Email Template', value: 120, color: '#ec4899' },
  { name: 'Battle Card', value: 35, color: '#06b6d4' },
]

const engagementByType = [
  { type: 'Sales Deck', engagement: 78 },
  { type: 'Proposal', engagement: 85 },
  { type: 'One-Pager', engagement: 72 },
  { type: 'Case Study', engagement: 68 },
  { type: 'Email Template', engagement: 82 },
  { type: 'Battle Card', engagement: 65 },
]

interface ContentRecord {
  id: string
  title: string
  type: string
  generatedAt: string
  downloads: number
  shares: number
  views: number
  createdBy: string
}

const topContent: ContentRecord[] = [
  { id: '1', title: 'Q4 Enterprise Sales Deck', type: 'Sales Deck', generatedAt: '2024-01-10T14:30:00Z', downloads: 45, shares: 28, views: 156, createdBy: 'Sarah J.' },
  { id: '2', title: 'Acme Corp Custom Proposal', type: 'Proposal', generatedAt: '2024-01-09T10:15:00Z', downloads: 38, shares: 22, views: 124, createdBy: 'Michael C.' },
  { id: '3', title: 'Product Feature One-Pager', type: 'One-Pager', generatedAt: '2024-01-09T08:45:00Z', downloads: 52, shares: 35, views: 189, createdBy: 'Emily D.' },
  { id: '4', title: 'TechStart Success Story', type: 'Case Study', generatedAt: '2024-01-08T16:20:00Z', downloads: 31, shares: 19, views: 98, createdBy: 'David W.' },
  { id: '5', title: 'Competitor Comparison Template', type: 'Email Template', generatedAt: '2024-01-08T11:00:00Z', downloads: 67, shares: 42, views: 234, createdBy: 'Sarah J.' },
  { id: '6', title: 'Enterprise Battle Card', type: 'Battle Card', generatedAt: '2024-01-07T09:30:00Z', downloads: 28, shares: 15, views: 87, createdBy: 'Michael C.' },
  { id: '7', title: 'ROI Calculator Deck', type: 'Sales Deck', generatedAt: '2024-01-07T14:00:00Z', downloads: 41, shares: 26, views: 142, createdBy: 'Emily D.' },
  { id: '8', title: 'Implementation Guide', type: 'One-Pager', generatedAt: '2024-01-06T15:45:00Z', downloads: 35, shares: 21, views: 118, createdBy: 'David W.' },
]

const contentColumns: Column<ContentRecord>[] = [
  {
    key: 'title',
    header: 'Title',
    sortable: true,
    render: (value, row) => (
      <div>
        <p className="font-medium text-gray-900">{value as string}</p>
        <p className="text-xs text-gray-500">{row.type}</p>
      </div>
    ),
  },
  {
    key: 'createdBy',
    header: 'Created By',
    width: '100px',
  },
  {
    key: 'generatedAt',
    header: 'Generated',
    width: '120px',
    sortable: true,
    render: (value) => formatRelativeTime(value as string),
  },
  {
    key: 'views',
    header: 'Views',
    width: '80px',
    align: 'right',
    sortable: true,
    render: (value) => (
      <div className="flex items-center justify-end gap-1">
        <Eye className="w-3 h-3 text-gray-400" />
        {formatNumber(value as number)}
      </div>
    ),
  },
  {
    key: 'downloads',
    header: 'Downloads',
    width: '100px',
    align: 'right',
    sortable: true,
    render: (value) => (
      <div className="flex items-center justify-end gap-1">
        <Download className="w-3 h-3 text-gray-400" />
        {formatNumber(value as number)}
      </div>
    ),
  },
  {
    key: 'shares',
    header: 'Shares',
    width: '80px',
    align: 'right',
    sortable: true,
    render: (value) => (
      <div className="flex items-center justify-end gap-1">
        <Share2 className="w-3 h-3 text-gray-400" />
        {formatNumber(value as number)}
      </div>
    ),
  },
]

export default function ContentAnalyticsPage() {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd'),
  })

  const handleExport = async (exportFormat: 'csv' | 'pdf') => {
    console.log('Exporting content as', exportFormat)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Content Analytics</h2>
          <p className="mt-1 text-sm text-gray-500">
            Track content generation, downloads, and engagement metrics
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
          title="Total Generated"
          value="444"
          metric={{ value: 444, change: 52, changePercent: 13.3, trend: 'up' }}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          title="Total Downloads"
          value="373"
          metric={{ value: 373, change: 38, changePercent: 11.3, trend: 'up' }}
          icon={<Download className="w-6 h-6" />}
        />
        <MetricCard
          title="Total Shares"
          value="242"
          metric={{ value: 242, change: 28, changePercent: 13.1, trend: 'up' }}
          icon={<Share2 className="w-6 h-6" />}
        />
        <MetricCard
          title="Engagement Rate"
          value="68.4%"
          metric={{ value: 68.4, change: 4.2, changePercent: 6.5, trend: 'up' }}
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Content Activity Trend"
          description="Daily content metrics over time"
          className="lg:col-span-2"
        >
          <LineChart
            data={contentTrendData}
            xAxisKey="date"
            xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
            lines={[
              { dataKey: 'generated', name: 'Generated', color: '#0ea5e9' },
              { dataKey: 'downloaded', name: 'Downloaded', color: '#22c55e' },
              { dataKey: 'shared', name: 'Shared', color: '#f59e0b' },
            ]}
            height={300}
          />
        </ChartCard>

        <ChartCard title="Content Type Distribution" description="By total generated">
          <PieChart
            data={contentTypeDistribution}
            height={300}
            innerRadius={50}
            outerRadius={90}
          />
        </ChartCard>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Content by Type" description="Generation and engagement breakdown">
          <BarChart
            data={contentByType}
            xAxisKey="type"
            bars={[
              { dataKey: 'generated', name: 'Generated', color: '#0ea5e9' },
              { dataKey: 'downloaded', name: 'Downloaded', color: '#22c55e' },
              { dataKey: 'shared', name: 'Shared', color: '#f59e0b' },
            ]}
            height={300}
          />
        </ChartCard>

        <ChartCard title="Engagement Rate by Type" description="Percentage of content engaged with">
          <BarChart
            data={engagementByType}
            xAxisKey="type"
            layout="vertical"
            bars={[{ dataKey: 'engagement', name: 'Engagement %', color: '#0ea5e9' }]}
            yAxisFormatter={(value) => `${value}%`}
            height={300}
            colorByValue
            colors={['#0ea5e9', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']}
          />
        </ChartCard>
      </div>

      {/* Top Performing Content Table */}
      <ChartCard title="Top Performing Content" description="Content pieces with highest engagement">
        <DataTable
          data={topContent}
          columns={contentColumns}
          keyField="id"
          maxHeight="400px"
          stickyHeader
        />
      </ChartCard>
    </div>
  )
}
