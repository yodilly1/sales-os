'use client';

import Link from 'next/link';
import type { CoachingCall } from '@/types/coaching';

interface CallCardProps {
  call: CoachingCall;
  className?: string;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600 bg-emerald-50';
  if (score >= 60) return 'text-amber-600 bg-amber-50';
  return 'text-red-600 bg-red-50';
}

function getStatusBadge(status: CoachingCall['status']) {
  switch (status) {
    case 'analyzed':
      return { label: 'Analyzed', color: 'bg-emerald-100 text-emerald-700' };
    case 'pending':
      return { label: 'Processing', color: 'bg-amber-100 text-amber-700' };
    case 'failed':
      return { label: 'Failed', color: 'bg-red-100 text-red-700' };
  }
}

export function CallCard({ call, className = '' }: CallCardProps) {
  const status = getStatusBadge(call.status);

  return (
    <Link
      href={`/coaching/${call.id}`}
      className={`block bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all ${className}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium text-gray-900 truncate">{call.title}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${status.color}`}>
              {status.label}
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>{call.prospect}</span>
            <span>•</span>
            <span>{call.company}</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-400 mt-2">
            <span>{formatDate(call.date)}</span>
            <span>•</span>
            <span>{formatDuration(call.duration)}</span>
          </div>
        </div>

        {call.status === 'analyzed' && (
          <div className={`flex-shrink-0 px-3 py-2 rounded-lg ${getScoreColor(call.scores.overall)}`}>
            <p className="text-xs text-center opacity-75">Score</p>
            <p className="text-2xl font-bold text-center">{call.scores.overall}</p>
          </div>
        )}
      </div>

      {call.status === 'analyzed' && (
        <div className="mt-4 grid grid-cols-5 gap-2">
          {(['situation', 'pain', 'impact', 'criticalEvent', 'decision'] as const).map((key) => (
            <div key={key} className="text-center">
              <p className="text-xs text-gray-400 uppercase">
                {key === 'criticalEvent' ? 'CE' : key[0].toUpperCase()}
              </p>
              <p className="text-sm font-medium text-gray-700">{call.scores[key]}</p>
            </div>
          ))}
        </div>
      )}
    </Link>
  );
}

export default CallCard;
