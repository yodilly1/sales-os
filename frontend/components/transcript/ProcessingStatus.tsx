'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, Clock, AlertCircle, Loader2, FileText, Brain, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ProcessingStatus as ProcessingStatusType } from '@/lib/types';

interface ProcessingStatusProps {
  status: ProcessingStatusType;
  progress?: number;
  message?: string;
  estimatedTime?: number; // seconds remaining
  className?: string;
}

const statusConfig = {
  pending: {
    icon: Clock,
    label: 'Queued',
    description: 'Your transcript is in the queue',
    color: 'text-neutral-500',
    bgColor: 'bg-neutral-100',
    borderColor: 'border-neutral-200',
  },
  processing: {
    icon: Loader2,
    label: 'Processing',
    description: 'Analyzing your transcript with AI',
    color: 'text-primary-600',
    bgColor: 'bg-primary-50',
    borderColor: 'border-primary-200',
  },
  completed: {
    icon: CheckCircle,
    label: 'Complete',
    description: 'SPICED analysis is ready',
    color: 'text-success-600',
    bgColor: 'bg-success-50',
    borderColor: 'border-success-200',
  },
  failed: {
    icon: AlertCircle,
    label: 'Failed',
    description: 'Something went wrong',
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
    borderColor: 'border-danger-200',
  },
};

const processingSteps = [
  { id: 'upload', label: 'Uploading transcript', icon: FileText },
  { id: 'parse', label: 'Parsing content', icon: FileText },
  { id: 'analyze', label: 'AI SPICED analysis', icon: Brain },
  { id: 'generate', label: 'Generating insights', icon: Sparkles },
];

export function ProcessingStatus({
  status,
  progress = 0,
  message,
  estimatedTime,
  className,
}: ProcessingStatusProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  const [currentStep, setCurrentStep] = useState(0);

  // Animate through steps when processing
  useEffect(() => {
    if (status !== 'processing') return;

    const stepFromProgress = Math.min(
      Math.floor((progress / 100) * processingSteps.length),
      processingSteps.length - 1
    );
    setCurrentStep(stepFromProgress);
  }, [status, progress]);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div
      className={cn(
        'rounded-xl border p-6',
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className={cn('p-2 rounded-lg', config.bgColor)}>
          <Icon
            className={cn(
              'w-6 h-6',
              config.color,
              status === 'processing' && 'animate-spin'
            )}
          />
        </div>
        <div>
          <h3 className={cn('font-semibold', config.color)}>{config.label}</h3>
          <p className="text-sm text-neutral-600">
            {message || config.description}
          </p>
        </div>
        {estimatedTime && status === 'processing' && (
          <div className="ml-auto text-right">
            <p className="text-sm text-neutral-500">Est. time remaining</p>
            <p className="font-medium text-neutral-700">
              {formatTime(estimatedTime)}
            </p>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {status === 'processing' && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-neutral-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Processing Steps */}
      {(status === 'processing' || status === 'pending') && (
        <div className="space-y-3">
          {processingSteps.map((step, index) => {
            const StepIcon = step.icon;
            const isComplete = status === 'processing' && index < currentStep;
            const isCurrent = status === 'processing' && index === currentStep;
            const isPending = status === 'pending' || index > currentStep;

            return (
              <div
                key={step.id}
                className={cn(
                  'flex items-center gap-3 text-sm transition-colors',
                  isComplete && 'text-success-600',
                  isCurrent && 'text-primary-600',
                  isPending && 'text-neutral-400'
                )}
              >
                {isComplete ? (
                  <CheckCircle className="w-4 h-4" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-current" />
                )}
                <span className={cn(isCurrent && 'font-medium')}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Completed Message */}
      {status === 'completed' && (
        <div className="text-sm text-success-700">
          Your transcript has been analyzed successfully. View the SPICED analysis
          below to see insights and recommendations.
        </div>
      )}

      {/* Failed Message */}
      {status === 'failed' && (
        <div className="text-sm text-danger-700">
          {message || 'We encountered an error processing your transcript. Please try again or contact support if the issue persists.'}
        </div>
      )}
    </div>
  );
}

/**
 * Minimal inline status indicator
 */
export function ProcessingStatusBadge({ status }: { status: ProcessingStatusType }) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
        config.bgColor,
        config.color
      )}
    >
      <Icon
        className={cn(
          'w-3 h-3',
          status === 'processing' && 'animate-spin'
        )}
      />
      {config.label}
    </span>
  );
}
