'use client';

import React from 'react';
import {
  FollowUp,
  FollowUpEmail,
  FollowUpTask,
  FollowUpContentRecommendation,
  FollowUpMeetingSuggestion,
  FollowUpStatus,
  Priority,
} from './types';

interface FollowUpCardProps {
  followUp: FollowUp;
  selected?: boolean;
  onSelect?: () => void;
  onClick?: () => void;
  onApprove?: (followUp: FollowUp) => void;
  onSchedule?: (followUp: FollowUp, scheduledAt: Date) => void;
  compact?: boolean;
}

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

const priorityColors: Record<Priority, string> = {
  low: '#94a3b8',
  medium: '#3b82f6',
  high: '#f59e0b',
  urgent: '#ef4444',
};

const typeIcons: Record<string, string> = {
  email: '📧',
  task: '✅',
  content_recommendation: '📚',
  meeting_suggestion: '📅',
};

export function FollowUpCard({
  followUp,
  selected = false,
  onSelect,
  onClick,
  onApprove,
  onSchedule,
  compact = false,
}: FollowUpCardProps) {
  function getTitle(): string {
    switch (followUp.type) {
      case 'email':
        return (followUp as FollowUpEmail).draft.subject;
      case 'task':
        return (followUp as FollowUpTask).title;
      case 'content_recommendation':
        return (followUp as FollowUpContentRecommendation).primaryRecommendation?.title || 'Content Recommendations';
      case 'meeting_suggestion':
        return (followUp as FollowUpMeetingSuggestion).suggestion.title;
      default:
        return 'Follow-up';
    }
  }

  function getDescription(): string {
    switch (followUp.type) {
      case 'email': {
        const email = followUp as FollowUpEmail;
        return `To: ${email.recipient.name} (${email.recipient.email})`;
      }
      case 'task': {
        const task = followUp as FollowUpTask;
        return task.description || `Category: ${task.category}`;
      }
      case 'content_recommendation': {
        const rec = followUp as FollowUpContentRecommendation;
        return `${rec.recommendations.length} recommendations`;
      }
      case 'meeting_suggestion': {
        const meeting = followUp as FollowUpMeetingSuggestion;
        return `${meeting.suggestion.meetingType} - ${meeting.suggestion.suggestedDurationMinutes} min`;
      }
      default:
        return '';
    }
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  }

  const canApprove = followUp.status === 'pending_approval' || followUp.status === 'draft';
  const canSchedule = followUp.status === 'approved';

  return (
    <div
      className={`follow-up-card ${selected ? 'selected' : ''} ${compact ? 'compact' : ''}`}
      onClick={onClick}
    >
      {/* Selection checkbox */}
      {onSelect && (
        <div className="select-box" onClick={(e) => { e.stopPropagation(); onSelect(); }}>
          <input type="checkbox" checked={selected} onChange={() => {}} />
        </div>
      )}

      {/* Type icon */}
      <div className="type-icon">{typeIcons[followUp.type]}</div>

      {/* Content */}
      <div className="content">
        <div className="header">
          <h4 className="title">{getTitle()}</h4>
          <div className="badges">
            <span
              className="status-badge"
              style={{ backgroundColor: statusColors[followUp.status] }}
            >
              {followUp.status.replace('_', ' ')}
            </span>
            <span
              className="priority-badge"
              style={{ borderColor: priorityColors[followUp.priority] }}
            >
              {followUp.priority}
            </span>
          </div>
        </div>

        <p className="description">{getDescription()}</p>

        {!compact && (
          <div className="meta">
            <span>Created: {formatDate(followUp.createdAt)}</span>
            {followUp.scheduledAt && (
              <span>Scheduled: {formatDate(followUp.scheduledAt)}</span>
            )}
            {followUp.sentAt && (
              <span>Sent: {formatDate(followUp.sentAt)}</span>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="actions">
        {canApprove && onApprove && (
          <button
            className="approve-btn"
            onClick={(e) => {
              e.stopPropagation();
              onApprove(followUp);
            }}
          >
            Approve
          </button>
        )}
        {canSchedule && onSchedule && (
          <button
            className="schedule-btn"
            onClick={(e) => {
              e.stopPropagation();
              onSchedule(followUp, new Date());
            }}
          >
            Schedule
          </button>
        )}
      </div>

      <style jsx>{`
        .follow-up-card {
          display: flex;
          align-items: flex-start;
          gap: 1rem;
          padding: 1rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .follow-up-card:hover {
          border-color: #3b82f6;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .follow-up-card.selected {
          border-color: #3b82f6;
          background: #f0f9ff;
        }

        .follow-up-card.compact {
          padding: 0.75rem;
        }

        .select-box {
          padding-top: 0.25rem;
        }

        .type-icon {
          font-size: 1.5rem;
          padding-top: 0.25rem;
        }

        .content {
          flex: 1;
          min-width: 0;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 0.5rem;
        }

        .title {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .badges {
          display: flex;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .status-badge {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          font-weight: 500;
          color: white;
          border-radius: 9999px;
          text-transform: capitalize;
        }

        .priority-badge {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          font-weight: 500;
          color: #64748b;
          border: 1px solid;
          border-radius: 9999px;
          text-transform: capitalize;
        }

        .description {
          margin: 0 0 0.5rem 0;
          font-size: 0.875rem;
          color: #64748b;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .meta {
          display: flex;
          gap: 1rem;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .actions {
          display: flex;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .actions button {
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .approve-btn {
          background: #22c55e;
          color: white;
        }

        .approve-btn:hover {
          background: #16a34a;
        }

        .schedule-btn {
          background: #3b82f6;
          color: white;
        }

        .schedule-btn:hover {
          background: #2563eb;
        }

        .compact .title {
          font-size: 0.875rem;
        }

        .compact .description,
        .compact .meta {
          display: none;
        }
      `}</style>
    </div>
  );
}
