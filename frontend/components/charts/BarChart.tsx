'use client'

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { cn } from '@/lib/utils/cn'

export interface BarChartBar {
  dataKey: string
  name: string
  color: string
  stackId?: string
}

export interface BarChartProps<T> {
  data: T[]
  bars: BarChartBar[]
  xAxisKey: string
  xAxisFormatter?: (value: string) => string
  yAxisFormatter?: (value: number) => string
  tooltipFormatter?: (value: number, name: string) => string
  height?: number
  showGrid?: boolean
  showLegend?: boolean
  layout?: 'horizontal' | 'vertical'
  barSize?: number
  className?: string
  colorByValue?: boolean
  colors?: string[]
}

const defaultColors = [
  '#0ea5e9',
  '#22c55e',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#f97316',
]

export function BarChart<T extends Record<string, unknown>>({
  data,
  bars,
  xAxisKey,
  xAxisFormatter,
  yAxisFormatter,
  tooltipFormatter,
  height = 300,
  showGrid = true,
  showLegend = true,
  layout = 'horizontal',
  barSize,
  className,
  colorByValue = false,
  colors = defaultColors,
}: BarChartProps<T>) {
  return (
    <div className={cn('w-full', className)}>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart
          data={data}
          layout={layout}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          barSize={barSize}
        >
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          )}
          {layout === 'horizontal' ? (
            <>
              <XAxis
                dataKey={xAxisKey}
                tickFormatter={xAxisFormatter}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
              />
              <YAxis
                tickFormatter={yAxisFormatter}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
              />
            </>
          ) : (
            <>
              <XAxis
                type="number"
                tickFormatter={yAxisFormatter}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
              />
              <YAxis
                type="category"
                dataKey={xAxisKey}
                tickFormatter={xAxisFormatter}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                axisLine={{ stroke: '#e5e7eb' }}
                tickLine={{ stroke: '#e5e7eb' }}
                width={100}
              />
            </>
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
            formatter={(value: number, name: string) =>
              tooltipFormatter ? [tooltipFormatter(value, name), name] : [value, name]
            }
          />
          {showLegend && bars.length > 1 && (
            <Legend wrapperStyle={{ paddingTop: 16 }} />
          )}
          {bars.map((bar) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.name}
              fill={bar.color}
              stackId={bar.stackId}
              radius={[4, 4, 0, 0]}
            >
              {colorByValue &&
                data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
            </Bar>
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  )
}
