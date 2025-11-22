'use client';

import { useState } from 'react';
import type { GongConnectRequest } from '@/lib/api/gong';

interface GongSettingsProps {
  isConnected: boolean;
  workspaceId?: string | null;
  onConnect: (credentials: GongConnectRequest) => Promise<void>;
  onDisconnect: () => Promise<void>;
}

export function GongSettings({
  isConnected,
  workspaceId,
  onConnect,
  onDisconnect,
}: GongSettingsProps) {
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [accessKey, setAccessKey] = useState('');
  const [accessKeySecret, setAccessKeySecret] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!accessKey.trim() || !accessKeySecret.trim()) {
      setFormError('Both Access Key and Access Key Secret are required');
      return;
    }

    try {
      setIsConnecting(true);
      await onConnect({
        access_key: accessKey.trim(),
        access_key_secret: accessKeySecret.trim(),
      });
      setShowForm(false);
      setAccessKey('');
      setAccessKeySecret('');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect Gong? Your synced data will be preserved.')) {
      return;
    }

    try {
      setIsDisconnecting(true);
      await onDisconnect();
    } finally {
      setIsDisconnecting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Gong</h2>
            <p className="text-sm text-gray-500">Conversation Intelligence Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            isConnected
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {isConnected ? 'Connected' : 'Not Connected'}
          </span>
        </div>
      </div>

      {isConnected ? (
        <div className="space-y-4">
          {workspaceId && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">Workspace ID:</span> {workspaceId}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
            >
              {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
            </button>
          </div>
        </div>
      ) : showForm ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="accessKey" className="block text-sm font-medium text-gray-700 mb-1">
              Access Key
            </label>
            <input
              type="text"
              id="accessKey"
              value={accessKey}
              onChange={(e) => setAccessKey(e.target.value)}
              placeholder="Enter your Gong API Access Key"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="accessKeySecret" className="block text-sm font-medium text-gray-700 mb-1">
              Access Key Secret
            </label>
            <input
              type="password"
              id="accessKeySecret"
              value={accessKeySecret}
              onChange={(e) => setAccessKeySecret(e.target.value)}
              placeholder="Enter your Gong API Access Key Secret"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {formError && (
            <p className="text-sm text-red-600">{formError}</p>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isConnecting}
              className="px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>

          <p className="text-xs text-gray-500">
            You can find your API credentials in Gong under Settings &gt; API.
            <a
              href="https://help.gong.io/hc/en-us/articles/360042154451-Create-an-API-key"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-600 hover:underline ml-1"
            >
              Learn more
            </a>
          </p>
        </form>
      ) : (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Connect your Gong account to automatically import call recordings and transcripts.
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            Connect Gong
          </button>
        </div>
      )}
    </div>
  );
}
