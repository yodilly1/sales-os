'use client';

import { useState, useEffect } from 'react';
import { getBestPerformers, getPerformanceMetrics, getTrends } from '@/lib/api/talktracks';
import type { TalkTrackLibraryItem, ScriptPerformanceMetrics } from '@/lib/api/talktracks';

export function TalkTrackPerformance() {
  const [bestPerformers, setBestPerformers] = useState<TalkTrackLibraryItem[]>([]);
  const [selectedMetrics, setSelectedMetrics] = useState<ScriptPerformanceMetrics | null>(null);
  const [trends, setTrends] = useState<Array<{
    period_start: string;
    period_end: string;
    total_uses: number;
    meetings_scheduled_rate: number;
    deal_advancement_rate: number;
  }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const [filterType, setFilterType] = useState('');

  useEffect(() => {
    loadBestPerformers();
  }, [filterType]);

  const loadBestPerformers = async () => {
    setIsLoading(true);
    try {
      const data = await getBestPerformers({
        script_type: filterType || undefined,
        limit: 10,
      });
      setBestPerformers(data);

      if (data.length > 0) {
        loadMetricsForTrack(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load best performers:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMetricsForTrack = async (talkTrackId: string) => {
    try {
      const [metrics, trendData] = await Promise.all([
        getPerformanceMetrics(talkTrackId, timeRange),
        getTrends(talkTrackId, 90, 7),
      ]);
      setSelectedMetrics(metrics);
      setTrends(trendData.data_points || []);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    }
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  const renderMetricCard = (
    label: string,
    value: string | number,
    subtext?: string,
    color: string = 'blue'
  ) => (
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className={`mt-2 text-3xl font-semibold text-${color}-600`}>{value}</p>
      {subtext && <p className="mt-1 text-sm text-gray-500">{subtext}</p>}
    </div>
  );

  const renderTrendChart = () => {
    if (trends.length === 0) return null;

    const maxUses = Math.max(...trends.map((t) => t.total_uses), 1);

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Usage Trends</h3>
        <div className="h-40 flex items-end gap-2">
          {trends.map((point, i) => (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div
                className="w-full bg-blue-500 rounded-t transition-all"
                style={{ height: `${(point.total_uses / maxUses) * 100}%`, minHeight: '4px' }}
                title={`${point.total_uses} uses`}
              />
              <span className="text-xs text-gray-400 mt-1 truncate max-w-full">
                {new Date(point.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-4 flex justify-between text-xs text-gray-500">
          <span>Uses over time</span>
          <span>Last 90 days</span>
        </div>
      </div>
    );
  };

  const renderLeaderboard = () => (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Top Performers</h3>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-sm rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="discovery_call">Discovery</option>
            <option value="demo_script">Demo</option>
            <option value="objection_response">Objection</option>
            <option value="closing_conversation">Closing</option>
            <option value="follow_up_guide">Follow-Up</option>
          </select>
        </div>
      </div>

      <ul className="divide-y divide-gray-200">
        {bestPerformers.map((item, index) => (
          <li
            key={item.id}
            className="p-4 hover:bg-gray-50 cursor-pointer"
            onClick={() => loadMetricsForTrack(item.id)}
          >
            <div className="flex items-center gap-4">
              <span
                className={`
                  flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium
                  ${index === 0 ? 'bg-yellow-100 text-yellow-800' : ''}
                  ${index === 1 ? 'bg-gray-100 text-gray-800' : ''}
                  ${index === 2 ? 'bg-orange-100 text-orange-800' : ''}
                  ${index > 2 ? 'bg-gray-50 text-gray-600' : ''}
                `}
              >
                {index + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500">{item.total_uses} uses</span>
                  {item.average_rating && (
                    <span className="text-xs text-yellow-500">★ {item.average_rating.toFixed(1)}</span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs font-medium text-gray-500">
                  {item.script_type.replace('_', ' ')}
                </span>
              </div>
            </div>
          </li>
        ))}

        {bestPerformers.length === 0 && !isLoading && (
          <li className="p-8 text-center text-gray-500">
            No talk tracks with performance data yet
          </li>
        )}
      </ul>
    </div>
  );

  const renderABTestResults = () => {
    if (!selectedMetrics?.variant_performance) return null;

    const variants = Object.entries(selectedMetrics.variant_performance);
    if (variants.length < 2) return null;

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">A/B Test Results</h3>
        <div className="space-y-4">
          {variants.map(([variant, data]: [string, Record<string, unknown>]) => (
            <div
              key={variant}
              className={`p-4 rounded-lg border ${
                data.is_winner ? 'border-green-500 bg-green-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">
                  Variant {variant}
                  {data.is_winner && (
                    <span className="ml-2 text-xs text-green-600 font-semibold">WINNER</span>
                  )}
                </span>
                <span className="text-sm text-gray-500">{data.total_uses as number} uses</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Meeting Rate:</span>
                  <span className="ml-2 font-medium">
                    {formatPercent(data.meetings_scheduled_rate as number)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Deal Advancement:</span>
                  <span className="ml-2 font-medium">
                    {formatPercent(data.deal_advancement_rate as number)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Performance Analytics</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Time Range:</span>
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`
                px-3 py-1 text-sm rounded-md
                ${timeRange === days
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Summary */}
      {selectedMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {renderMetricCard('Total Uses', selectedMetrics.total_uses, `${selectedMetrics.unique_users} unique users`)}
          {renderMetricCard(
            'Meeting Rate',
            formatPercent(selectedMetrics.meetings_scheduled_rate),
            'Calls that scheduled next step',
            'green'
          )}
          {renderMetricCard(
            'Deal Advancement',
            formatPercent(selectedMetrics.deal_advancement_rate),
            'Calls that moved deal forward',
            'purple'
          )}
          {renderMetricCard(
            'Avg Rating',
            selectedMetrics.average_rating?.toFixed(1) || 'N/A',
            selectedMetrics.average_rating ? 'out of 5 stars' : 'No ratings yet',
            'yellow'
          )}
        </div>
      )}

      {/* Charts and Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {renderTrendChart()}
          {renderABTestResults()}
        </div>
        <div className="lg:col-span-1">
          {renderLeaderboard()}
        </div>
      </div>
    </div>
  );
}
