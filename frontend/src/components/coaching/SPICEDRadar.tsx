'use client';

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { SPICEDScores } from '@/types/coaching';

interface SPICEDRadarProps {
  scores: SPICEDScores;
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const SPICED_LABELS: Record<keyof Omit<SPICEDScores, 'overall'>, string> = {
  situation: 'Situation',
  pain: 'Pain',
  impact: 'Impact',
  criticalEvent: 'Critical Event',
  decision: 'Decision',
};

const SPICED_DESCRIPTIONS: Record<keyof Omit<SPICEDScores, 'overall'>, string> = {
  situation: 'Understanding the current state',
  pain: 'Identifying challenges and problems',
  impact: 'Quantifying business impact',
  criticalEvent: 'Identifying timeline triggers',
  decision: 'Understanding decision process',
};

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600';
  if (score >= 60) return 'text-amber-600';
  return 'text-red-600';
}

function getScoreBadge(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Needs Work';
  return 'Critical';
}

interface RadarDataPoint {
  element: string;
  fullName: string;
  score: number;
  description: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: RadarDataPoint }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const item = payload[0].payload;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs">
        <p className="font-semibold text-gray-900">{item.fullName}</p>
        <p className="text-sm text-gray-600 mb-2">{item.description}</p>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${getScoreColor(item.score)}`}>{item.score}</span>
          <span className="text-xs text-gray-500">/ 100</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            item.score >= 80 ? 'bg-emerald-100 text-emerald-700' :
            item.score >= 60 ? 'bg-amber-100 text-amber-700' :
            'bg-red-100 text-red-700'
          }`}>
            {getScoreBadge(item.score)}
          </span>
        </div>
      </div>
    );
  }
  return null;
}

export function SPICEDRadar({ scores, showLabels = true, size = 'md', className = '' }: SPICEDRadarProps) {
  const data: RadarDataPoint[] = [
    { element: 'S', fullName: 'Situation', score: scores.situation, description: SPICED_DESCRIPTIONS.situation },
    { element: 'P', fullName: 'Pain', score: scores.pain, description: SPICED_DESCRIPTIONS.pain },
    { element: 'I', fullName: 'Impact', score: scores.impact, description: SPICED_DESCRIPTIONS.impact },
    { element: 'C', fullName: 'Critical Event', score: scores.criticalEvent, description: SPICED_DESCRIPTIONS.criticalEvent },
    { element: 'D', fullName: 'Decision', score: scores.decision, description: SPICED_DESCRIPTIONS.decision },
  ];

  const sizeClasses = {
    sm: 'h-48',
    md: 'h-64',
    lg: 'h-80',
  };

  return (
    <div className={`${className}`}>
      <div className={`${sizeClasses[size]} w-full`}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="element"
              tick={{ fill: '#374151', fontSize: 14, fontWeight: 600 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#9ca3af', fontSize: 10 }}
              tickCount={5}
            />
            <Tooltip content={<CustomTooltip />} />
            <Radar
              name="SPICED Score"
              dataKey="score"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {showLabels && (
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-5 gap-2">
          {Object.entries(SPICED_LABELS).map(([key, label]) => {
            const score = scores[key as keyof Omit<SPICEDScores, 'overall'>];
            return (
              <div key={key} className="text-center p-2 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
                <p className={`text-lg font-bold ${getScoreColor(score)}`}>{score}</p>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4 flex items-center justify-center gap-2">
        <span className="text-sm text-gray-600">Overall Score:</span>
        <span className={`text-2xl font-bold ${getScoreColor(scores.overall)}`}>{scores.overall}</span>
        <span className="text-sm text-gray-400">/ 100</span>
      </div>
    </div>
  );
}

export default SPICEDRadar;
