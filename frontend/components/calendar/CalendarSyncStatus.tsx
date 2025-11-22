'use client';

/**
 * CalendarSyncStatus Component
 *
 * Displays sync status and provides sync controls for calendar integrations.
 */

import React from 'react';
import { SyncStatus, SyncResult } from './types';

interface CalendarSyncStatusProps {
  status: SyncStatus;
  lastSyncAt?: Date;
  lastSyncResult?: SyncResult;
  isSyncing?: boolean;
  onSync?: () => Promise<void>;
}

const statusConfig: Record<
  SyncStatus,
  { label: string; color: string; bgColor: string; icon: string }
> = {
  active: {
    label: 'Syncing',
    color: '#059669',
    bgColor: '#D1FAE5',
    icon: '✓',
  },
  paused: {
    label: 'Paused',
    color: '#D97706',
    bgColor: '#FEF3C7',
    icon: '⏸',
  },
  error: {
    label: 'Sync Error',
    color: '#DC2626',
    bgColor: '#FEE2E2',
    icon: '⚠',
  },
  disconnected: {
    label: 'Disconnected',
    color: '#6B7280',
    bgColor: '#F3F4F6',
    icon: '○',
  },
};

export function CalendarSyncStatus({
  status,
  lastSyncAt,
  lastSyncResult,
  isSyncing = false,
  onSync,
}: CalendarSyncStatusProps) {
  const config = statusConfig[status];

  const formatLastSync = (date?: Date) => {
    if (!date) return 'Never synced';

    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  };

  return (
    <div className="sync-status">
      <div className="status-header">
        <div
          className="status-badge"
          style={{
            color: config.color,
            backgroundColor: config.bgColor,
          }}
        >
          <span className="status-icon">{isSyncing ? '↻' : config.icon}</span>
          <span className="status-label">
            {isSyncing ? 'Syncing...' : config.label}
          </span>
        </div>

        {onSync && status !== 'disconnected' && (
          <button
            className="sync-button"
            onClick={onSync}
            disabled={isSyncing}
            title="Sync now"
          >
            {isSyncing ? (
              <span className="spinning">↻</span>
            ) : (
              <span>↻</span>
            )}
          </button>
        )}
      </div>

      <div className="sync-details">
        <span className="last-sync">
          Last synced: {formatLastSync(lastSyncAt)}
        </span>

        {lastSyncResult && (
          <div className="sync-result">
            <div className="result-item">
              <span className="result-value">{lastSyncResult.eventsSynced}</span>
              <span className="result-label">Events</span>
            </div>
            <div className="result-item">
              <span className="result-value">{lastSyncResult.eventsCreated}</span>
              <span className="result-label">New</span>
            </div>
            <div className="result-item">
              <span className="result-value">{lastSyncResult.eventsUpdated}</span>
              <span className="result-label">Updated</span>
            </div>
          </div>
        )}

        {lastSyncResult && lastSyncResult.errors.length > 0 && (
          <div className="sync-errors">
            <span className="error-title">Sync Errors:</span>
            <ul className="error-list">
              {lastSyncResult.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <style jsx>{`
        .sync-status {
          padding: 12px;
          background: #FAFAFA;
          border-radius: 8px;
        }

        .status-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 9999px;
          font-size: 13px;
          font-weight: 500;
        }

        .status-icon {
          font-size: 14px;
        }

        .sync-button {
          width: 28px;
          height: 28px;
          border: none;
          background: #E5E7EB;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          color: #6B7280;
          transition: all 0.2s;
        }

        .sync-button:hover:not(:disabled) {
          background: #D1D5DB;
          color: #374151;
        }

        .sync-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
          display: inline-block;
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .sync-details {
          font-size: 12px;
        }

        .last-sync {
          color: #6B7280;
        }

        .sync-result {
          display: flex;
          gap: 16px;
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #E5E7EB;
        }

        .result-item {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .result-value {
          font-size: 16px;
          font-weight: 600;
          color: #111827;
        }

        .result-label {
          font-size: 11px;
          color: #6B7280;
          text-transform: uppercase;
        }

        .sync-errors {
          margin-top: 8px;
          padding: 8px;
          background: #FEE2E2;
          border-radius: 6px;
        }

        .error-title {
          font-weight: 500;
          color: #DC2626;
          display: block;
          margin-bottom: 4px;
        }

        .error-list {
          margin: 0;
          padding-left: 16px;
          color: #991B1B;
        }

        .error-list li {
          margin-bottom: 2px;
        }
      `}</style>
    </div>
  );
}
