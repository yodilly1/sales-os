'use client';

import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Quote,
  Lightbulb,
  Target,
  AlertTriangle,
  Flame,
  TrendingUp,
  Calendar,
  CheckSquare,
} from 'lucide-react';
import { Card, CardBody } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { cn } from '@/lib/utils';
import { SPICEDElement } from '@/lib/types';

interface SPICEDCardProps {
  element: SPICEDElement;
  className?: string;
}

const elementConfig = {
  situation: {
    icon: Target,
    title: 'Situation',
    description: 'Current state and context of the prospect',
    color: 'primary',
  },
  pain: {
    icon: AlertTriangle,
    title: 'Pain',
    description: 'Problems and challenges they face',
    color: 'danger',
  },
  impact: {
    icon: TrendingUp,
    title: 'Impact',
    description: 'Business impact of the pain',
    color: 'warning',
  },
  critical_event: {
    icon: Calendar,
    title: 'Critical Event',
    description: 'Triggering event or deadline driving urgency',
    color: 'accent',
  },
  expected_decision: {
    icon: CheckSquare,
    title: 'Expected Decision',
    description: 'Timeline and decision process',
    color: 'success',
  },
  decision_criteria: {
    icon: Flame,
    title: 'Decision Criteria',
    description: 'How they will evaluate solutions',
    color: 'primary',
  },
};

const scoreConfig = {
  1: { label: 'Not Identified', variant: 'danger' as const, bg: 'bg-danger-50', border: 'border-danger-200' },
  2: { label: 'Weak', variant: 'danger' as const, bg: 'bg-danger-50', border: 'border-danger-200' },
  3: { label: 'Partial', variant: 'warning' as const, bg: 'bg-warning-50', border: 'border-warning-200' },
  4: { label: 'Good', variant: 'primary' as const, bg: 'bg-primary-50', border: 'border-primary-200' },
  5: { label: 'Strong', variant: 'success' as const, bg: 'bg-success-50', border: 'border-success-200' },
};

export function SPICEDCard({ element, className }: SPICEDCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const config = elementConfig[element.key];
  const score = scoreConfig[element.score];
  const Icon = config.icon;

  return (
    <Card className={cn('transition-shadow hover:shadow-elevated', className)}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full flex items-center gap-4 p-4 text-left transition-colors rounded-t-xl',
          score.bg
        )}
      >
        {/* Icon */}
        <div
          className={cn(
            'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center',
            `bg-${config.color}-100`
          )}
        >
          <Icon className={`w-5 h-5 text-${config.color}-600`} />
        </div>

        {/* Title and Score */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-neutral-900">{config.title}</h3>
            <Badge variant={score.variant}>{score.label}</Badge>
          </div>
          <p className="text-sm text-neutral-600 truncate">{config.description}</p>
        </div>

        {/* Score Visual */}
        <div className="flex-shrink-0 flex items-center gap-3">
          <ScoreIndicator score={element.score} />
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-neutral-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-neutral-400" />
          )}
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <CardBody className="space-y-4">
          {/* Main Content */}
          <div>
            <h4 className="text-sm font-medium text-neutral-500 mb-2">Analysis</h4>
            <p className="text-neutral-700">{element.content}</p>
          </div>

          {/* Quotes */}
          {element.quotes.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-neutral-500 mb-2 flex items-center gap-1">
                <Quote className="w-4 h-4" />
                Key Quotes
              </h4>
              <div className="space-y-2">
                {element.quotes.map((quote, index) => (
                  <blockquote
                    key={index}
                    className="pl-4 border-l-2 border-neutral-200 text-sm text-neutral-600 italic"
                  >
                    "{quote}"
                  </blockquote>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {element.recommendations && element.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-neutral-500 mb-2 flex items-center gap-1">
                <Lightbulb className="w-4 h-4" />
                Recommendations
              </h4>
              <ul className="space-y-1">
                {element.recommendations.map((rec, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-sm text-neutral-600"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-2 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardBody>
      )}
    </Card>
  );
}

/**
 * Visual score indicator (5 dots)
 */
function ScoreIndicator({ score }: { score: 1 | 2 | 3 | 4 | 5 }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={cn(
            'w-2 h-2 rounded-full transition-colors',
            i <= score
              ? score >= 4
                ? 'bg-success-500'
                : score >= 3
                ? 'bg-warning-500'
                : 'bg-danger-500'
              : 'bg-neutral-200'
          )}
        />
      ))}
    </div>
  );
}

/**
 * Compact version for list views
 */
export function SPICEDCardCompact({ element }: { element: SPICEDElement }) {
  const config = elementConfig[element.key];
  const score = scoreConfig[element.score];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border',
        score.bg,
        score.border
      )}
    >
      <Icon className={`w-4 h-4 text-${config.color}-600`} />
      <span className="font-medium text-sm text-neutral-900">{config.title}</span>
      <div className="ml-auto flex items-center gap-2">
        <ScoreIndicator score={element.score} />
        <Badge variant={score.variant} size="sm">
          {element.score}/5
        </Badge>
      </div>
    </div>
  );
}
