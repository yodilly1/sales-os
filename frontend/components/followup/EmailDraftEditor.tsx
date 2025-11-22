'use client';

import React, { useState, useEffect } from 'react';
import { FollowUpEmail, EmailDraft } from './types';

interface EmailDraftEditorProps {
  email: FollowUpEmail;
  onSave: (draft: EmailDraft) => void;
  onApprove?: () => void;
  onSchedule?: (scheduledAt: Date) => void;
  onCancel?: () => void;
  readOnly?: boolean;
}

export function EmailDraftEditor({
  email,
  onSave,
  onApprove,
  onSchedule,
  onCancel,
  readOnly = false,
}: EmailDraftEditorProps) {
  const [draft, setDraft] = useState<EmailDraft>(email.draft);
  const [isEditing, setIsEditing] = useState(!readOnly);
  const [showHtml, setShowHtml] = useState(false);
  const [scheduleDate, setScheduleDate] = useState<string>('');
  const [scheduleTime, setScheduleTime] = useState<string>('09:00');
  const [showScheduler, setShowScheduler] = useState(false);

  useEffect(() => {
    setDraft(email.draft);
  }, [email]);

  function handleChange(field: keyof EmailDraft, value: string) {
    setDraft((prev) => ({ ...prev, [field]: value }));
  }

  function handleSave() {
    onSave(draft);
    setIsEditing(false);
  }

  function handleSchedule() {
    if (scheduleDate && scheduleTime) {
      const scheduledAt = new Date(`${scheduleDate}T${scheduleTime}`);
      onSchedule?.(scheduledAt);
      setShowScheduler(false);
    }
  }

  const canApprove = email.status === 'draft' || email.status === 'pending_approval';
  const canSchedule = email.status === 'approved';

  return (
    <div className="email-editor">
      {/* Header */}
      <div className="editor-header">
        <div className="recipient-info">
          <div className="recipient">
            <span className="label">To:</span>
            <span className="value">{email.recipient.name} &lt;{email.recipient.email}&gt;</span>
          </div>
          {email.cc.length > 0 && (
            <div className="cc">
              <span className="label">CC:</span>
              <span className="value">{email.cc.map(r => r.email).join(', ')}</span>
            </div>
          )}
        </div>
        <div className="status-info">
          <span className={`status status-${email.status}`}>
            {email.status.replace('_', ' ')}
          </span>
          {email.draft.confidenceScore !== undefined && (
            <span className="confidence">
              Confidence: {Math.round(email.draft.confidenceScore * 100)}%
            </span>
          )}
        </div>
      </div>

      {/* Subject */}
      <div className="subject-row">
        <label>Subject:</label>
        {isEditing ? (
          <input
            type="text"
            value={draft.subject}
            onChange={(e) => handleChange('subject', e.target.value)}
            placeholder="Email subject"
          />
        ) : (
          <span className="subject-text">{draft.subject}</span>
        )}
      </div>

      {/* Body */}
      <div className="body-section">
        <div className="body-header">
          <span>Body</span>
          <button
            className="toggle-btn"
            onClick={() => setShowHtml(!showHtml)}
          >
            {showHtml ? 'Show Plain Text' : 'Show HTML'}
          </button>
        </div>

        {isEditing ? (
          <textarea
            value={showHtml ? draft.bodyHtml : draft.bodyText}
            onChange={(e) => handleChange(showHtml ? 'bodyHtml' : 'bodyText', e.target.value)}
            rows={12}
            placeholder="Email body"
          />
        ) : (
          <div className="body-preview">
            {showHtml ? (
              <div dangerouslySetInnerHTML={{ __html: draft.bodyHtml }} />
            ) : (
              <pre>{draft.bodyText}</pre>
            )}
          </div>
        )}
      </div>

      {/* Personalization tokens */}
      {draft.tokensUsed.length > 0 && (
        <div className="tokens-section">
          <span className="label">Personalization tokens used:</span>
          <div className="tokens">
            {draft.tokensUsed.map((token) => (
              <span key={token} className="token">{token}</span>
            ))}
          </div>
        </div>
      )}

      {/* Scheduler */}
      {showScheduler && (
        <div className="scheduler">
          <h4>Schedule Email</h4>
          <div className="schedule-inputs">
            <input
              type="date"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
            />
            <input
              type="time"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
            />
          </div>
          <div className="schedule-actions">
            <button onClick={handleSchedule} className="btn-primary">
              Confirm Schedule
            </button>
            <button onClick={() => setShowScheduler(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="actions">
        {isEditing ? (
          <>
            <button onClick={handleSave} className="btn-primary">
              Save Changes
            </button>
            <button onClick={() => { setDraft(email.draft); setIsEditing(false); }} className="btn-secondary">
              Cancel
            </button>
          </>
        ) : (
          <>
            {!readOnly && (
              <button onClick={() => setIsEditing(true)} className="btn-secondary">
                Edit
              </button>
            )}
            {canApprove && onApprove && (
              <button onClick={onApprove} className="btn-success">
                Approve
              </button>
            )}
            {canSchedule && onSchedule && (
              <button onClick={() => setShowScheduler(true)} className="btn-primary">
                Schedule
              </button>
            )}
            {onCancel && (
              <button onClick={onCancel} className="btn-danger">
                Cancel Email
              </button>
            )}
          </>
        )}
      </div>

      <style jsx>{`
        .email-editor {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          padding: 1.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
        }

        .editor-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding-bottom: 1rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .recipient-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .recipient, .cc {
          display: flex;
          gap: 0.5rem;
          font-size: 0.875rem;
        }

        .label {
          color: #64748b;
          font-weight: 500;
        }

        .value {
          color: #1e293b;
        }

        .status-info {
          display: flex;
          gap: 1rem;
          align-items: center;
        }

        .status {
          padding: 0.25rem 0.75rem;
          font-size: 0.75rem;
          font-weight: 500;
          border-radius: 9999px;
          text-transform: capitalize;
        }

        .status-draft { background: #e2e8f0; color: #475569; }
        .status-pending_approval { background: #fef3c7; color: #92400e; }
        .status-approved { background: #dcfce7; color: #166534; }
        .status-scheduled { background: #dbeafe; color: #1e40af; }
        .status-sent { background: #ede9fe; color: #5b21b6; }

        .confidence {
          font-size: 0.75rem;
          color: #64748b;
        }

        .subject-row {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .subject-row label {
          font-weight: 500;
          color: #64748b;
        }

        .subject-row input {
          flex: 1;
          padding: 0.5rem;
          font-size: 1rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
        }

        .subject-text {
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
        }

        .body-section {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .body-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .body-header span {
          font-weight: 500;
          color: #64748b;
        }

        .toggle-btn {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          background: #f1f5f9;
          border: 1px solid #e2e8f0;
          border-radius: 0.25rem;
          cursor: pointer;
        }

        textarea {
          padding: 0.75rem;
          font-family: inherit;
          font-size: 0.875rem;
          line-height: 1.5;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          resize: vertical;
        }

        .body-preview {
          padding: 1rem;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          min-height: 200px;
        }

        .body-preview pre {
          margin: 0;
          white-space: pre-wrap;
          font-family: inherit;
          font-size: 0.875rem;
          line-height: 1.6;
        }

        .tokens-section {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          background: #f0fdf4;
          border-radius: 0.375rem;
        }

        .tokens {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .token {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          background: #dcfce7;
          color: #166534;
          border-radius: 0.25rem;
        }

        .scheduler {
          padding: 1rem;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
        }

        .scheduler h4 {
          margin: 0 0 1rem 0;
        }

        .schedule-inputs {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .schedule-inputs input {
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
        }

        .schedule-actions {
          display: flex;
          gap: 0.5rem;
        }

        .actions {
          display: flex;
          gap: 0.5rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .actions button {
          padding: 0.5rem 1rem;
          font-weight: 500;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-primary {
          background: #3b82f6;
          color: white;
        }
        .btn-primary:hover { background: #2563eb; }

        .btn-secondary {
          background: #f1f5f9;
          color: #475569;
        }
        .btn-secondary:hover { background: #e2e8f0; }

        .btn-success {
          background: #22c55e;
          color: white;
        }
        .btn-success:hover { background: #16a34a; }

        .btn-danger {
          background: #ef4444;
          color: white;
        }
        .btn-danger:hover { background: #dc2626; }
      `}</style>
    </div>
  );
}
