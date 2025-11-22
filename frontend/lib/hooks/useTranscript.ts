'use client';

import { useState, useEffect, useCallback } from 'react';
import { transcriptApi, ApiClientError } from '@/lib/api';
import {
  Transcript,
  TranscriptListItem,
  ProcessingStatus,
  CRMPushRequest,
  CRMPushResponse,
} from '@/lib/types';

interface UseTranscriptOptions {
  pollWhileProcessing?: boolean;
  pollInterval?: number;
}

/**
 * Hook for fetching and managing a single transcript
 */
export function useTranscript(id: string | null, options: UseTranscriptOptions = {}) {
  const { pollWhileProcessing = true, pollInterval = 3000 } = options;

  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch transcript
  const fetchTranscript = useCallback(async () => {
    if (!id) {
      setTranscript(null);
      setIsLoading(false);
      return;
    }

    try {
      setError(null);
      const data = await transcriptApi.get(id);
      setTranscript(data);
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? err.message
          : 'Failed to fetch transcript';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  // Initial fetch
  useEffect(() => {
    setIsLoading(true);
    fetchTranscript();
  }, [fetchTranscript]);

  // Poll while processing
  useEffect(() => {
    if (!pollWhileProcessing || !transcript) return;
    if (transcript.status !== 'processing' && transcript.status !== 'pending') return;

    const intervalId = setInterval(fetchTranscript, pollInterval);
    return () => clearInterval(intervalId);
  }, [pollWhileProcessing, pollInterval, transcript?.status, fetchTranscript]);

  // Update notes
  const updateNotes = useCallback(
    async (content: string) => {
      if (!id) return;

      try {
        const updated = await transcriptApi.updateNotes(id, content);
        setTranscript((prev) =>
          prev ? { ...prev, callNotes: updated } : prev
        );
      } catch (err) {
        throw err;
      }
    },
    [id]
  );

  // Toggle task
  const toggleTask = useCallback(
    async (taskId: string, completed: boolean) => {
      if (!id) return;

      try {
        await transcriptApi.toggleTask(id, taskId, completed);
        setTranscript((prev) => {
          if (!prev?.spicedAnalysis) return prev;
          return {
            ...prev,
            spicedAnalysis: {
              ...prev.spicedAnalysis,
              suggestedTasks: prev.spicedAnalysis.suggestedTasks.map((task) =>
                task.id === taskId ? { ...task, completed } : task
              ),
            },
          };
        });
      } catch (err) {
        throw err;
      }
    },
    [id]
  );

  // Push to CRM
  const pushToCRM = useCallback(
    async (request: Omit<CRMPushRequest, 'transcriptId'>): Promise<CRMPushResponse> => {
      if (!id) throw new Error('No transcript ID');

      const response = await transcriptApi.pushToCRM({
        ...request,
        transcriptId: id,
      });

      if (response.success) {
        setTranscript((prev) =>
          prev
            ? {
                ...prev,
                crmStatus: 'synced',
                crmRecordId: response.recordId,
                crmPushedAt: new Date().toISOString(),
              }
            : prev
        );
      }

      return response;
    },
    [id]
  );

  // Re-analyze
  const reanalyze = useCallback(async () => {
    if (!id) return;

    try {
      await transcriptApi.analyze(id);
      setTranscript((prev) =>
        prev ? { ...prev, status: 'processing' } : prev
      );
    } catch (err) {
      throw err;
    }
  }, [id]);

  return {
    transcript,
    isLoading,
    error,
    refetch: fetchTranscript,
    updateNotes,
    toggleTask,
    pushToCRM,
    reanalyze,
  };
}

/**
 * Hook for fetching transcript list
 */
export function useTranscripts() {
  const [transcripts, setTranscripts] = useState<TranscriptListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchTranscripts = useCallback(async (pageNum: number = 1) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await transcriptApi.list({
        page: pageNum,
        pageSize: 20,
      });

      if (pageNum === 1) {
        setTranscripts(response.items);
      } else {
        setTranscripts((prev) => [...prev, ...response.items]);
      }

      setHasMore(response.hasMore);
      setPage(pageNum);
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? err.message
          : 'Failed to fetch transcripts';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchTranscripts(1);
  }, [fetchTranscripts]);

  const loadMore = useCallback(() => {
    if (!isLoading && hasMore) {
      fetchTranscripts(page + 1);
    }
  }, [fetchTranscripts, isLoading, hasMore, page]);

  const refetch = useCallback(() => {
    fetchTranscripts(1);
  }, [fetchTranscripts]);

  // Add new transcript to list
  const addTranscript = useCallback((transcript: TranscriptListItem) => {
    setTranscripts((prev) => [transcript, ...prev]);
  }, []);

  // Remove transcript from list
  const removeTranscript = useCallback((id: string) => {
    setTranscripts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Update transcript in list
  const updateTranscript = useCallback(
    (id: string, updates: Partial<TranscriptListItem>) => {
      setTranscripts((prev) =>
        prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
      );
    },
    []
  );

  return {
    transcripts,
    isLoading,
    error,
    hasMore,
    loadMore,
    refetch,
    addTranscript,
    removeTranscript,
    updateTranscript,
  };
}
