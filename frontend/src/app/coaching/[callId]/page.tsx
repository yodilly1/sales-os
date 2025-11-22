'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { SPICEDRadar, FeedbackPanel, WbDTips } from '@/components/coaching';
import { mockCallData, mockDashboardData } from '@/lib/api/coaching';

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export default function CallFeedbackPage() {
  // callId will be used for API calls in production
  const _params = useParams();
  void _params; // Will be used to fetch call data

  // In production, this would fetch the call data based on callId
  const call = mockCallData;
  const tips = mockDashboardData.tips;

  // Find the weakest SPICED element to highlight tips for
  const scores = call.scores;
  type SPICEDElement = 'situation' | 'pain' | 'impact' | 'criticalEvent' | 'decision';
  const elements: SPICEDElement[] = ['situation', 'pain', 'impact', 'criticalEvent', 'decision'];
  const weakestElement = elements.reduce<SPICEDElement>((weakest, current) => {
    return scores[current] < scores[weakest] ? current : weakest;
  }, elements[0]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm mb-4">
            <Link href="/coaching" className="text-blue-600 hover:text-blue-700">
              Coaching
            </Link>
            <span className="text-gray-400">/</span>
            <span className="text-gray-600">Call Feedback</span>
          </nav>

          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                {call.title}
              </h1>
              <div className="flex flex-wrap items-center gap-4 mt-2 text-gray-500">
                <span className="flex items-center gap-1">
                  <span>👤</span>
                  <span>{call.prospect}</span>
                </span>
                <span className="flex items-center gap-1">
                  <span>🏢</span>
                  <span>{call.company}</span>
                </span>
                <span className="flex items-center gap-1">
                  <span>📅</span>
                  <span>{formatDate(call.date)}</span>
                </span>
                <span className="flex items-center gap-1">
                  <span>⏱️</span>
                  <span>{formatDuration(call.duration)}</span>
                </span>
              </div>
            </div>

            {/* Overall Score */}
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-500">Overall Score</p>
                <p className={`text-4xl font-bold ${
                  call.scores.overall >= 80 ? 'text-emerald-600' :
                  call.scores.overall >= 60 ? 'text-amber-600' :
                  'text-red-600'
                }`}>
                  {call.scores.overall}
                </p>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                call.scores.overall >= 80 ? 'bg-emerald-100 text-emerald-700' :
                call.scores.overall >= 60 ? 'bg-amber-100 text-amber-700' :
                'bg-red-100 text-red-700'
              }`}>
                {call.scores.overall >= 80 ? 'Excellent' :
                 call.scores.overall >= 60 ? 'Good' :
                 call.scores.overall >= 40 ? 'Needs Work' : 'Critical'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Scores & Feedback */}
          <div className="lg:col-span-2 space-y-8">
            {/* SPICED Radar */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                SPICED Score Breakdown
              </h2>
              <SPICEDRadar scores={call.scores} size="lg" />
            </div>

            {/* Feedback Panel */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Coaching Feedback
              </h2>
              <FeedbackPanel feedback={call.feedback} />
            </div>

            {/* Transcript (if available) */}
            {call.transcript && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Call Transcript
                </h2>
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans bg-gray-50 p-4 rounded-lg">
                    {call.transcript}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Tips & Actions */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
                  <span>📧</span>
                  <span>Share Feedback</span>
                </button>
                <button className="w-full flex items-center gap-2 px-4 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors">
                  <span>📥</span>
                  <span>Download Report</span>
                </button>
                {call.recordingUrl && (
                  <button className="w-full flex items-center gap-2 px-4 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors">
                    <span>🎧</span>
                    <span>Listen to Recording</span>
                  </button>
                )}
              </div>
            </div>

            {/* Improvement Focus */}
            <div className="bg-amber-50 rounded-xl border border-amber-200 p-6">
              <h3 className="font-semibold text-amber-800 mb-2">Focus Area</h3>
              <p className="text-sm text-amber-700">
                Based on this call, consider focusing on{' '}
                <strong>
                  {weakestElement === 'criticalEvent' ? 'Critical Event' :
                   weakestElement.charAt(0).toUpperCase() + weakestElement.slice(1)}
                </strong>
                {' '}in your next calls.
              </p>
            </div>

            {/* Related Tips */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Related Tips</h3>
              <WbDTips
                tips={tips.filter(t => t.element === weakestElement).slice(0, 2)}
                highlightElement={weakestElement}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
