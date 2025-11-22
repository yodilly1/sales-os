'use client';

/**
 * CalendarIntegrationCard Component
 *
 * Displays the status of a calendar integration with options
 * to sync, configure, or disconnect.
 */

import React, { useState } from 'react';
import { CalendarIntegration, CalendarProvider, SyncStatus } from './types';

interface CalendarIntegrationCardProps {
  integration: CalendarIntegration;
  onSync?: (integrationId: string) => Promise<void>;
  onDisconnect?: (integrationId: string) => Promise<void>;
  onConfigure?: (integrationId: string) => void;
}

const providerConfig: Record<CalendarProvider, { name: string; icon: string; color: string }> = {
  google: {
    name: 'Google Calendar',
    icon: '📅',
    color: '#4285F4',
  },
  outlook: {
    name: 'Microsoft Outlook',
    icon: '📆',
    color: '#0078D4',
  },
};

const statusConfig: Record<SyncStatus, { label: string; color: string; bgColor: string }> = {
  active: { label: 'Connected', color: '#059669', bgColor: '#D1FAE5' },
  paused: { label: 'Paused', color: '#D97706', bgColor: '#FEF3C7' },
  error: { label: 'Error', color: '#DC2626', bgColor: '#FEE2E2' },
  disconnected: { label: 'Disconnected', color: '#6B7280', bgColor: '#F3F4F6' },
};

export function CalendarIntegrationCard({
  integration,
  onSync,
  onDisconnect,
  onConfigure,
}: CalendarIntegrationCardProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  const provider = providerConfig[integration.provider];
  const status = statusConfig[integration.status];

  const handleSync = async () => {
    if (!onSync || isSyncing) return;
    setIsSyncing(true);
    try {
      await onSync(integration.id);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!onDisconnect || isDisconnecting) return;
    if (!confirm('Are you sure you want to disconnect this calendar?')) return;
    setIsDisconnecting(true);
    try {
      await onDisconnect(integration.id);
    } finally {
      setIsDisconnecting(false);
    }
  };

  const formatLastSync = (date?: Date) => {
    if (!date) return 'Never';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <div className="calendar-integration-card">
      <div className="card-header">
        <div className="provider-info">
          <span className="provider-icon">{provider.icon}</span>
          <div>
            <h3 className="provider-name">{provider.name}</h3>
            <span
              className="status-badge"
              style={{
                color: status.color,
                backgroundColor: status.bgColor,
              }}
            >
              {status.label}
            </span>
          </div>
        </div>
      </div>

      <div className="card-body">
        <div className="sync-info">
          <span className="sync-label">Last synced:</span>
          <span className="sync-time">{formatLastSync(integration.lastSyncAt)}</span>
        </div>

        {integration.calendarId && (
          <div className="calendar-info">
            <span className="calendar-label">Calendar:</span>
            <span className="calendar-name">{integration.calendarId}</span>
          </div>
        )}
      </div>

      <div className="card-actions">
        <button
          className="btn btn-secondary"
          onClick={handleSync}
          disabled={isSyncing || integration.status === 'disconnected'}
        >
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </button>

        {onConfigure && (
          <button
            className="btn btn-secondary"
            onClick={() => onConfigure(integration.id)}
            disabled={integration.status === 'disconnected'}
          >
            Configure
          </button>
        )}

        <button
          className="btn btn-danger"
          onClick={handleDisconnect}
          disabled={isDisconnecting}
        >
          {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
        </button>
      </div>

      <style jsx>{`
        .calendar-integration-card {
          background: white;
          border: 1px solid #E5E7EB;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
        }

        .provider-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .provider-icon {
          font-size: 32px;
        }

        .provider-name {
          font-size: 16px;
          font-weight: 600;
          color: #111827;
          margin: 0 0 4px 0;
        }

        .status-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 9999px;
          font-size: 12px;
          font-weight: 500;
        }

        .card-body {
          margin-bottom: 16px;
        }

        .sync-info,
        .calendar-info {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #F3F4F6;
        }

        .sync-label,
        .calendar-label {
          color: #6B7280;
          font-size: 14px;
        }

        .sync-time,
        .calendar-name {
          color: #111827;
          font-size: 14px;
          font-weight: 500;
        }

        .card-actions {
          display: flex;
          gap: 8px;
        }

        .btn {
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #F3F4F6;
          color: #374151;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #E5E7EB;
        }

        .btn-danger {
          background: #FEE2E2;
          color: #DC2626;
        }

        .btn-danger:hover:not(:disabled) {
          background: #FECACA;
        }
      `}</style>
    </div>
  );
}
