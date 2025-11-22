'use client'

import { useState } from 'react'
import { Users, TrendingUp, DollarSign, Target, ArrowRight } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { MetricCard, DateRangePicker, ChartCard, ExportButton } from '@/components/analytics'
import { LineChart, BarChart, PieChart, DataTable, Column } from '@/components/charts'
import { formatCurrency, formatPercent, formatNumber, formatDate } from '@/lib/utils/format'
import type { DateRange } from '@/lib/types/analytics'

// Mock data
const enrichmentTrendData = [
  { date: '2024-01-01', enriched: 25, converted: 8, value: 45000 },
  { date: '2024-01-02', enriched: 32, converted: 10, value: 62000 },
  { date: '2024-01-03', enriched: 28, converted: 9, value: 54000 },
  { date: '2024-01-04', enriched: 35, converted: 12, value: 78000 },
  { date: '2024-01-05', enriched: 42, converted: 15, value: 95000 },
  { date: '2024-01-06', enriched: 30, converted: 11, value: 68000 },
  { date: '2024-01-07', enriched: 38, converted: 14, value: 88000 },
  { date: '2024-01-08', enriched: 45, converted: 16, value: 102000 },
  { date: '2024-01-09', enriched: 40, converted: 13, value: 82000 },
  { date: '2024-01-10', enriched: 48, converted: 18, value: 115000 },
]

const pipelineStageData = [
  { stage: 'Lead', count: 245, value: 2450000, conversionRate: 100 },
  { stage: 'Qualified', count: 156, value: 1560000, conversionRate: 63.7 },
  { stage: 'Meeting', count: 98, value: 980000, conversionRate: 62.8 },
  { stage: 'Proposal', count: 64, value: 640000, conversionRate: 65.3 },
  { stage: 'Negotiation', count: 42, value: 420000, conversionRate: 65.6 },
  { stage: 'Closed Won', count: 28, value: 280000, conversionRate: 66.7 },
]

const stageConversionData = [
  { stage: 'Lead → Qualified', rate: 63.7 },
  { stage: 'Qualified → Meeting', rate: 62.8 },
  { stage: 'Meeting → Proposal', rate: 65.3 },
  { stage: 'Proposal → Negotiation', rate: 65.6 },
  { stage: 'Negotiation → Won', rate: 66.7 },
]

const prospectSourceData = [
  { name: 'Inbound', value: 35, color: '#0ea5e9' },
  { name: 'Outbound', value: 28, color: '#22c55e' },
  { name: 'Referral', value: 18, color: '#f59e0b' },
  { name: 'Event', value: 12, color: '#8b5cf6' },
  { name: 'Partner', value: 7, color: '#ec4899' },
]

const sourcePerformance = [
  { source: 'Inbound', count: 312, conversionRate: 28.5, avgDealSize: 42000 },
  { source: 'Outbound', count: 248, conversionRate: 22.3, avgDealSize: 38000 },
  { source: 'Referral', count: 156, conversionRate: 35.2, avgDealSize: 52000 },
  { source: 'Event', count: 108, conversionRate: 18.5, avgDealSize: 35000 },
  { source: 'Partner', count: 68, conversionRate: 32.4, avgDealSize: 48000 },
]

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

const recentProspects: ProspectRecord[] = [
  { id: '1', company: 'Acme Corporation', stage: 'Proposal', value: 85000, source: 'Inbound', enrichedAt: '2024-01-10', daysinStage: 5, probability: 75 },
  { id: '2', company: 'TechStart Inc', stage: 'Meeting', value: 42000, source: 'Outbound', enrichedAt: '2024-01-09', daysinStage: 8, probability: 45 },
  { id: '3', company: 'Global Solutions', stage: 'Negotiation', value: 125000, source: 'Referral', enrichedAt: '2024-01-09', daysinStage: 3, probability: 85 },
  { id: '4', company: 'DataFlow Systems', stage: 'Qualified', value: 38000, source: 'Event', enrichedAt: '2024-01-08', daysinStage: 12, probability: 30 },
  { id: '5', company: 'CloudNet Pro', stage: 'Proposal', value: 67000, source: 'Partner', enrichedAt: '2024-01-08', daysinStage: 6, probability: 65 },
  { id: '6', company: 'InnovateTech', stage: 'Meeting', value: 55000, source: 'Inbound', enrichedAt: '2024-01-07', daysinStage: 10, probability: 50 },
  { id: '7', company: 'SmartBiz Ltd', stage: 'Negotiation', value: 92000, source: 'Outbound', enrichedAt: '2024-01-07', daysinStage: 4, probability: 80 },
  { id: '8', company: 'Enterprise Plus', stage: 'Closed Won', value: 145000, source: 'Referral', enrichedAt: '2024-01-06', daysinStage: 0, probability: 100 },
]

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

  const handleExport = async (exportFormat: 'csv' | 'pdf') => {
    console.log('Exporting pipeline as', exportFormat)
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
          value="363"
          metric={{ value: 363, change: 42, changePercent: 13.1, trend: 'up' }}
          icon={<Users className="w-6 h-6" />}
        />
        <MetricCard
          title="Conversion Rate"
          value="24.5%"
          metric={{ value: 24.5, change: 2.3, changePercent: 10.4, trend: 'up' }}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          title="Avg Deal Size"
          value="$42.5K"
          metric={{ value: 42500, change: 3200, changePercent: 8.1, trend: 'up' }}
          icon={<DollarSign className="w-6 h-6" />}
        />
        <MetricCard
          title="Pipeline Value"
          value="$2.4M"
          metric={{ value: 2400000, change: 280000, changePercent: 13.2, trend: 'up' }}
          icon={<Target className="w-6 h-6" />}
        />
      </div>

      {/* Pipeline Funnel */}
      <ChartCard title="Pipeline Funnel" description="Prospects by stage with value and conversion rates">
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-4">
          {pipelineStageData.map((stage, index) => (
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
              {index < pipelineStageData.length - 1 && (
                <ArrowRight className="w-5 h-5 text-gray-300 mx-2 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </ChartCard>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Enrichment & Conversion Trend"
          description="Daily prospects enriched and converted"
          className="lg:col-span-2"
        >
          <LineChart
            data={enrichmentTrendData}
            xAxisKey="date"
            xAxisFormatter={(value) => format(new Date(value), 'MMM d')}
            lines={[
              { dataKey: 'enriched', name: 'Enriched', color: '#0ea5e9' },
              { dataKey: 'converted', name: 'Converted', color: '#22c55e' },
            ]}
            height={300}
          />
        </ChartCard>

        <ChartCard title="Prospect Sources" description="Distribution by lead source">
          <PieChart
            data={prospectSourceData}
            height={300}
            innerRadius={50}
            outerRadius={90}
          />
        </ChartCard>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Stage Conversion Rates" description="Conversion rate between stages">
          <BarChart
            data={stageConversionData}
            xAxisKey="stage"
            layout="vertical"
            bars={[{ dataKey: 'rate', name: 'Conversion Rate', color: '#0ea5e9' }]}
            yAxisFormatter={(value) => `${value}%`}
            height={280}
          />
        </ChartCard>

        <ChartCard title="Source Performance" description="Conversion and deal size by source">
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
        </ChartCard>
      </div>

      {/* Recent Prospects Table */}
      <ChartCard title="Active Prospects" description="Recently enriched prospects in pipeline">
        <DataTable
          data={recentProspects}
          columns={prospectColumns}
          keyField="id"
          maxHeight="400px"
          stickyHeader
        />
      </ChartCard>
    </div>
  )
}
