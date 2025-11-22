'use client';

import { useState, useEffect } from 'react';
import { SettingsSection, IntegrationCard } from '@/components/settings';
import type { Integration } from '@/lib/types/settings';
import {
  getIntegrations,
  connectIntegration,
  disconnectIntegration,
  syncIntegration,
} from '@/lib/api/settings';

const availableIntegrations: Omit<Integration, 'id' | 'status'>[] = [
  {
    type: 'hubspot',
    name: 'HubSpot',
    description: 'Sync contacts, companies, and deals with your HubSpot CRM',
  },
  {
    type: 'avoma',
    name: 'Avoma',
    description: 'Import call recordings and transcripts automatically',
  },
  {
    type: 'salesforce',
    name: 'Salesforce',
    description: 'Connect to Salesforce for CRM data synchronization',
  },
  {
    type: 'gong',
    name: 'Gong',
    description: 'Import conversation intelligence data from Gong',
  },
  {
    type: 'zoom',
    name: 'Zoom',
    description: 'Automatically import Zoom meeting recordings',
  },
];

export default function IntegrationsSettingsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      const data = await getIntegrations();
      // Merge with available integrations to show all options
      const mergedIntegrations = availableIntegrations.map((available) => {
        const existing = data.find((i) => i.type === available.type);
        return existing || {
          ...available,
          id: available.type,
          status: 'disconnected' as const,
        };
      });
      setIntegrations(mergedIntegrations);
    } catch (err) {
      setError('Failed to load integrations');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (type: Integration['type']) => {
    try {
      setIntegrations((prev) =>
        prev.map((i) =>
          i.type === type ? { ...i, status: 'pending' } : i
        )
      );

      const { authUrl } = await connectIntegration(type);
      // Redirect to OAuth flow
      window.location.href = authUrl;
    } catch (err) {
      setError(`Failed to connect ${type}`);
      setIntegrations((prev) =>
        prev.map((i) =>
          i.type === type ? { ...i, status: 'disconnected' } : i
        )
      );
      console.error(err);
    }
  };

  const handleDisconnect = async (type: Integration['type']) => {
    try {
      await disconnectIntegration(type);
      setIntegrations((prev) =>
        prev.map((i) =>
          i.type === type
            ? {
                ...i,
                status: 'disconnected',
                connectedAt: undefined,
                lastSyncAt: undefined,
              }
            : i
        )
      );
    } catch (err) {
      setError(`Failed to disconnect ${type}`);
      console.error(err);
    }
  };

  const handleSync = async (type: Integration['type']) => {
    try {
      await syncIntegration(type);
      setIntegrations((prev) =>
        prev.map((i) =>
          i.type === type
            ? { ...i, lastSyncAt: new Date().toISOString() }
            : i
        )
      );
    } catch (err) {
      setError(`Failed to sync ${type}`);
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const connectedIntegrations = integrations.filter(
    (i) => i.status === 'connected'
  );
  const availableToConnect = integrations.filter(
    (i) => i.status !== 'connected'
  );

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Connected Integrations */}
      {connectedIntegrations.length > 0 && (
        <SettingsSection
          title="Connected"
          description="Integrations currently connected to your account"
        >
          <div className="space-y-4">
            {connectedIntegrations.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
                onSync={handleSync}
              />
            ))}
          </div>
        </SettingsSection>
      )}

      {/* Available Integrations */}
      <SettingsSection
        title="Available Integrations"
        description="Connect external services to enhance Sales OS"
      >
        {availableToConnect.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-gray-900 mb-1">All set!</h4>
            <p className="text-sm text-gray-500">
              All available integrations are connected
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {availableToConnect.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
                onSync={handleSync}
              />
            ))}
          </div>
        )}
      </SettingsSection>

      {/* Integration Help */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h4 className="font-medium text-blue-900">Need help with integrations?</h4>
            <p className="text-sm text-blue-700 mt-1">
              Visit our{' '}
              <a href="/docs/integrations" className="underline hover:no-underline">
                integration documentation
              </a>{' '}
              for setup guides and troubleshooting tips.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
