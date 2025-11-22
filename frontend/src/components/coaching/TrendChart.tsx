'use client';

import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { TrendDataPoint } from '@/types/coaching';

interface TrendChartProps {
  data: TrendDataPoint[];
  height?: number;
  showLegend?: boolean;
  className?: string;
}

const SPICED_COLORS = {
  situation: '#3b82f6',    // blue
  pain: '#ef4444',         // red
  impact: '#10b981',       // emerald
  criticalEvent: '#f59e0b', // amber
  decision: '#8b5cf6',     // violet
  overall: '#1f2937',      // gray-800
};

const SPICED_LABELS = {
  situation: 'Situation',
  pain: 'Pain',
  impact: 'Impact',
  criticalEvent: 'Critical Event',
  decision: 'Decision',
  overall: 'Overall',
};

type MetricKey = keyof typeof SPICED_COLORS;

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function formatDateForDisplay(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="font-medium text-gray-900 mb-2">{label && formatDateForDisplay(label)}</p>
        <div className="space-y-1">
          {payload.map((entry) => (
            <div key={entry.name} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600">
                  {SPICED_LABELS[entry.name as MetricKey]}
                </span>
              </div>
              <span className="text-sm font-semibold">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
}

export function TrendChart({ data, height = 300, showLegend = true, className = '' }: TrendChartProps) {
  const [activeMetrics, setActiveMetrics] = useState<Set<MetricKey>>(
    new Set(['overall', 'situation', 'pain'])
  );

  const toggleMetric = (metric: MetricKey) => {
    setActiveMetrics(prev => {
      const next = new Set(prev);
      if (next.has(metric)) {
        if (next.size > 1) {
          next.delete(metric);
        }
      } else {
        next.add(metric);
      }
      return next;
    });
  };

  return (
    <div className={className}>
      {showLegend && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(Object.keys(SPICED_COLORS) as MetricKey[]).map((metric) => (
            <button
              key={metric}
              onClick={() => toggleMetric(metric)}
              className={`px-3 py-1 text-sm rounded-full border transition-all ${
                activeMetrics.has(metric)
                  ? 'border-transparent text-white'
                  : 'border-gray-300 text-gray-500 bg-white hover:bg-gray-50'
              }`}
              style={{
                backgroundColor: activeMetrics.has(metric) ? SPICED_COLORS[metric] : undefined,
              }}
            >
              {SPICED_LABELS[metric]}
            </button>
          ))}
        </div>
      )}

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDateForDisplay}
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              tickCount={5}
            />
            <Tooltip content={<CustomTooltip />} />

            {(Object.keys(SPICED_COLORS) as MetricKey[]).map((metric) => (
              activeMetrics.has(metric) && (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  stroke={SPICED_COLORS[metric]}
                  strokeWidth={metric === 'overall' ? 3 : 2}
                  dot={{ r: 4, fill: SPICED_COLORS[metric] }}
                  activeDot={{ r: 6, fill: SPICED_COLORS[metric] }}
                />
              )
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex items-center justify-center gap-4 text-sm text-gray-500">
        <span>Click legend items to show/hide metrics</span>
      </div>
    </div>
  );
}

export default TrendChart;
