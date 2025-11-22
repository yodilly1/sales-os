'use client';

import { useState, useEffect, useCallback } from 'react';
import { GongSettings } from '@/components/integrations/gong/GongSettings';
import { GongSyncStatus } from '@/components/integrations/gong/GongSyncStatus';
import { GongCallList } from '@/components/integrations/gong/GongCallList';
import {
  getGongStatus,
  connectGong,
  disconnectGong,
  triggerGongSync,
  type GongStatusResponse,
  type GongConnectRequest,
} from '@/lib/api/gong';

export default function GongIntegrationPage() {
  const [status, setStatus] = useState<GongStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await getGongStatus();
      setStatus(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleConnect = async (credentials: GongConnectRequest) => {
    try {
      setError(null);
      await connectGong(credentials);
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      throw err;
    }
  };

  const handleDisconnect = async () => {
    try {
      setError(null);
      await disconnectGong();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect');
    }
  };

  const handleSync = async () => {
    try {
      setIsSyncing(true);
      setError(null);
      await triggerGongSync({ sync_type: 'incremental' });
      // Poll for completion
      setTimeout(() => {
        fetchStatus();
        setIsSyncing(false);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start sync');
      setIsSyncing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 w-48 bg-gray-200 rounded mb-4" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  const isConnected = status?.status === 'connected';

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Gong Integration</h1>
        <p className="mt-2 text-gray-600">
          Connect your Gong account to import calls, transcripts, and conversation intelligence.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        {/* Connection Settings */}
        <GongSettings
          isConnected={isConnected}
          workspaceId={status?.workspace_id}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
        />

        {/* Sync Status */}
        {isConnected && (
          <GongSyncStatus
            lastSyncAt={status?.last_sync_at}
            totalCallsSynced={status?.total_calls_synced || 0}
            isSyncing={isSyncing}
            onSync={handleSync}
          />
        )}

        {/* Call List */}
        {isConnected && (
          <GongCallList />
        )}
      </div>
    </div>
  );
}
