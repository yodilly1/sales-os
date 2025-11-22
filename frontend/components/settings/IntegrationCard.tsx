'use client';

import { useState } from 'react';
import type { Integration } from '@/lib/types/settings';

interface IntegrationCardProps {
  integration: Integration;
  onConnect: (type: Integration['type']) => Promise<void>;
  onDisconnect: (type: Integration['type']) => Promise<void>;
  onSync: (type: Integration['type']) => Promise<void>;
}

const integrationLogos: Record<Integration['type'], React.ReactNode> = {
  hubspot: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.164 7.93V5.084a2.198 2.198 0 001.267-1.984 2.21 2.21 0 00-2.212-2.212 2.21 2.21 0 00-2.212 2.212c0 .864.501 1.61 1.227 1.974v2.858a5.189 5.189 0 00-2.502 1.18l-6.747-5.242a2.333 2.333 0 00.072-.563A2.322 2.322 0 004.74.889a2.322 2.322 0 00-2.318 2.318 2.322 2.322 0 002.318 2.318c.393 0 .762-.103 1.088-.275l6.648 5.167a5.204 5.204 0 00-.502 2.227c0 .815.188 1.585.52 2.274l-2.091 2.091a2.104 2.104 0 00-.643-.107 2.105 2.105 0 00-2.106 2.105 2.105 2.105 0 002.106 2.106 2.105 2.105 0 002.105-2.106c0-.232-.04-.454-.108-.664l2.063-2.063a5.207 5.207 0 003.38 1.235 5.233 5.233 0 005.233-5.233 5.233 5.233 0 00-5.233-5.233 5.27 5.27 0 00-1.036.107z" />
    </svg>
  ),
  avoma: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  ),
  salesforce: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
      <path d="M10.006 5.415a4.195 4.195 0 013.045-1.306c1.56 0 2.954.9 3.663 2.3a5.08 5.08 0 011.985-.405c2.79 0 5.049 2.26 5.049 5.049s-2.26 5.049-5.049 5.049a5.04 5.04 0 01-1.551-.243 3.59 3.59 0 01-3.143 1.858 3.57 3.57 0 01-1.787-.477 4.31 4.31 0 01-3.87 2.423c-2.093 0-3.904-1.482-4.267-3.537a4.05 4.05 0 01-.532.036c-2.24 0-4.054-1.814-4.054-4.054s1.814-4.054 4.054-4.054c.37 0 .729.05 1.069.143a4.199 4.199 0 015.388-2.782z" />
    </svg>
  ),
  gong: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="10" />
    </svg>
  ),
  zoom: (
    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
      <path d="M4.5 4.5h10.8c2.5 0 4.2 1.7 4.2 4.2v6.6c0 2.5-1.7 4.2-4.2 4.2H4.5c-2.5 0-4.2-1.7-4.2-4.2V8.7c0-2.5 1.7-4.2 4.2-4.2zm13.5 7.5l4.8 3V9l-4.8 3z" />
    </svg>
  ),
};

const statusColors: Record<Integration['status'], { bg: string; text: string; dot: string }> = {
  connected: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  disconnected: { bg: 'bg-gray-50', text: 'text-gray-600', dot: 'bg-gray-400' },
  error: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
  pending: { bg: 'bg-yellow-50', text: 'text-yellow-700', dot: 'bg-yellow-500' },
};

const statusLabels: Record<Integration['status'], string> = {
  connected: 'Connected',
  disconnected: 'Not Connected',
  error: 'Connection Error',
  pending: 'Connecting...',
};

export function IntegrationCard({
  integration,
  onConnect,
  onDisconnect,
  onSync,
}: IntegrationCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const statusStyle = statusColors[integration.status];

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      await onConnect(integration.type);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm(`Are you sure you want to disconnect ${integration.name}?`)) {
      return;
    }
    setIsLoading(true);
    try {
      await onDisconnect(integration.type);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await onSync(integration.type);
    } finally {
      setIsSyncing(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-4">
        {/* Logo */}
        <div className="flex-shrink-0 w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
          {integrationLogos[integration.type]}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{integration.name}</h3>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusStyle.bg} ${statusStyle.text}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${statusStyle.dot}`} />
              {statusLabels[integration.status]}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-3">{integration.description}</p>

          {/* Error message */}
          {integration.status === 'error' && integration.errorMessage && (
            <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {integration.errorMessage}
            </div>
          )}

          {/* Connection info */}
          {integration.status === 'connected' && (
            <div className="text-xs text-gray-500 space-y-1 mb-3">
              <p>Connected: {formatDate(integration.connectedAt)}</p>
              <p>Last synced: {formatDate(integration.lastSyncAt)}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2">
            {integration.status === 'connected' ? (
              <>
                <button
                  onClick={handleSync}
                  disabled={isSyncing}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSyncing ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Syncing...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Sync Now
                    </>
                  )}
                </button>
                <button
                  onClick={handleDisconnect}
                  disabled={isLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? 'Disconnecting...' : 'Disconnect'}
                </button>
              </>
            ) : (
              <button
                onClick={handleConnect}
                disabled={isLoading || integration.status === 'pending'}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading || integration.status === 'pending' ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Connecting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    Connect
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default IntegrationCard;
