/**
 * React hook for OAuth connection management
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { initiateOAuth, disconnectOAuth, listOAuthConnections } from '../auth';
import type { OAuthProvider } from '../config';

interface UseOAuthReturn {
  connections: string[];
  isLoading: boolean;
  error: string | null;
  fetchConnections: () => Promise<void>;
  connect: (provider: OAuthProvider) => Promise<void>;
  disconnect: (provider: OAuthProvider) => Promise<void>;
  isConnected: (provider: OAuthProvider) => boolean;
}

/**
 * Hook for managing OAuth connections
 */
export function useOAuth(): UseOAuthReturn {
  const [connections, setConnections] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConnections = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const connectedProviders = await listOAuthConnections();
      setConnections(connectedProviders);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch connections';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const connect = useCallback(async (provider: OAuthProvider): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      // This will redirect to the OAuth provider
      await initiateOAuth(provider);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to initiate OAuth';
      setError(message);
      setIsLoading(false);
      throw err;
    }
    // Note: Loading state remains true as page will redirect
  }, []);

  const disconnect = useCallback(async (provider: OAuthProvider): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await disconnectOAuth(provider);
      setConnections((prev) => prev.filter((p) => p !== provider));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to disconnect';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const isConnected = useCallback(
    (provider: OAuthProvider): boolean => {
      return connections.includes(provider);
    },
    [connections]
  );

  // Fetch connections on mount
  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

  return {
    connections,
    isLoading,
    error,
    fetchConnections,
    connect,
    disconnect,
    isConnected,
  };
}
