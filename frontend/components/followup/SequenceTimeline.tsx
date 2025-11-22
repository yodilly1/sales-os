'use client';

import React from 'react';
import { Sequence, SequenceStep, SequenceStepType, FollowUpStatus } from './types';

interface SequenceTimelineProps {
  sequence: Sequence;
  onStepClick?: (step: SequenceStep) => void;
}

const stepTypeIcons: Record<SequenceStepType, string> = {
  email: '📧',
  task: '✅',
  wait: '⏰',
  condition: '🔀',
};

const statusColors: Record<FollowUpStatus, string> = {
  draft: '#94a3b8',
  pending_approval: '#f59e0b',
  approved: '#22c55e',
  scheduled: '#3b82f6',
  sent: '#8b5cf6',
  completed: '#10b981',
  cancelled: '#ef4444',
  failed: '#dc2626',
};

export function SequenceTimeline({ sequence, onStepClick }: SequenceTimelineProps) {
  function formatDuration(hours: number): string {
    if (hours < 24) return `${hours}h`;
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    if (remainingHours === 0) return `${days}d`;
    return `${days}d ${remainingHours}h`;
  }

  function getStepStatus(step: SequenceStep): 'completed' | 'current' | 'pending' {
    if (step.status === 'completed' || step.status === 'sent') return 'completed';
    if (step.stepNumber === sequence.currentStep && sequence.status === 'active') return 'current';
    return 'pending';
  }

  return (
    <div className="sequence-timeline">
      {/* Header */}
      <div className="header">
        <div className="header-info">
          <h3>{sequence.name}</h3>
          <span className={`status-badge status-${sequence.status}`}>
            {sequence.status}
          </span>
        </div>
        <div className="progress-info">
          <span>Step {sequence.currentStep} of {sequence.totalSteps}</span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${(sequence.currentStep / sequence.totalSteps) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="timeline">
        {sequence.steps.map((step, index) => {
          const stepStatus = getStepStatus(step);
          const isLast = index === sequence.steps.length - 1;

          return (
            <div
              key={step.stepNumber}
              className={`timeline-step ${stepStatus}`}
              onClick={() => onStepClick?.(step)}
            >
              {/* Connector line */}
              {!isLast && (
                <div className="connector">
                  <div className={`line ${stepStatus}`} />
                  {step.delayHours > 0 && step.stepType !== 'wait' && (
                    <span className="delay-label">+{formatDuration(step.delayHours)}</span>
                  )}
                </div>
              )}

              {/* Step node */}
              <div className={`node ${stepStatus}`}>
                <span className="icon">{stepTypeIcons[step.stepType]}</span>
                {stepStatus === 'completed' && <span className="check">✓</span>}
                {stepStatus === 'current' && <span className="pulse" />}
              </div>

              {/* Step content */}
              <div className="step-content">
                <div className="step-header">
                  <span className="step-number">Step {step.stepNumber}</span>
                  <span
                    className="step-status"
                    style={{ color: statusColors[step.status] }}
                  >
                    {step.status.replace('_', ' ')}
                  </span>
                </div>

                <div className="step-info">
                  {step.stepType === 'email' && (
                    <>
                      <span className="step-type">Send Email</span>
                      {step.emailTemplateId && (
                        <span className="step-detail">Template: {step.emailTemplateId}</span>
                      )}
                    </>
                  )}

                  {step.stepType === 'task' && (
                    <>
                      <span className="step-type">Create Task</span>
                      {step.taskTemplate && (
                        <span className="step-detail">{step.taskTemplate}</span>
                      )}
                    </>
                  )}

                  {step.stepType === 'wait' && (
                    <span className="step-type">Wait {formatDuration(step.delayHours)}</span>
                  )}

                  {step.stepType === 'condition' && (
                    <>
                      <span className="step-type">Check: {step.condition}</span>
                      <div className="branch-info">
                        <span>→ True: Step {step.conditionTrueStep}</span>
                        <span>→ False: Step {step.conditionFalseStep}</span>
                      </div>
                    </>
                  )}
                </div>

                {step.executedAt && (
                  <div className="executed-at">
                    Executed: {new Date(step.executedAt).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Sequence info */}
      <div className="sequence-info">
        {sequence.startedAt && (
          <div className="info-item">
            <span className="label">Started:</span>
            <span className="value">{new Date(sequence.startedAt).toLocaleString()}</span>
          </div>
        )}
        {sequence.completedAt && (
          <div className="info-item">
            <span className="label">Completed:</span>
            <span className="value">{new Date(sequence.completedAt).toLocaleString()}</span>
          </div>
        )}
        {sequence.pausedAt && (
          <div className="info-item">
            <span className="label">Paused:</span>
            <span className="value">{new Date(sequence.pausedAt).toLocaleString()}</span>
          </div>
        )}
      </div>

      <style jsx>{`
        .sequence-timeline {
          padding: 1.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 1.5rem;
        }

        .header-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .header-info h3 {
          margin: 0;
          font-size: 1.125rem;
          font-weight: 600;
        }

        .status-badge {
          padding: 0.25rem 0.75rem;
          font-size: 0.75rem;
          font-weight: 500;
          border-radius: 9999px;
          text-transform: capitalize;
        }

        .status-draft { background: #f1f5f9; color: #475569; }
        .status-active { background: #dbeafe; color: #1e40af; }
        .status-paused { background: #fef3c7; color: #92400e; }
        .status-completed { background: #dcfce7; color: #166534; }
        .status-cancelled { background: #fee2e2; color: #991b1b; }

        .progress-info {
          text-align: right;
        }

        .progress-info span {
          font-size: 0.875rem;
          color: #64748b;
        }

        .progress-bar {
          width: 120px;
          height: 6px;
          background: #e2e8f0;
          border-radius: 3px;
          margin-top: 0.5rem;
        }

        .progress-fill {
          height: 100%;
          background: #3b82f6;
          border-radius: 3px;
          transition: width 0.3s;
        }

        .timeline {
          display: flex;
          flex-direction: column;
          gap: 0;
        }

        .timeline-step {
          display: flex;
          position: relative;
          padding-left: 3rem;
          cursor: pointer;
        }

        .timeline-step:hover .step-content {
          background: #f8fafc;
        }

        .connector {
          position: absolute;
          left: 1rem;
          top: 2.5rem;
          bottom: -0.5rem;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .line {
          width: 2px;
          flex: 1;
          background: #e2e8f0;
        }

        .line.completed {
          background: #22c55e;
        }

        .line.current {
          background: linear-gradient(to bottom, #22c55e, #e2e8f0);
        }

        .delay-label {
          position: absolute;
          left: 1.5rem;
          top: 50%;
          transform: translateY(-50%);
          font-size: 0.625rem;
          color: #94a3b8;
          background: white;
          padding: 0.125rem 0.25rem;
        }

        .node {
          position: absolute;
          left: 0;
          top: 0.5rem;
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border: 2px solid #e2e8f0;
          border-radius: 9999px;
        }

        .node.completed {
          border-color: #22c55e;
          background: #dcfce7;
        }

        .node.current {
          border-color: #3b82f6;
          background: #dbeafe;
        }

        .icon {
          font-size: 0.875rem;
        }

        .check {
          position: absolute;
          bottom: -0.25rem;
          right: -0.25rem;
          width: 0.875rem;
          height: 0.875rem;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.5rem;
          color: white;
          background: #22c55e;
          border-radius: 9999px;
        }

        .pulse {
          position: absolute;
          width: 100%;
          height: 100%;
          border: 2px solid #3b82f6;
          border-radius: 9999px;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.3); opacity: 0; }
          100% { transform: scale(1); opacity: 0; }
        }

        .step-content {
          flex: 1;
          padding: 0.75rem;
          margin-bottom: 0.5rem;
          border-radius: 0.375rem;
          transition: background 0.2s;
        }

        .step-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.25rem;
        }

        .step-number {
          font-size: 0.75rem;
          font-weight: 600;
          color: #64748b;
        }

        .step-status {
          font-size: 0.75rem;
          font-weight: 500;
          text-transform: capitalize;
        }

        .step-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .step-type {
          font-weight: 500;
          color: #1e293b;
        }

        .step-detail {
          font-size: 0.875rem;
          color: #64748b;
        }

        .branch-info {
          display: flex;
          gap: 1rem;
          font-size: 0.75rem;
          color: #64748b;
        }

        .executed-at {
          margin-top: 0.5rem;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .sequence-info {
          display: flex;
          gap: 2rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .info-item {
          display: flex;
          gap: 0.5rem;
          font-size: 0.875rem;
        }

        .info-item .label {
          color: #64748b;
        }

        .info-item .value {
          color: #1e293b;
        }
      `}</style>
    </div>
  );
}
