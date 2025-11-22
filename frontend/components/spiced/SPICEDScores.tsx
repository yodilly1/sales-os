'use client';

import { Card, CardHeader, CardTitle, CardBody } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { cn } from '@/lib/utils';
import { SPICEDAnalysis, SPICEDElement } from '@/lib/types';
import {
  Target,
  AlertTriangle,
  TrendingUp,
  Calendar,
  CheckSquare,
  Flame,
  Trophy,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';

interface SPICEDScoresProps {
  analysis: SPICEDAnalysis;
  className?: string;
}

const elementConfig: Record<
  string,
  { icon: React.ElementType; label: string; shortLabel: string }
> = {
  situation: { icon: Target, label: 'Situation', shortLabel: 'S' },
  pain: { icon: AlertTriangle, label: 'Pain', shortLabel: 'P' },
  impact: { icon: TrendingUp, label: 'Impact', shortLabel: 'I' },
  critical_event: { icon: Calendar, label: 'Critical Event', shortLabel: 'C' },
  expected_decision: { icon: CheckSquare, label: 'Decision', shortLabel: 'E' },
  decision_criteria: { icon: Flame, label: 'Criteria', shortLabel: 'D' },
};

export function SPICEDScores({ analysis, className }: SPICEDScoresProps) {
  const getScoreColor = (score: number) => {
    if (score >= 4) return 'success';
    if (score >= 3) return 'warning';
    return 'danger';
  };

  const overallColor = getScoreColor(analysis.overallScore);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>SPICED Analysis</CardTitle>
          <div className="flex items-center gap-2">
            <Trophy className={`w-5 h-5 text-${overallColor}-500`} />
            <span className="text-2xl font-bold text-neutral-900">
              {analysis.overallScore.toFixed(1)}
            </span>
            <span className="text-sm text-neutral-500">/ 5</span>
          </div>
        </div>
      </CardHeader>

      <CardBody className="space-y-6">
        {/* Visual Score Chart */}
        <div className="grid grid-cols-6 gap-2">
          {analysis.elements.map((element) => {
            const config = elementConfig[element.key];
            const Icon = config.icon;
            return (
              <div key={element.key} className="text-center">
                <div
                  className={cn(
                    'relative h-24 bg-neutral-100 rounded-lg overflow-hidden mb-2'
                  )}
                >
                  <div
                    className={cn(
                      'absolute bottom-0 left-0 right-0 transition-all duration-500',
                      element.score >= 4
                        ? 'bg-success-500'
                        : element.score >= 3
                        ? 'bg-warning-500'
                        : 'bg-danger-500'
                    )}
                    style={{ height: `${(element.score / 5) * 100}%` }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-neutral-900 drop-shadow-sm">
                      {element.score}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <Icon className="w-4 h-4 text-neutral-500" />
                  <span className="text-xs font-medium text-neutral-600 truncate w-full">
                    {config.shortLabel}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary */}
        <div className="p-4 bg-neutral-50 rounded-lg">
          <p className="text-sm text-neutral-700">{analysis.summary}</p>
        </div>

        {/* Strengths and Areas for Improvement */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Strengths */}
          <div className="p-4 bg-success-50 rounded-lg border border-success-100">
            <h4 className="flex items-center gap-2 font-medium text-success-800 mb-3">
              <ArrowUp className="w-4 h-4" />
              Strengths
            </h4>
            <ul className="space-y-2">
              {analysis.strengths.map((strength, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm text-success-700"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-success-500 mt-1.5 flex-shrink-0" />
                  {strength}
                </li>
              ))}
            </ul>
          </div>

          {/* Areas for Improvement */}
          <div className="p-4 bg-warning-50 rounded-lg border border-warning-100">
            <h4 className="flex items-center gap-2 font-medium text-warning-800 mb-3">
              <ArrowDown className="w-4 h-4" />
              Areas for Improvement
            </h4>
            <ul className="space-y-2">
              {analysis.areasForImprovement.map((area, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm text-warning-700"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-warning-500 mt-1.5 flex-shrink-0" />
                  {area}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Coaching Feedback */}
        {analysis.coachingFeedback && (
          <div className="p-4 bg-primary-50 rounded-lg border border-primary-100">
            <h4 className="font-medium text-primary-800 mb-2">
              Coaching Feedback
            </h4>
            <p className="text-sm text-primary-700">{analysis.coachingFeedback}</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

/**
 * Mini version for list/card views
 */
export function SPICEDScoreMini({ score }: { score: number }) {
  const getVariant = () => {
    if (score >= 4) return 'success';
    if (score >= 3) return 'warning';
    return 'danger';
  };

  return (
    <Badge variant={getVariant()}>
      <Trophy className="w-3 h-3 mr-1" />
      {score.toFixed(1)}
    </Badge>
  );
}

/**
 * Horizontal bar chart version
 */
export function SPICEDScoreBar({
  elements,
}: {
  elements: SPICEDElement[];
}) {
  return (
    <div className="space-y-2">
      {elements.map((element) => {
        const config = elementConfig[element.key];
        const Icon = config.icon;
        const percentage = (element.score / 5) * 100;

        return (
          <div key={element.key} className="flex items-center gap-3">
            <div className="flex items-center gap-2 w-24">
              <Icon className="w-4 h-4 text-neutral-400" />
              <span className="text-sm text-neutral-600 truncate">
                {config.label}
              </span>
            </div>
            <div className="flex-1 h-2 bg-neutral-100 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-500',
                  element.score >= 4
                    ? 'bg-success-500'
                    : element.score >= 3
                    ? 'bg-warning-500'
                    : 'bg-danger-500'
                )}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="w-6 text-sm font-medium text-neutral-700 text-right">
              {element.score}
            </span>
          </div>
        );
      })}
    </div>
  );
}
