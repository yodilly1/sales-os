'use client';

import { useState } from 'react';
import {
  SPICEDRadar,
  TrendChart,
  WbDTips,
  TeamLeaderboard,
  MetricCard,
  CallCard,
} from '@/components/coaching';
import { mockDashboardData } from '@/lib/api/coaching';

type TabType = 'overview' | 'trends' | 'team' | 'tips';

export default function CoachingDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const data = mockDashboardData;

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'trends', label: 'Trends', icon: '📈' },
    { id: 'team', label: 'Team', icon: '👥' },
    { id: 'tips', label: 'WbD Tips', icon: '💡' },
  ];

  // Calculate average scores for the radar chart
  const averageScores = {
    situation: Math.round(data.teamLeaderboard.reduce((sum, m) => sum + m.recentScores.situation, 0) / data.teamLeaderboard.length),
    pain: Math.round(data.teamLeaderboard.reduce((sum, m) => sum + m.recentScores.pain, 0) / data.teamLeaderboard.length),
    impact: Math.round(data.teamLeaderboard.reduce((sum, m) => sum + m.recentScores.impact, 0) / data.teamLeaderboard.length),
    criticalEvent: Math.round(data.teamLeaderboard.reduce((sum, m) => sum + m.recentScores.criticalEvent, 0) / data.teamLeaderboard.length),
    decision: Math.round(data.teamLeaderboard.reduce((sum, m) => sum + m.recentScores.decision, 0) / data.teamLeaderboard.length),
    overall: data.metrics.averageScore,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                Coaching Dashboard
              </h1>
              <p className="text-gray-500 mt-1">
                Track SPICED performance and get actionable coaching insights
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">Powered by</span>
              <span className="font-semibold text-blue-600">Winning by Design</span>
            </div>
          </div>

          {/* Tabs */}
          <nav className="mt-6 flex gap-1 overflow-x-auto pb-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Total Calls Analyzed"
                value={data.metrics.totalCalls}
                change={data.metrics.callsChangePercent}
                changeLabel="vs last month"
                icon="📞"
              />
              <MetricCard
                title="Average SPICED Score"
                value={data.metrics.averageScore}
                change={data.metrics.scoreChange}
                changeLabel="vs last month"
                icon="📊"
              />
              <MetricCard
                title="Top Performer"
                value={data.metrics.topPerformer}
                subtitle="Highest avg score this month"
                icon="🏆"
              />
              <MetricCard
                title="Focus Area"
                value="Critical Event"
                subtitle="Team needs improvement here"
                icon="🎯"
              />
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* SPICED Radar */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Team SPICED Overview
                </h2>
                <SPICEDRadar scores={averageScores} size="lg" />
              </div>

              {/* Recent Calls */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Recent Calls</h2>
                  <a href="#" className="text-sm text-blue-600 hover:text-blue-700">
                    View all →
                  </a>
                </div>
                <div className="space-y-3">
                  {data.recentCalls.slice(0, 3).map((call) => (
                    <CallCard key={call.id} call={call} />
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Tips */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Quick Tips</h2>
                <button
                  onClick={() => setActiveTab('tips')}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  See all tips →
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.tips.slice(0, 2).map((tip) => (
                  <div
                    key={tip.id}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-100"
                  >
                    <h3 className="font-medium text-gray-900">{tip.title}</h3>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {tip.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="space-y-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                SPICED Score Trends
              </h2>
              <TrendChart data={data.trends} height={400} />
            </div>

            {/* Trend Insights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-emerald-500">↑</span>
                  <span className="text-sm text-gray-500">Biggest Improvement</span>
                </div>
                <p className="text-xl font-bold text-gray-900">Impact</p>
                <p className="text-sm text-emerald-600">+14 points this week</p>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-amber-500">→</span>
                  <span className="text-sm text-gray-500">Most Consistent</span>
                </div>
                <p className="text-xl font-bold text-gray-900">Situation</p>
                <p className="text-sm text-gray-600">Steady performance</p>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-red-500">!</span>
                  <span className="text-sm text-gray-500">Needs Attention</span>
                </div>
                <p className="text-xl font-bold text-gray-900">Critical Event</p>
                <p className="text-sm text-red-600">Below target</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'team' && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <TeamLeaderboard members={data.teamLeaderboard} />
          </div>
        )}

        {activeTab === 'tips' && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <WbDTips
              tips={data.tips}
              highlightElement={data.metrics.improvementArea}
            />
          </div>
        )}
      </main>
    </div>
  );
}
