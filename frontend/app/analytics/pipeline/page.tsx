'use client'

import { useState, useEffect } from 'react'
import { Users, TrendingUp, DollarSign, Target, ArrowRight, Loader2, AlertCircle } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart, DataTable, Column } from '@/components/charts'
import { formatCurrency } from '@/lib/utils/format'
import type { DateRange, MetricValue, PipelineStageData, EnrichmentTrendData, ProspectSource } from '@/lib/types/analytics'

interface PipelineMetricsData {
  prospectsEnriched: MetricValue
  conversionRate: MetricValue
  avgDealSize: MetricValue
  pipelineValue: MetricValue
}

interface SourceDistribution {
  name: string
  value: number
  color: string
}

interface StageConversion {
  stage: string
  rate: number
}

interface ProspectRecord {
  id: string
  company: string
  stage: string
  value: number
  source: string
  enrichedAt: string
  daysinStage: number
  probability: number
}

const defaultMetrics: PipelineMetricsData = {
  prospectsEnriched: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  conversionRate: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  avgDealSize: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
  pipelineValue: { value: 0, change: 0, changePercent: 0, trend: 'stable' },
}

const prospectColumns: Column<ProspectRecord>[] = [
  {
    key: 'company',
    header: 'Company',
    sortable: true,
    render: (value) => <span className="font-medium text-gray-900">{value as string}</span>,
  },
  {
    key: 'stage',
    header: 'Stage',
    width: '120px',
    render: (value) => {
      const stage = value as string
      const colors: Record<string, string> = {
        'Lead': 'bg-gray-100 text-gray-700',
        'Qualified': 'bg-primary-50 text-primary-700',
        'Meeting': 'bg-primary-100 text-primary-700',
        'Proposal': 'bg-warning-50 text-warning-700',
        'Negotiation': 'bg-success-50 text-success-700',
        'Closed Won': 'bg-success-100 text-success-800',
      }
      return (
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[stage] || 'bg-gray-100 text-gray-600'}`}>
          {stage}
        </span>
      )
    },
  },
  {
    key: 'value',
    header: 'Value',
    width: '100px',
    align: 'right',
    sortable: true,
    render: (value) => formatCurrency(value as number),
  },
  {
    key: 'source',
    header: 'Source',
    width: '90px',
  },
  {
    key: 'daysinStage',
    header: 'Days in Stage',
    width: '110px',
    align: 'right',
    sortable: true,
    render: (value) => {
      const days = value as number
      const color = days > 10 ? 'text-danger-600' : days > 5 ? 'text-warning-600' : 'text-gray-600'
      return <span className={color}>{days} days</span>
    },
  },
  {
    key: 'probability',
    header: 'Probability',
    width: '100px',
    align: 'right',
    sortable: true,
    render: (value) => {
      const prob = value as number
      const color = prob >= 75 ? 'text-success-600' : prob >= 50 ? 'text-warning-600' : 'text-gray-600'
      return <span className={`font-medium ${color}`}>{prob}%</span>
    },
  },
]

export default function PipelineAnalyticsPage() {
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd'),
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<PipelineMetricsData>(defaultMetrics)
  const [pipelineStages, setPipelineStages] = useState<PipelineStageData[]>([])
  const [enrichmentTrend, setEnrichmentTrend] = useState<EnrichmentTrendData[]>([])
  const [sourceDistribution, setSourceDistribution] = useState<SourceDistribution[]>([])
  const [stageConversions, setStageConversions] = useState<StageConversion[]>([])
  const [sourcePerformance, setSourcePerformance] = useState<ProspectSource[]>([])
  const [recentProspects, setRecentProspects] = useState<ProspectRecord[]>([])

  useEffect(() => {
    loadPipelineData()
  }, [dateRange])

  const loadPipelineData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
      })

      // Fetch all pipeline data in parallel
      const [metricsRes, stagesRes, trendsRes, sourcesRes] = await Promise.all([
        fetch(`/api/v1/analytics/pipeline/metrics?${params}`),
        fetch(`/api/v1/analytics/pipeline/stages?${params}`),
        fetch(`/api/v1/analytics/pipeline/enrichment-trends?${params}`),
        fetch(`/api/v1/analytics/pipeline/sources?${params}`),
      ])

      // Process metrics
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics({
          prospectsEnriched: data.data?.prospects_enriched || data.data?.prospectsEnriched || defaultMetrics.prospectsEnriched,
          conversionRate: data.data?.conversion_rate || data.data?.conversionRate || defaultMetrics.conversionRate,
          avgDealSize: data.data?.avg_deal_size || data.data?.avgDealSize || defaultMetrics.avgDealSize,
          pipelineValue: data.data?.pipeline_value || data.data?.pipelineValue || defaultMetrics.pipelineValue,
        })
      }

      // Process stages
      if (stagesRes.ok) {
        const data = await stagesRes.json()
        if (Array.isArray(data.data)) {
          setPipelineStages(data.data.map((d: { stage: string; count: number; value: number; conversion_rate?: number; conversionRate?: number }) => ({
            stage: d.stage,
            count: d.count,
            value: d.value,
            conversionRate: d.conversion_rate || d.conversionRate || 0,
          })))

          // Calculate stage conversions
          const conversions: StageConversion[] = []
          for (let i = 1; i < data.data.length; i++) {
            const prevStage = data.data[i - 1].stage
            const currStage = data.data[i].stage
            const rate = data.data[i].conversion_rate || data.data[i].conversionRate || 0
            conversions.push({
              stage: `${prevStage} → ${currStage}`,
              rate: rate,
            })
          }
          setStageConversions(conversions)
        }
      }

      // Process enrichment trends
      if (trendsRes.ok) {
        const data = await trendsRes.json()
        if (Array.isArray(data.data)) {
          setEnrichmentTrend(data.data)
        }
      }

      // Process sources
      if (sourcesRes.ok) {
        const data = await sourcesRes.json()
        if (Array.isArray(data.data)) {
          setSourcePerformance(data.data.map((d: { source: string; count: number; conversion_rate?: number; conversionRate?: number; avg_deal_size?: number; avgDealSize?: number }) => ({
            source: d.source,
            count: d.count,
            conversionRate: d.conversion_rate || d.conversionRate || 0,
            avgDealSize: d.avg_deal_size || d.avgDealSize || 0,
          })))

          // Create source distribution
          const colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']
          const total = data.data.reduce((sum: number, d: { count: number }) => sum + d.count, 0)
          setSourceDistribution(data.data.map((d: { source: string; count: number }, i: number) => ({
            name: d.source,
            value: total > 0 ? Math.round((d.count / total) * 100) : 0,
            color: colors[i % colors.length],
          })))
        }
      }

      // For recent prospects, we'd need a separate endpoint - show empty for now
      setRecentProspects([])

    } catch (err) {
      console.error('Failed to load pipeline analytics:', err)
      setError('Failed to load pipeline analytics data. Please try again.')
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
      window.open(`/api/v1/analytics/pipeline/export?${params}`, '_blank')
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-neutral-600">Loading pipeline analytics...</p>
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
            onClick={loadPipelineData}
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
          <h2 className="text-2xl font-bold text-gray-900">Pipeline Analytics</h2>
          <p className="mt-1 text-sm text-gray-500">
            Track prospect enrichment, conversions, and pipeline health
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
          title="Prospects Enriched"
          value={metrics.prospectsEnriched.value.toLocaleString()}
          metric={metrics.prospectsEnriched}
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          title="Conversion Rate"
          value={`${metrics.conversionRate.value.toFixed(1)}%`}
          metric={metrics.conversionRate}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Deal Size"
          value={formatCurrency(metrics.avgDealSize.value)}
          metric={metrics.avgDealSize}
          icon={<DollarSign className="w-6 h-6" />}
        />
        <MetricCard
          title="Pipeline Value"
          value={formatCurrency(metrics.pipelineValue.value)}
          metric={metrics.pipelineValue}
          icon={<Target className="w-6 h-6" />}
        />
      </div>

      {/* Pipeline Funnel */}
      <ChartCard title="Pipeline Funnel" description="Prospects by stage with value and conversion rates">
        {pipelineStages.length > 0 ? (
          <div className="flex items-center justify-between gap-2 overflow-x-auto pb-4">
            {pipelineStages.map((stage, index) => (
              <div key={stage.stage} className="flex items-center">
                <div
                  className="flex-shrink-0 text-center p-4 bg-gradient-to-b from-primary-50 to-primary-100 rounded-lg min-w-[140px]"
                  style={{ opacity: 1 - (index * 0.1) }}
                >
                  <p className="text-sm font-medium text-gray-600">{stage.stage}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stage.count}</p>
                  <p className="text-sm text-gray-500">{formatCurrency(stage.value)}</p>
                  {index > 0 && (
                    <p className="text-xs text-primary-600 mt-1">{stage.conversionRate.toFixed(1)}% conv.</p>
                  )}
                </div>
                {index < pipelineStages.length - 1 && (
                  <ArrowRight className="w-5 h-5 text-gray-300 mx-2 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-[150px] text-gray-500">
            No pipeline data available
          </div>
        )}
      </ChartCard>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Enrichment & Conversion Trend"
          description="Daily prospects enriched and converted"
          className="lg:col-span-2"
        >
          {enrichmentTrend.length > 0 ? (
            <LineChart
              data={enrichmentTrend}
              xAxisKey="date"
              xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
              lines={[
                { dataKey: 'enriched', name: 'Enriched', color: '#0ea5e9' },
                { dataKey: 'converted', name: 'Converted', color: '#22c55e' },
              ]}
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No trend data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Prospect Sources" description="Distribution by lead source">
          {sourceDistribution.length > 0 ? (
            <PieChart
              data={sourceDistribution}
              height={300}
              innerRadius={50}
              outerRadius={90}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              No source data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Stage Conversion Rates" description="Conversion rate between stages">
          {stageConversions.length > 0 ? (
            <BarChart
              data={stageConversions}
              xAxisKey="stage"
              layout="vertical"
              bars={[{ dataKey: 'rate', name: 'Conversion Rate', color: '#0ea5e9' }]}
              yAxisFormatter={(value) => `${value}%`}
              height={280}
            />
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-500">
              No conversion data available
            </div>
          )}
        </ChartCard>

        <ChartCard title="Source Performance" description="Conversion and deal size by source">
          {sourcePerformance.length > 0 ? (
            <BarChart
              data={sourcePerformance}
              xAxisKey="source"
              bars={[
                { dataKey: 'conversionRate', name: 'Conversion %', color: '#0ea5e9' },
              ]}
              yAxisFormatter={(value) => `${value}%`}
              height={280}
              colorByValue
              colors={['#0ea5e9', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']}
            />
          ) : (
            <div className="flex items-center justify-center h-[280px] text-gray-500">
              No source performance data available
            </div>
          )}
        </ChartCard>
      </div>

      {/* Recent Prospects Table */}
      <ChartCard title="Active Prospects" description="Recently enriched prospects in pipeline">
        {recentProspects.length > 0 ? (
          <DataTable
            data={recentProspects}
            columns={prospectColumns}
            keyField="id"
            maxHeight="400px"
            stickyHeader
          />
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-500">
            No active prospects to display. Enrich prospects to see them here.
          </div>
        )}
      </ChartCard>
    </div>
  )
}
