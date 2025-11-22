'use client'

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { cn } from '@/lib/utils/cn'

export interface PieChartDataItem {
  name: string
  value: number
  color?: string
}

export interface PieChartProps {
  data: PieChartDataItem[]
  height?: number
  innerRadius?: number
  outerRadius?: number
  showLegend?: boolean
  showLabels?: boolean
  valueFormatter?: (value: number) => string
  className?: string
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
  '#84cc16',
  '#14b8a6',
]

const RADIAN = Math.PI / 180

interface LabelProps {
  cx: number
  cy: number
  midAngle: number
  innerRadius: number
  outerRadius: number
  percent: number
}

const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}: LabelProps) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)

  if (percent < 0.05) return null

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="text-xs font-medium"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

export function PieChart({
  data,
  height = 300,
  innerRadius = 0,
  outerRadius = 100,
  showLegend = true,
  showLabels = true,
  valueFormatter,
  className,
}: PieChartProps) {
  return (
    <div className={cn('w-full', className)}>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={showLabels ? renderCustomizedLabel : undefined}
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="value"
            paddingAngle={2}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || defaultColors[index % defaultColors.length]}
                stroke="#ffffff"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
            formatter={(value: number) => [
              valueFormatter ? valueFormatter(value) : value,
              'Value',
            ]}
          />
          {showLegend && (
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              wrapperStyle={{ paddingTop: 16 }}
            />
          )}
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  )
}
