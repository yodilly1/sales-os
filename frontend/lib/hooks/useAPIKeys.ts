/**
 * React hook for API key management
 */

'use client';

import { useState, useCallback } from 'react';
import type { APIKey, APIKeyCreated, CreateAPIKeyData } from '../../types/auth';
import { createAPIKey, listAPIKeys, revokeAPIKey } from '../auth';

interface UseAPIKeysReturn {
  apiKeys: APIKey[];
  isLoading: boolean;
  error: string | null;
  fetchAPIKeys: () => Promise<void>;
  createKey: (data: CreateAPIKeyData) => Promise<APIKeyCreated>;
  revokeKey: (keyId: string) => Promise<void>;
}

/**
 * Hook for managing API keys
 */
export function useAPIKeys(): UseAPIKeysReturn {
  const [apiKeys, setAPIKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAPIKeys = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const keys = await listAPIKeys();
      setAPIKeys(keys);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch API keys';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createKey = useCallback(async (data: CreateAPIKeyData): Promise<APIKeyCreated> => {
    setIsLoading(true);
    setError(null);

    try {
      const newKey = await createAPIKey(data);
      // Add to local state (without the raw key for security)
      setAPIKeys((prev) => [
        {
          id: newKey.id,
          name: newKey.name,
          key_prefix: newKey.key_prefix,
          scopes: newKey.scopes,
          is_active: newKey.is_active,
          expires_at: newKey.expires_at,
          last_used_at: newKey.last_used_at,
          created_at: newKey.created_at,
        },
        ...prev,
      ]);
      return newKey;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create API key';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const revokeKey = useCallback(async (keyId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await revokeAPIKey(keyId);
      // Remove from local state
      setAPIKeys((prev) => prev.filter((key) => key.id !== keyId));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to revoke API key';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    apiKeys,
    isLoading,
    error,
    fetchAPIKeys,
    createKey,
    revokeKey,
  };
}
