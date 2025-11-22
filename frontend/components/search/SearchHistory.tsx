'use client';

/**
 * SearchHistory component displays recent searches.
 *
 * Features:
 * - List of recent searches
 * - Click to re-execute search
 * - Delete individual items
 * - Clear all history
 */

import React, { useState, useEffect } from 'react';
import {
  SearchHistoryItem,
  getSearchHistory,
  deleteSearchHistoryItem,
  clearSearchHistory,
} from '@/lib/api/search';

interface SearchHistoryProps {
  onSearchSelect: (query: string, filters?: Record<string, unknown>) => void;
  limit?: number;
}

export function SearchHistory({
  onSearchSelect,
  limit = 10,
}: SearchHistoryProps) {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load history
  useEffect(() => {
    loadHistory();
  }, [limit]);

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getSearchHistory(limit);
      setHistory(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

  // Delete single item
  const handleDelete = async (id: number) => {
    try {
      await deleteSearchHistoryItem(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  // Clear all history
  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all search history?')) {
      return;
    }

    try {
      await clearSearchHistory();
      setHistory([]);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  // Format relative time
  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-500 text-sm">{error}</p>
        <button
          onClick={loadHistory}
          className="mt-2 text-blue-600 text-sm hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="p-4 text-center">
        <svg
          className="w-8 h-8 mx-auto text-gray-400 mb-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-gray-500 text-sm">No recent searches</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
        <h3 className="text-sm font-medium text-gray-700">Recent Searches</h3>
        <button
          onClick={handleClearAll}
          className="text-xs text-gray-500 hover:text-red-600"
        >
          Clear all
        </button>
      </div>

      {/* History list */}
      <ul className="divide-y divide-gray-100">
        {history.map((item) => (
          <li
            key={item.id}
            className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 group"
          >
            {/* Clock icon */}
            <svg
              className="w-4 h-4 text-gray-400 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>

            {/* Search info */}
            <button
              onClick={() => onSearchSelect(item.query, item.filters || undefined)}
              className="flex-1 min-w-0 text-left"
            >
              <div className="text-sm text-gray-900 truncate">{item.query}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span>{item.result_count} results</span>
                <span>-</span>
                <span>{formatRelativeTime(item.created_at)}</span>
              </div>
            </button>

            {/* Entity types */}
            {item.entity_types && item.entity_types.length > 0 && (
              <div className="hidden sm:flex gap-1 flex-shrink-0">
                {item.entity_types.slice(0, 2).map((type) => (
                  <span
                    key={type}
                    className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                  >
                    {type}
                  </span>
                ))}
                {item.entity_types.length > 2 && (
                  <span className="text-xs text-gray-400">
                    +{item.entity_types.length - 2}
                  </span>
                )}
              </div>
            )}

            {/* Delete button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(item.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
              title="Delete from history"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
