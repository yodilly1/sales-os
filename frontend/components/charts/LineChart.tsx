'use client'

import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { cn } from '@/lib/utils/cn'

export interface LineChartLine {
  dataKey: string
  name: string
  color: string
  strokeWidth?: number
  dashed?: boolean
}

export interface LineChartProps<T> {
  data: T[]
  lines: LineChartLine[]
  xAxisKey: string
  xAxisFormatter?: (value: string) => string
  yAxisFormatter?: (value: number) => string
  tooltipFormatter?: (value: number, name: string) => string
  height?: number
  showGrid?: boolean
  showLegend?: boolean
  className?: string
}

export function LineChart<T extends Record<string, unknown>>({
  data,
  lines,
  xAxisKey,
  xAxisFormatter,
  yAxisFormatter,
  tooltipFormatter,
  height = 300,
  showGrid = true,
  showLegend = true,
  className,
}: LineChartProps<T>) {
  return (
    <div className={cn('w-full', className)}>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          )}
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
            labelFormatter={xAxisFormatter}
          />
          {showLegend && (
            <Legend
              wrapperStyle={{ paddingTop: 16 }}
              iconType="line"
            />
          )}
          {lines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={line.strokeWidth ?? 2}
              strokeDasharray={line.dashed ? '5 5' : undefined}
              dot={{ fill: line.color, strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  )
}
