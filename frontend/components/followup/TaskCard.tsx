'use client';

import React, { useState } from 'react';
import { FollowUpTask, TaskCategory, Priority } from './types';

interface TaskCardProps {
  task: FollowUpTask;
  onComplete?: (notes?: string) => void;
  onEdit?: (updates: Partial<FollowUpTask>) => void;
  onDelete?: () => void;
  onSyncToCRM?: () => void;
  showActions?: boolean;
}

const categoryIcons: Record<TaskCategory, string> = {
  call: '📞',
  email: '📧',
  meeting: '📅',
  research: '🔍',
  proposal: '📝',
  demo: '🎬',
  internal: '🏢',
  other: '📌',
};

const priorityStyles: Record<Priority, { bg: string; border: string; text: string }> = {
  low: { bg: '#f1f5f9', border: '#94a3b8', text: '#64748b' },
  medium: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
  high: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
  urgent: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
};

export function TaskCard({
  task,
  onComplete,
  onEdit,
  onDelete,
  onSyncToCRM,
  showActions = true,
}: TaskCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(task.title);
  const [editedDescription, setEditedDescription] = useState(task.description || '');
  const [completionNotes, setCompletionNotes] = useState('');
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);

  function handleSave() {
    onEdit?.({
      title: editedTitle,
      description: editedDescription,
    });
    setIsEditing(false);
  }

  function handleComplete() {
    onComplete?.(completionNotes || undefined);
    setShowCompleteDialog(false);
  }

  function formatDate(dateString?: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  function formatTime(dateString?: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  }

  function isDue(): boolean {
    if (!task.dueAt) return false;
    return new Date(task.dueAt) < new Date();
  }

  function isDueSoon(): boolean {
    if (!task.dueAt) return false;
    const dueDate = new Date(task.dueAt);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return dueDate < tomorrow && dueDate > new Date();
  }

  const isCompleted = task.status === 'completed';
  const priorityStyle = priorityStyles[task.priority];

  return (
    <div className={`task-card ${isCompleted ? 'completed' : ''}`}>
      {/* Priority indicator */}
      <div
        className="priority-bar"
        style={{ backgroundColor: priorityStyle.border }}
      />

      {/* Main content */}
      <div className="content">
        {/* Header */}
        <div className="header">
          <span className="category-icon">{categoryIcons[task.category]}</span>

          {isEditing ? (
            <input
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="title-input"
            />
          ) : (
            <h4 className={`title ${isCompleted ? 'completed' : ''}`}>
              {task.title}
            </h4>
          )}

          <span
            className="priority-badge"
            style={{
              backgroundColor: priorityStyle.bg,
              borderColor: priorityStyle.border,
              color: priorityStyle.text,
            }}
          >
            {task.priority}
          </span>
        </div>

        {/* Description */}
        {isEditing ? (
          <textarea
            value={editedDescription}
            onChange={(e) => setEditedDescription(e.target.value)}
            placeholder="Task description"
            rows={2}
            className="description-input"
          />
        ) : (
          task.description && (
            <p className="description">{task.description}</p>
          )
        )}

        {/* Meta info */}
        <div className="meta">
          <span className="category">{task.category}</span>

          {task.dueAt && (
            <span className={`due-date ${isDue() ? 'overdue' : ''} ${isDueSoon() ? 'due-soon' : ''}`}>
              Due: {formatDate(task.dueAt)} {formatTime(task.dueAt)}
            </span>
          )}

          {task.crmTaskId && (
            <span className="crm-synced">CRM Synced</span>
          )}
        </div>

        {/* Completion info */}
        {isCompleted && task.completedAt && (
          <div className="completion-info">
            <span>Completed: {formatDate(task.completedAt)}</span>
            {task.completionNotes && (
              <p className="completion-notes">{task.completionNotes}</p>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      {showActions && !isCompleted && (
        <div className="actions">
          {isEditing ? (
            <>
              <button onClick={handleSave} className="btn-save">Save</button>
              <button onClick={() => setIsEditing(false)} className="btn-cancel">Cancel</button>
            </>
          ) : (
            <>
              <button
                onClick={() => setShowCompleteDialog(true)}
                className="btn-complete"
                title="Complete task"
              >
                ✓
              </button>
              {onEdit && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-edit"
                  title="Edit task"
                >
                  ✎
                </button>
              )}
              {onSyncToCRM && !task.crmTaskId && (
                <button
                  onClick={onSyncToCRM}
                  className="btn-sync"
                  title="Sync to CRM"
                >
                  ↗
                </button>
              )}
              {onDelete && (
                <button
                  onClick={onDelete}
                  className="btn-delete"
                  title="Delete task"
                >
                  ✕
                </button>
              )}
            </>
          )}
        </div>
      )}

      {/* Complete dialog */}
      {showCompleteDialog && (
        <div className="complete-dialog">
          <h5>Complete Task</h5>
          <textarea
            value={completionNotes}
            onChange={(e) => setCompletionNotes(e.target.value)}
            placeholder="Add completion notes (optional)"
            rows={3}
          />
          <div className="dialog-actions">
            <button onClick={handleComplete} className="btn-confirm">
              Complete
            </button>
            <button onClick={() => setShowCompleteDialog(false)} className="btn-cancel">
              Cancel
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .task-card {
          display: flex;
          gap: 1rem;
          padding: 1rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          position: relative;
          transition: all 0.2s;
        }

        .task-card:hover {
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .task-card.completed {
          opacity: 0.7;
          background: #f8fafc;
        }

        .priority-bar {
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 4px;
          border-radius: 0.5rem 0 0 0.5rem;
        }

        .content {
          flex: 1;
          min-width: 0;
          padding-left: 0.5rem;
        }

        .header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.5rem;
        }

        .category-icon {
          font-size: 1.25rem;
        }

        .title {
          flex: 1;
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
        }

        .title.completed {
          text-decoration: line-through;
          color: #94a3b8;
        }

        .title-input {
          flex: 1;
          padding: 0.375rem 0.5rem;
          font-size: 1rem;
          font-weight: 600;
          border: 1px solid #3b82f6;
          border-radius: 0.25rem;
        }

        .priority-badge {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          font-weight: 500;
          border: 1px solid;
          border-radius: 9999px;
          text-transform: capitalize;
        }

        .description {
          margin: 0 0 0.5rem 0;
          font-size: 0.875rem;
          color: #64748b;
          line-height: 1.5;
        }

        .description-input {
          width: 100%;
          padding: 0.5rem;
          font-size: 0.875rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          resize: vertical;
          margin-bottom: 0.5rem;
        }

        .meta {
          display: flex;
          gap: 1rem;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .category {
          text-transform: capitalize;
        }

        .due-date {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .due-date.overdue {
          color: #ef4444;
          font-weight: 500;
        }

        .due-date.due-soon {
          color: #f59e0b;
          font-weight: 500;
        }

        .crm-synced {
          color: #22c55e;
        }

        .completion-info {
          margin-top: 0.5rem;
          padding-top: 0.5rem;
          border-top: 1px solid #e2e8f0;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .completion-notes {
          margin: 0.25rem 0 0 0;
          font-style: italic;
        }

        .actions {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .actions button {
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 0.25rem;
          cursor: pointer;
          font-size: 0.875rem;
          transition: background 0.2s;
        }

        .btn-complete {
          background: #dcfce7;
          color: #166534;
        }
        .btn-complete:hover { background: #bbf7d0; }

        .btn-edit {
          background: #dbeafe;
          color: #1e40af;
        }
        .btn-edit:hover { background: #bfdbfe; }

        .btn-sync {
          background: #fef3c7;
          color: #92400e;
        }
        .btn-sync:hover { background: #fde68a; }

        .btn-delete {
          background: #fee2e2;
          color: #991b1b;
        }
        .btn-delete:hover { background: #fecaca; }

        .btn-save {
          background: #22c55e;
          color: white;
        }

        .btn-cancel {
          background: #f1f5f9;
          color: #475569;
        }

        .complete-dialog {
          position: absolute;
          right: 0;
          top: 100%;
          z-index: 10;
          width: 300px;
          padding: 1rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .complete-dialog h5 {
          margin: 0 0 0.75rem 0;
        }

        .complete-dialog textarea {
          width: 100%;
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          resize: vertical;
          margin-bottom: 0.75rem;
        }

        .dialog-actions {
          display: flex;
          gap: 0.5rem;
        }

        .dialog-actions button {
          padding: 0.5rem 1rem;
          border: none;
          border-radius: 0.25rem;
          cursor: pointer;
        }

        .btn-confirm {
          background: #22c55e;
          color: white;
        }
      `}</style>
    </div>
  );
}
