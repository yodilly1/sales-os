'use client';

import type { CallFeedback } from '@/types/coaching';

interface FeedbackPanelProps {
  feedback: CallFeedback[];
  className?: string;
}

const CATEGORY_CONFIG = {
  strength: {
    icon: '✓',
    label: 'Strength',
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-600',
    titleColor: 'text-emerald-800',
  },
  improvement: {
    icon: '!',
    label: 'Needs Improvement',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    titleColor: 'text-amber-800',
  },
  tip: {
    icon: '💡',
    label: 'Coaching Tip',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    titleColor: 'text-blue-800',
  },
};

const SPICED_LABELS = {
  situation: 'Situation',
  pain: 'Pain',
  impact: 'Impact',
  criticalEvent: 'Critical Event',
  decision: 'Decision',
};

function FeedbackCard({ item }: { item: CallFeedback }) {
  const config = CATEGORY_CONFIG[item.category];

  return (
    <div className={`rounded-lg border p-4 ${config.bgColor} ${config.borderColor}`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${config.iconBg}`}>
          <span className={`text-sm font-bold ${config.iconColor}`}>{config.icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`font-semibold ${config.titleColor}`}>{item.title}</span>
            {item.spicedElement && (
              <span className="text-xs px-2 py-0.5 bg-white/50 rounded-full text-gray-600">
                {SPICED_LABELS[item.spicedElement]}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">{item.content}</p>
          {item.timestamp && (
            <p className="text-xs text-gray-500 mt-2">
              At {item.timestamp} in the call
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function FeedbackPanel({ feedback, className = '' }: FeedbackPanelProps) {
  const strengths = feedback.filter(f => f.category === 'strength');
  const improvements = feedback.filter(f => f.category === 'improvement');
  const tips = feedback.filter(f => f.category === 'tip');

  if (feedback.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <div className="text-gray-400 text-4xl mb-2">📋</div>
        <p className="text-gray-500">No feedback available yet</p>
        <p className="text-sm text-gray-400 mt-1">Feedback will appear after the call is analyzed</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-emerald-50 rounded-lg">
          <p className="text-2xl font-bold text-emerald-600">{strengths.length}</p>
          <p className="text-xs text-emerald-700">Strengths</p>
        </div>
        <div className="text-center p-3 bg-amber-50 rounded-lg">
          <p className="text-2xl font-bold text-amber-600">{improvements.length}</p>
          <p className="text-xs text-amber-700">To Improve</p>
        </div>
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <p className="text-2xl font-bold text-blue-600">{tips.length}</p>
          <p className="text-xs text-blue-700">Tips</p>
        </div>
      </div>

      {/* Strengths */}
      {strengths.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
            What You Did Well
          </h3>
          <div className="space-y-3">
            {strengths.map(item => (
              <FeedbackCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* Improvements */}
      {improvements.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
            Areas for Improvement
          </h3>
          <div className="space-y-3">
            {improvements.map(item => (
              <FeedbackCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      {tips.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
            Coaching Tips
          </h3>
          <div className="space-y-3">
            {tips.map(item => (
              <FeedbackCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default FeedbackPanel;
