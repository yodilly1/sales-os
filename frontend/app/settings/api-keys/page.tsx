'use client';

import { useState, useEffect } from 'react';
import { SettingsSection, ApiKeyManager } from '@/components/settings';
import type { ApiKey, ApiKeyCreate } from '@/lib/types/settings';
import {
  getApiKeys,
  createApiKey,
  revokeApiKey,
  updateApiKey,
} from '@/lib/api/settings';

export default function ApiKeysSettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const data = await getApiKeys();
      setApiKeys(data);
    } catch (err) {
      setError('Failed to load API keys');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateKey = async (data: ApiKeyCreate) => {
    const result = await createApiKey(data);
    setApiKeys((prev) => [result.key, ...prev]);
    return result;
  };

  const handleRevokeKey = async (keyId: string) => {
    await revokeApiKey(keyId);
    setApiKeys((prev) => prev.filter((key) => key.id !== keyId));
  };

  const handleToggleKey = async (keyId: string, isActive: boolean) => {
    const updatedKey = await updateApiKey(keyId, { isActive });
    setApiKeys((prev) =>
      prev.map((key) => (key.id === keyId ? updatedKey : key))
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

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

      {/* API Keys Manager */}
      <SettingsSection
        title="API Keys"
        description="Manage API keys for programmatic access to Sales OS"
      >
        <ApiKeyManager
          apiKeys={apiKeys}
          onCreateKey={handleCreateKey}
          onRevokeKey={handleRevokeKey}
          onToggleKey={handleToggleKey}
        />
      </SettingsSection>

      {/* Security Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex gap-3">
          <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <h4 className="font-medium text-yellow-900">Security Best Practices</h4>
            <ul className="text-sm text-yellow-700 mt-2 space-y-1 list-disc list-inside">
              <li>Never share your API keys or commit them to version control</li>
              <li>Use environment variables to store API keys in your applications</li>
              <li>Create separate keys for different applications or environments</li>
              <li>Regularly rotate your API keys and revoke unused ones</li>
              <li>Use the minimum required scopes for each key</li>
            </ul>
          </div>
        </div>
      </div>

      {/* API Documentation Link */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900">API Documentation</h4>
            <p className="text-sm text-gray-500 mt-1">
              Learn how to use the Sales OS API in your applications
            </p>
          </div>
          <a
            href="/docs/api"
            className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
          >
            View Docs
          </a>
        </div>
      </div>
    </div>
  );
}
