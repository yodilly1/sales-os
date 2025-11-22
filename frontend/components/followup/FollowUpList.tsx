'use client';

import React, { useState, useEffect } from 'react';
import { FollowUp, FollowUpStatus, FollowUpType, Priority } from './types';
import { FollowUpCard } from './FollowUpCard';

interface FollowUpListProps {
  prospectId?: string;
  callId?: string;
  initialStatus?: FollowUpStatus;
  initialType?: FollowUpType;
  onSelect?: (followUp: FollowUp) => void;
  onApprove?: (followUp: FollowUp) => void;
  onSchedule?: (followUp: FollowUp, scheduledAt: Date) => void;
  className?: string;
}

interface Filters {
  status?: FollowUpStatus;
  type?: FollowUpType;
  priority?: Priority;
}

export function FollowUpList({
  prospectId,
  callId,
  initialStatus,
  initialType,
  onSelect,
  onApprove,
  onSchedule,
  className = '',
}: FollowUpListProps) {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>({
    status: initialStatus,
    type: initialType,
  });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchFollowUps();
  }, [prospectId, callId, filters]);

  async function fetchFollowUps() {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (prospectId) params.append('prospect_id', prospectId);
      if (callId) params.append('call_id', callId);
      if (filters.status) params.append('status', filters.status);
      if (filters.type) params.append('type', filters.type);

      const response = await fetch(`/api/followup?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch follow-ups');

      const data = await response.json();
      setFollowUps(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }

  function handleFilterChange(key: keyof Filters, value: string | undefined) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  }

  function handleSelectAll() {
    if (selectedIds.size === followUps.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(followUps.map((f) => f.id)));
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

  async function handleBulkApprove() {
    try {
      const response = await fetch('/api/followup/bulk/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          followup_ids: Array.from(selectedIds),
          action: 'approve',
        }),
      });

      if (!response.ok) throw new Error('Failed to approve follow-ups');

      setSelectedIds(new Set());
      fetchFollowUps();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve');
    }
  }

  const statusOptions: FollowUpStatus[] = [
    'draft',
    'pending_approval',
    'approved',
    'scheduled',
    'sent',
    'completed',
    'cancelled',
  ];

  const typeOptions: FollowUpType[] = [
    'email',
    'task',
    'content_recommendation',
    'meeting_suggestion',
  ];

  const priorityOptions: Priority[] = ['low', 'medium', 'high', 'urgent'];

  if (loading) {
    return (
      <div className={`follow-up-list ${className}`}>
        <div className="loading">Loading follow-ups...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`follow-up-list ${className}`}>
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchFollowUps}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className={`follow-up-list ${className}`}>
      {/* Filters */}
      <div className="filters">
        <select
          value={filters.status || ''}
          onChange={(e) => handleFilterChange('status', e.target.value as FollowUpStatus)}
        >
          <option value="">All Statuses</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status.replace('_', ' ')}
            </option>
          ))}
        </select>

        <select
          value={filters.type || ''}
          onChange={(e) => handleFilterChange('type', e.target.value as FollowUpType)}
        >
          <option value="">All Types</option>
          {typeOptions.map((type) => (
            <option key={type} value={type}>
              {type.replace('_', ' ')}
            </option>
          ))}
        </select>

        <select
          value={filters.priority || ''}
          onChange={(e) => handleFilterChange('priority', e.target.value as Priority)}
        >
          <option value="">All Priorities</option>
          {priorityOptions.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
      </div>

      {/* Bulk Actions */}
      {selectedIds.size > 0 && (
        <div className="bulk-actions">
          <span>{selectedIds.size} selected</span>
          <button onClick={handleBulkApprove}>Approve Selected</button>
          <button onClick={() => setSelectedIds(new Set())}>Clear Selection</button>
        </div>
      )}

      {/* Header */}
      <div className="list-header">
        <label>
          <input
            type="checkbox"
            checked={selectedIds.size === followUps.length && followUps.length > 0}
            onChange={handleSelectAll}
          />
          Select All
        </label>
        <span className="count">{followUps.length} follow-ups</span>
      </div>

      {/* List */}
      {followUps.length === 0 ? (
        <div className="empty-state">
          <p>No follow-ups found</p>
          <p>Generate follow-ups from a call to get started</p>
        </div>
      ) : (
        <div className="list-items">
          {followUps.map((followUp) => (
            <FollowUpCard
              key={followUp.id}
              followUp={followUp}
              selected={selectedIds.has(followUp.id)}
              onSelect={() => handleSelect(followUp.id)}
              onClick={() => onSelect?.(followUp)}
              onApprove={onApprove}
              onSchedule={onSchedule}
            />
          ))}
        </div>
      )}

      <style jsx>{`
        .follow-up-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .filters {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .filters select {
          padding: 0.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          background: white;
          font-size: 0.875rem;
        }

        .bulk-actions {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem;
          background: #f0f9ff;
          border-radius: 0.5rem;
        }

        .bulk-actions button {
          padding: 0.5rem 1rem;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }

        .bulk-actions button:hover {
          background: #2563eb;
        }

        .list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0;
          border-bottom: 1px solid #e2e8f0;
        }

        .list-header label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .count {
          font-size: 0.875rem;
          color: #64748b;
        }

        .list-items {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .loading,
        .empty-state {
          padding: 3rem;
          text-align: center;
          color: #64748b;
        }

        .error {
          padding: 2rem;
          text-align: center;
          color: #ef4444;
        }

        .error button {
          margin-top: 1rem;
          padding: 0.5rem 1rem;
          background: #ef4444;
          color: white;
          border: none;
          border-radius: 0.375rem;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}
