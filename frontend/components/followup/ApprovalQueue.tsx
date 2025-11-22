'use client';

import React, { useState, useEffect } from 'react';
import { FollowUp, FollowUpStatus } from './types';
import { FollowUpCard } from './FollowUpCard';

interface ApprovalQueueProps {
  onApprove: (followUp: FollowUp, modifications?: Record<string, unknown>) => void;
  onReject: (followUp: FollowUp, reason?: string) => void;
  onBulkApprove?: (followUps: FollowUp[]) => void;
  className?: string;
}

export function ApprovalQueue({
  onApprove,
  onReject,
  onBulkApprove,
  className = '',
}: ApprovalQueueProps) {
  const [pendingItems, setPendingItems] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectDialog, setShowRejectDialog] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingApprovals();
  }, []);

  async function fetchPendingApprovals() {
    try {
      setLoading(true);
      const response = await fetch('/api/followup/approvals/pending');
      if (!response.ok) throw new Error('Failed to fetch pending approvals');

      const data = await response.json();
      setPendingItems(data.items);
    } catch (error) {
      console.error('Error fetching pending approvals:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleSelect(id: string) {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  }

  function handleSelectAll() {
    if (selectedIds.size === pendingItems.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(pendingItems.map((item) => item.id)));
    }
  }

  function handleApprove(followUp: FollowUp) {
    onApprove(followUp);
    setPendingItems((items) => items.filter((item) => item.id !== followUp.id));
    setSelectedIds((ids) => {
      const newIds = new Set(ids);
      newIds.delete(followUp.id);
      return newIds;
    });
  }

  function handleReject(followUp: FollowUp) {
    onReject(followUp, rejectReason);
    setPendingItems((items) => items.filter((item) => item.id !== followUp.id));
    setShowRejectDialog(null);
    setRejectReason('');
  }

  function handleBulkApprove() {
    const selectedItems = pendingItems.filter((item) => selectedIds.has(item.id));
    onBulkApprove?.(selectedItems);
    setPendingItems((items) => items.filter((item) => !selectedIds.has(item.id)));
    setSelectedIds(new Set());
  }

  if (loading) {
    return (
      <div className={`approval-queue ${className}`}>
        <div className="loading">Loading pending approvals...</div>
      </div>
    );
  }

  return (
    <div className={`approval-queue ${className}`}>
      {/* Header */}
      <div className="header">
        <div className="header-info">
          <h2>Approval Queue</h2>
          <span className="count">{pendingItems.length} pending</span>
        </div>

        {pendingItems.length > 0 && (
          <div className="header-actions">
            <label className="select-all">
              <input
                type="checkbox"
                checked={selectedIds.size === pendingItems.length}
                onChange={handleSelectAll}
              />
              Select all
            </label>

            {selectedIds.size > 0 && onBulkApprove && (
              <button onClick={handleBulkApprove} className="bulk-approve-btn">
                Approve {selectedIds.size} selected
              </button>
            )}
          </div>
        )}
      </div>

      {/* Empty state */}
      {pendingItems.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">✓</div>
          <h3>All caught up!</h3>
          <p>No follow-ups are waiting for approval</p>
        </div>
      )}

      {/* Items list */}
      <div className="items-list">
        {pendingItems.map((item) => (
          <div
            key={item.id}
            className={`approval-item ${expandedId === item.id ? 'expanded' : ''}`}
          >
            <div className="item-header">
              <input
                type="checkbox"
                checked={selectedIds.has(item.id)}
                onChange={() => handleSelect(item.id)}
              />

              <FollowUpCard
                followUp={item}
                compact
                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
              />

              <div className="quick-actions">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleApprove(item);
                  }}
                  className="approve-btn"
                  title="Approve"
                >
                  ✓
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowRejectDialog(item.id);
                  }}
                  className="reject-btn"
                  title="Reject"
                >
                  ✕
                </button>
              </div>
            </div>

            {expandedId === item.id && (
              <div className="item-details">
                <ApprovalDetails
                  followUp={item}
                  onApprove={() => handleApprove(item)}
                  onReject={() => setShowRejectDialog(item.id)}
                />
              </div>
            )}

            {showRejectDialog === item.id && (
              <div className="reject-dialog">
                <h4>Reject Follow-up</h4>
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Reason for rejection (optional)"
                  rows={3}
                />
                <div className="dialog-actions">
                  <button
                    onClick={() => handleReject(item)}
                    className="btn-reject"
                  >
                    Confirm Reject
                  </button>
                  <button
                    onClick={() => {
                      setShowRejectDialog(null);
                      setRejectReason('');
                    }}
                    className="btn-cancel"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <style jsx>{`
        .approval-queue {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 1rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .header-info {
          display: flex;
          align-items: baseline;
          gap: 0.75rem;
        }

        .header-info h2 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .count {
          padding: 0.25rem 0.5rem;
          font-size: 0.75rem;
          font-weight: 500;
          color: #f59e0b;
          background: #fef3c7;
          border-radius: 9999px;
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .select-all {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: #64748b;
          cursor: pointer;
        }

        .bulk-approve-btn {
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          font-weight: 500;
          color: white;
          background: #22c55e;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }

        .bulk-approve-btn:hover {
          background: #16a34a;
        }

        .loading {
          padding: 3rem;
          text-align: center;
          color: #64748b;
        }

        .empty-state {
          padding: 4rem 2rem;
          text-align: center;
        }

        .empty-icon {
          width: 4rem;
          height: 4rem;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 2rem;
          color: #22c55e;
          background: #dcfce7;
          border-radius: 9999px;
          margin-bottom: 1rem;
        }

        .empty-state h3 {
          margin: 0 0 0.5rem 0;
          color: #1e293b;
        }

        .empty-state p {
          margin: 0;
          color: #64748b;
        }

        .items-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .approval-item {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          overflow: hidden;
        }

        .approval-item.expanded {
          border-color: #3b82f6;
        }

        .item-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
        }

        .item-header > input {
          flex-shrink: 0;
        }

        .quick-actions {
          display: flex;
          gap: 0.25rem;
          flex-shrink: 0;
        }

        .quick-actions button {
          width: 2rem;
          height: 2rem;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 0.25rem;
          cursor: pointer;
          font-size: 0.875rem;
        }

        .approve-btn {
          background: #dcfce7;
          color: #166534;
        }

        .approve-btn:hover {
          background: #bbf7d0;
        }

        .reject-btn {
          background: #fee2e2;
          color: #991b1b;
        }

        .reject-btn:hover {
          background: #fecaca;
        }

        .item-details {
          padding: 1rem;
          border-top: 1px solid #e2e8f0;
          background: #f8fafc;
        }

        .reject-dialog {
          padding: 1rem;
          border-top: 1px solid #e2e8f0;
          background: #fff7ed;
        }

        .reject-dialog h4 {
          margin: 0 0 0.75rem 0;
          font-size: 0.875rem;
          color: #9a3412;
        }

        .reject-dialog textarea {
          width: 100%;
          padding: 0.5rem;
          border: 1px solid #fed7aa;
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
          font-size: 0.875rem;
          border: none;
          border-radius: 0.25rem;
          cursor: pointer;
        }

        .btn-reject {
          background: #ef4444;
          color: white;
        }

        .btn-cancel {
          background: #f1f5f9;
          color: #475569;
        }
      `}</style>
    </div>
  );
}

interface ApprovalDetailsProps {
  followUp: FollowUp;
  onApprove: () => void;
  onReject: () => void;
}

function ApprovalDetails({ followUp, onApprove, onReject }: ApprovalDetailsProps) {
  return (
    <div className="approval-details">
      <div className="details-content">
        <div className="detail-row">
          <span className="label">Type:</span>
          <span className="value">{followUp.type.replace('_', ' ')}</span>
        </div>
        <div className="detail-row">
          <span className="label">Priority:</span>
          <span className="value">{followUp.priority}</span>
        </div>
        <div className="detail-row">
          <span className="label">Created:</span>
          <span className="value">{new Date(followUp.createdAt).toLocaleString()}</span>
        </div>
        {followUp.spicedAnalysisId && (
          <div className="detail-row">
            <span className="label">From SPICED Analysis:</span>
            <span className="value">{followUp.spicedAnalysisId}</span>
          </div>
        )}
      </div>

      <div className="details-actions">
        <button onClick={onApprove} className="btn-approve">
          Approve
        </button>
        <button onClick={onReject} className="btn-reject">
          Reject
        </button>
      </div>

      <style jsx>{`
        .approval-details {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
        }

        .details-content {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .detail-row {
          display: flex;
          gap: 0.5rem;
          font-size: 0.875rem;
        }

        .label {
          color: #64748b;
        }

        .value {
          color: #1e293b;
          text-transform: capitalize;
        }

        .details-actions {
          display: flex;
          gap: 0.5rem;
        }

        .details-actions button {
          padding: 0.5rem 1rem;
          font-weight: 500;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }

        .btn-approve {
          background: #22c55e;
          color: white;
        }

        .btn-reject {
          background: #ef4444;
          color: white;
        }
      `}</style>
    </div>
  );
}
