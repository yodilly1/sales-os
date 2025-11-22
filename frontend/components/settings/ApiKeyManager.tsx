'use client';

import { useState } from 'react';
import type { ApiKey, ApiKeyCreate } from '@/lib/types/settings';
import { API_KEY_SCOPES } from '@/lib/api/settings';

interface ApiKeyManagerProps {
  apiKeys: ApiKey[];
  onCreateKey: (data: ApiKeyCreate) => Promise<{ key: ApiKey; secret: string }>;
  onRevokeKey: (keyId: string) => Promise<void>;
  onToggleKey: (keyId: string, isActive: boolean) => Promise<void>;
}

interface CreateKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ApiKeyCreate) => Promise<void>;
}

function CreateKeyModal({ isOpen, onClose, onSubmit }: CreateKeyModalProps) {
  const [name, setName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  const [expiresIn, setExpiresIn] = useState<string>('never');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || selectedScopes.length === 0) return;

    setIsSubmitting(true);
    try {
      let expiresAt: string | undefined;
      if (expiresIn !== 'never') {
        const days = parseInt(expiresIn, 10);
        const date = new Date();
        date.setDate(date.getDate() + days);
        expiresAt = date.toISOString();
      }

      await onSubmit({
        name: name.trim(),
        scopes: selectedScopes,
        expiresAt,
      });
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleScope = (scopeId: string) => {
    setSelectedScopes((prev) =>
      prev.includes(scopeId)
        ? prev.filter((s) => s !== scopeId)
        : [...prev, scopeId]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Create API Key</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Key Name */}
            <div className="mb-4">
              <label htmlFor="keyName" className="block text-sm font-medium text-gray-700 mb-1">
                Key Name
              </label>
              <input
                id="keyName"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Production API Key"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Expiration */}
            <div className="mb-4">
              <label htmlFor="expiration" className="block text-sm font-medium text-gray-700 mb-1">
                Expiration
              </label>
              <select
                id="expiration"
                value={expiresIn}
                onChange={(e) => setExpiresIn(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="never">Never expires</option>
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90">90 days</option>
                <option value="180">6 months</option>
                <option value="365">1 year</option>
              </select>
            </div>

            {/* Scopes */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Permissions
              </label>
              <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-md p-3">
                {API_KEY_SCOPES.map((scope) => (
                  <label
                    key={scope.id}
                    className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedScopes.includes(scope.id)}
                      onChange={() => toggleScope(scope.id)}
                      className="mt-0.5 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-900">{scope.label}</span>
                      <p className="text-xs text-gray-500">{scope.description}</p>
                    </div>
                  </label>
                ))}
              </div>
              {selectedScopes.length === 0 && (
                <p className="text-sm text-red-600 mt-1">Select at least one permission</p>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !name.trim() || selectedScopes.length === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Creating...' : 'Create Key'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

interface SecretDisplayModalProps {
  isOpen: boolean;
  secret: string;
  keyName: string;
  onClose: () => void;
}

function SecretDisplayModal({ isOpen, secret, keyName, onClose }: SecretDisplayModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(secret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">API Key Created</h2>
              <p className="text-sm text-gray-500">{keyName}</p>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-sm text-yellow-800">
                <strong>Important:</strong> Copy your API key now. You won&apos;t be able to see it again!
              </p>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">Your API Key</label>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 bg-gray-100 rounded-md text-sm font-mono text-gray-900 break-all">
                {secret}
              </code>
              <button
                onClick={handleCopy}
                className="flex-shrink-0 px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
              >
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ApiKeyManager({
  apiKeys,
  onCreateKey,
  onRevokeKey,
  onToggleKey,
}: ApiKeyManagerProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeySecret, setNewKeySecret] = useState<{ name: string; secret: string } | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const handleCreateKey = async (data: ApiKeyCreate) => {
    const result = await onCreateKey(data);
    setNewKeySecret({ name: data.name, secret: result.secret });
    setShowCreateModal(false);
  };

  const handleRevokeKey = async (keyId: string, keyName: string) => {
    if (!confirm(`Are you sure you want to revoke "${keyName}"? This action cannot be undone.`)) {
      return;
    }
    setRevokingId(keyId);
    try {
      await onRevokeKey(keyId);
    } finally {
      setRevokingId(null);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const isExpired = (expiresAt?: string) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">API Keys</h3>
          <p className="text-sm text-gray-500 mt-1">
            Manage API keys for programmatic access to Sales OS
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create New Key
        </button>
      </div>

      {/* API Keys List */}
      {apiKeys.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <h4 className="text-lg font-medium text-gray-900 mb-1">No API keys yet</h4>
          <p className="text-sm text-gray-500 mb-4">Create your first API key to get started</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create API Key
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {apiKeys.map((key) => {
            const expired = isExpired(key.expiresAt);
            return (
              <div
                key={key.id}
                className={`bg-white border rounded-lg p-4 ${
                  !key.isActive || expired ? 'border-gray-200 bg-gray-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900">{key.name}</h4>
                      {!key.isActive && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-gray-200 text-gray-600 rounded">
                          Disabled
                        </span>
                      )}
                      {expired && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
                          Expired
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-2">
                      <code className="px-2 py-0.5 bg-gray-100 rounded text-xs font-mono">
                        {key.prefix}...
                      </code>
                      <span>Created {formatDate(key.createdAt)}</span>
                      {key.lastUsedAt && <span>Last used {formatDate(key.lastUsedAt)}</span>}
                      {key.expiresAt && (
                        <span className={expired ? 'text-red-600' : ''}>
                          {expired ? 'Expired' : 'Expires'} {formatDate(key.expiresAt)}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {key.scopes.map((scope) => (
                        <span
                          key={scope}
                          className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                        >
                          {scope}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onToggleKey(key.id, !key.isActive)}
                      className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                        key.isActive
                          ? 'text-yellow-700 bg-yellow-50 hover:bg-yellow-100'
                          : 'text-green-700 bg-green-50 hover:bg-green-100'
                      }`}
                    >
                      {key.isActive ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => handleRevokeKey(key.id, key.name)}
                      disabled={revokingId === key.id}
                      className="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-50 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {revokingId === key.id ? 'Revoking...' : 'Revoke'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Key Modal */}
      <CreateKeyModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateKey}
      />

      {/* Secret Display Modal */}
      {newKeySecret && (
        <SecretDisplayModal
          isOpen={true}
          secret={newKeySecret.secret}
          keyName={newKeySecret.name}
          onClose={() => setNewKeySecret(null)}
        />
      )}
    </div>
  );
}

export default ApiKeyManager;
