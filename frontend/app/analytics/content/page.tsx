'use client'

import { useState, useEffect } from 'react'
import { FileText, Download, Share2, Eye, TrendingUp, Loader2, AlertCircle } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart, DataTable, Column } from '@/components/charts'
import { formatNumber, formatRelativeTime } from '@/lib/utils/format'
import type { DateRange, MetricValue, ContentTypeData, ContentTrendData, ContentPerformance } from '@/lib/types/analytics'

interface ContentMetricsData {
  totalGenerated: MetricValue
  totalDownloaded: MetricValue
  totalShared: MetricValue
  engagementRate: MetricValue
}

interface ContentTypeDistribution {
  name: string
  value: number
  color: string
}

interface EngagementByType {
  type: string
  engagement: number
}

const defaultMetrics: ContentMetricsData = {
  totalGenerated: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  totalDownloaded: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  totalShared: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  engagementRate: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
}

const contentColumns: Column<ContentPerformance>[] = [
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
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<ContentMetricsData>(defaultMetrics)
  const [trendData, setTrendData] = useState<ContentTrendData[]>([])
  const [contentByType, setContentByType] = useState<ContentTypeData[]>([])
  const [typeDistribution, setTypeDistribution] = useState<ContentTypeDistribution[]>([])
  const [engagementByType, setEngagementByType] = useState<EngagementByType[]>([])
  const [topContent, setTopContent] = useState<ContentPerformance[]>([])

  useEffect(() => {
    loadContentData()
  }, [dateRange])

  const loadContentData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
      })

      // Fetch all content data in parallel
      const [metricsRes, trendsRes, byTypeRes, topRes] = await Promise.all([
        fetch(`/api/v1/analytics/content/metrics?${params}`),
        fetch(`/api/v1/analytics/content/trends?${params}`),
        fetch(`/api/v1/analytics/content/by-type?${params}`),
        fetch(`/api/v1/analytics/content/top?${params}&page=1&pageSize=10`),
      ])

      // Process metrics
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics({
          totalGenerated: data.data?.total_generated || data.data?.totalGenerated || defaultMetrics.totalGenerated,
          totalDownloaded: data.data?.total_downloaded || data.data?.totalDownloaded || defaultMetrics.totalDownloaded,
          totalShared: data.data?.total_shared || data.data?.totalShared || defaultMetrics.totalShared,
          engagementRate: data.data?.engagement_rate || data.data?.engagementRate || defaultMetrics.engagementRate,
        })
      }

      // Process trends
      if (trendsRes.ok) {
        const data = await trendsRes.json()
        if (Array.isArray(data.data)) {
          setTrendData(data.data)
        }
      }

      // Process by type
      if (byTypeRes.ok) {
        const data = await byTypeRes.json()
        if (Array.isArray(data.data)) {
          setContentByType(data.data)

          // Calculate type distribution
          const colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']
          setTypeDistribution(data.data.map((d: ContentTypeData, i: number) => ({
            name: d.type,
            value: d.generated,
            color: colors[i % colors.length],
          })))

          // Calculate engagement by type
          setEngagementByType(data.data.map((d: ContentTypeData) => ({
            type: d.type,
            engagement: d.generated > 0 ? Math.round(((d.downloaded + d.shared) / d.generated) * 100) : 0,
          })))
        }
      }

      // Process top content
      if (topRes.ok) {
        const data = await topRes.json()
        if (Array.isArray(data.data)) {
          setTopContent(data.data.map((d: { id: string; title: string; type: string; generated_at?: string; generatedAt?: string; downloads: number; shares: number; views: number }) => ({
            id: d.id,
            title: d.title,
            type: d.type,
            generatedAt: d.generated_at || d.generatedAt || new Date().toISOString(),
            downloads: d.downloads,
            shares: d.shares,
            views: d.views,
          })))
        }
      }

    } catch (err) {
      console.error('Failed to load content analytics:', err)
      setError('Failed to load content analytics data. Please try again.')
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
      window.open(`/api/v1/analytics/content/export?${params}`, '_blank')
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-neutral-600">Loading content analytics...</p>
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
            onClick={loadContentData}
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
          value={metrics.totalGenerated.value.toLocaleString()}
          metric={metrics.totalGenerated}
          icon={<FileText className="w-6 h-6" />}
        />
        <MetricCard
          title="Total Downloads"
          value={metrics.totalDownloaded.value.toLocaleString()}
          metric={metrics.totalDownloaded}
          icon={<Download className="w-6 h-6" />}
        />
        <MetricCard
          title="Total Shares"
          value={metrics.totalShared.value.toLocaleString()}
          metric={metrics.totalShared}
          icon={<Share2 className="w-6 h-6" />}
        />
        <MetricCard
          title="Engagement Rate"
          value={`${metrics.engagementRate.value.toFixed(1)}%`}
          metric={metrics.engagementRate}
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
          {trendData.length > 0 ? (
            <LineChart
              data={trendData}
              xAxisKey="date"
              xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
              lines={[
                { dataKey: 'generated', name: 'Generated', color: '#0ea5e9' },
                { dataKey: 'downloaded', name: 'Downloaded', color: '#22c55e' },
                { dataKey: 'shared', name: 'Shared', color: '#f59e0b' },
              ]}
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No trend data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Content Type Distribution" description="By total generated">
          {typeDistribution.length > 0 ? (
            <PieChart
              data={typeDistribution}
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

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Content by Type" description="Generation and engagement breakdown">
          {contentByType.length > 0 ? (
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
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No type data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Engagement Rate by Type" description="Percentage of content engaged with">
          {engagementByType.length > 0 ? (
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
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No engagement data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* Top Performing Content Table */}
      <ChartCard title="Top Performing Content" description="Content pieces with highest engagement">
        {topContent.length > 0 ? (
          <DataTable
            data={topContent}
            columns={contentColumns}
            keyField="id"
            maxHeight="400px"
            stickyHeader
          />
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            No content to display. Generate content to see performance data here.
          </div>
        )}
      </ChartCard>
    </div>
  )
}
