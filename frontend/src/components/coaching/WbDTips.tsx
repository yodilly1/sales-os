'use client';

import { useState } from 'react';
import type { WbDTip, SPICEDScores } from '@/types/coaching';

interface WbDTipsProps {
  tips: WbDTip[];
  highlightElement?: keyof Omit<SPICEDScores, 'overall'>;
  className?: string;
}

const ELEMENT_COLORS = {
  situation: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', badge: 'bg-blue-100' },
  pain: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-100' },
  impact: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', badge: 'bg-emerald-100' },
  criticalEvent: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', badge: 'bg-amber-100' },
  decision: { bg: 'bg-violet-50', border: 'border-violet-200', text: 'text-violet-700', badge: 'bg-violet-100' },
};

const ELEMENT_LABELS = {
  situation: 'Situation',
  pain: 'Pain',
  impact: 'Impact',
  criticalEvent: 'Critical Event',
  decision: 'Decision',
};

const ELEMENT_ICONS = {
  situation: '🎯',
  pain: '🔥',
  impact: '📈',
  criticalEvent: '⏰',
  decision: '✅',
};

function TipCard({ tip, isHighlighted }: { tip: WbDTip; isHighlighted: boolean }) {
  const [isExpanded, setIsExpanded] = useState(isHighlighted);
  const colors = ELEMENT_COLORS[tip.element];

  return (
    <div
      className={`rounded-lg border transition-all ${colors.bg} ${colors.border} ${
        isHighlighted ? 'ring-2 ring-offset-2 ring-blue-500' : ''
      }`}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left flex items-start gap-3"
      >
        <span className="text-2xl">{ELEMENT_ICONS[tip.element]}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full ${colors.badge} ${colors.text}`}>
              {ELEMENT_LABELS[tip.element]}
            </span>
            {isHighlighted && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500 text-white">
                Recommended
              </span>
            )}
          </div>
          <h4 className="font-semibold text-gray-900">{tip.title}</h4>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{tip.description}</p>
        </div>
        <span className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-white/50">
          {tip.example && (
            <div className="mt-4">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Example Question</h5>
              <blockquote className="text-sm italic text-gray-600 bg-white/50 rounded p-3 border-l-4 border-gray-300">
                {tip.example}
              </blockquote>
            </div>
          )}

          {tip.actionItems.length > 0 && (
            <div className="mt-4">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Action Items</h5>
              <ul className="space-y-2">
                {tip.actionItems.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-emerald-500 mt-0.5">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function WbDTips({ tips, highlightElement, className = '' }: WbDTipsProps) {
  const [selectedElement, setSelectedElement] = useState<keyof Omit<SPICEDScores, 'overall'> | 'all'>('all');

  const filteredTips = selectedElement === 'all'
    ? tips
    : tips.filter(tip => tip.element === selectedElement);

  const sortedTips = [...filteredTips].sort((a, b) => {
    if (a.element === highlightElement) return -1;
    if (b.element === highlightElement) return 1;
    return 0;
  });

  return (
    <div className={className}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">📚</span>
          <h2 className="text-xl font-bold text-gray-900">WbD Methodology Tips</h2>
        </div>
        <p className="text-sm text-gray-600">
          Master the SPICED framework with these coaching tips from Winning by Design.
        </p>
      </div>

      {/* Filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => setSelectedElement('all')}
          className={`px-3 py-1 text-sm rounded-full border transition-all ${
            selectedElement === 'all'
              ? 'bg-gray-900 text-white border-gray-900'
              : 'border-gray-300 text-gray-600 hover:bg-gray-50'
          }`}
        >
          All Tips
        </button>
        {(Object.keys(ELEMENT_LABELS) as Array<keyof typeof ELEMENT_LABELS>).map((element) => {
          const colors = ELEMENT_COLORS[element];
          return (
            <button
              key={element}
              onClick={() => setSelectedElement(element)}
              className={`px-3 py-1 text-sm rounded-full border transition-all flex items-center gap-1 ${
                selectedElement === element
                  ? `${colors.badge} ${colors.text} ${colors.border}`
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{ELEMENT_ICONS[element]}</span>
              <span>{ELEMENT_LABELS[element]}</span>
            </button>
          );
        })}
      </div>

      {/* Tips List */}
      {sortedTips.length > 0 ? (
        <div className="space-y-3">
          {sortedTips.map(tip => (
            <TipCard
              key={tip.id}
              tip={tip}
              isHighlighted={tip.element === highlightElement}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No tips available for this category</p>
        </div>
      )}

      {/* SPICED Framework Summary */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-3">The SPICED Framework</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {(Object.keys(ELEMENT_LABELS) as Array<keyof typeof ELEMENT_LABELS>).map((element) => (
            <div key={element} className="text-center p-2">
              <span className="text-2xl block mb-1">{ELEMENT_ICONS[element]}</span>
              <span className={`text-sm font-medium ${ELEMENT_COLORS[element].text}`}>
                {ELEMENT_LABELS[element]}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-500 text-center mt-3">
          Winning by Design&apos;s proven methodology for discovery and qualification
        </p>
      </div>
    </div>
  );
}

export default WbDTips;
