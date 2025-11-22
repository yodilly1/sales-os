'use client';

/**
 * SearchModal - Full-featured search modal component.
 *
 * Combines all search components into a unified modal experience:
 * - SearchBar with autocomplete
 * - SearchFilters with facets
 * - SearchResults with pagination
 * - SearchHistory and SavedSearches in sidebar
 */

import React, { useEffect, useCallback } from 'react';
import { SearchBar } from './SearchBar';
import { SearchResults } from './SearchResults';
import { SearchFilters as SearchFiltersComponent } from './SearchFilters';
import { SearchHistory } from './SearchHistory';
import { SavedSearches } from './SavedSearches';
import { useSearch } from './useSearch';
import { executeSavedSearch, SearchResult, SearchFilters } from '@/lib/api/search';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onResultClick?: (result: SearchResult) => void;
  initialQuery?: string;
}

export function SearchModal({
  isOpen,
  onClose,
  onResultClick,
  initialQuery = '',
}: SearchModalProps) {
  const {
    query,
    results,
    suggestions,
    filters,
    isLoading,
    isLoadingSuggestions,
    error,
    page,
    sortBy,
    setQuery,
    setFilters,
    setSortBy,
    setPage,
    executeSearch,
    clearSearch,
    clearFilters,
  } = useSearch({ autoSearch: false, debounceMs: 500 });

  // Set initial query
  useEffect(() => {
    if (isOpen && initialQuery && initialQuery !== query) {
      setQuery(initialQuery);
    }
  }, [isOpen, initialQuery]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Close on Escape
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }

      // Open search modal with Cmd/Ctrl + K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (!isOpen) {
          // Would need parent to handle this
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Handle result click
  const handleResultClick = useCallback(
    (result: SearchResult) => {
      onResultClick?.(result);
      onClose();
    },
    [onResultClick, onClose]
  );

  // Execute saved search
  const handleExecuteSavedSearch = useCallback(
    async (searchId: number) => {
      try {
        const response = await executeSavedSearch(searchId);
        // Update local state with saved search results
        setQuery(response.query);
        // Results will be shown automatically
      } catch (err) {
        console.error('Failed to execute saved search:', err);
      }
    },
    [setQuery]
  );

  // Handle search from history
  const handleHistorySelect = useCallback(
    (historyQuery: string, historyFilters?: Record<string, unknown>) => {
      setQuery(historyQuery);
      if (historyFilters) {
        setFilters(historyFilters as SearchFilters);
      }
      executeSearch();
    },
    [setQuery, setFilters, executeSearch]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative flex flex-col h-full max-h-[90vh] w-full max-w-6xl mx-auto mt-[5vh] bg-white rounded-t-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-4 px-6 py-4 border-b border-gray-200">
          <div className="flex-1">
            <SearchBar
              value={query}
              onChange={setQuery}
              onSearch={executeSearch}
              suggestions={suggestions}
              isLoading={isLoadingSuggestions}
              autoFocus
              className="max-w-2xl"
            />
          </div>

          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <svg
              className="w-6 h-6"
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
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0 border-r border-gray-200 overflow-y-auto bg-gray-50">
            {/* Filters */}
            {results && results.facets && (
              <div className="p-4 border-b border-gray-200">
                <SearchFiltersComponent
                  filters={filters}
                  facets={results.facets}
                  onFiltersChange={setFilters}
                  onClearFilters={clearFilters}
                />
              </div>
            )}

            {/* History & Saved Searches tabs */}
            <div className="divide-y divide-gray-200">
              <SearchHistory onSearchSelect={handleHistorySelect} limit={5} />
              <SavedSearches
                onExecute={handleExecuteSavedSearch}
                currentQuery={query}
                currentFilters={filters}
              />
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Empty state when no search */}
            {!query && !results && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <svg
                  className="w-16 h-16 text-gray-400 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <h2 className="text-xl font-medium text-gray-900 mb-2">
                  Search Sales OS
                </h2>
                <p className="text-gray-500 max-w-md">
                  Search across transcripts, generated content, prospects,
                  companies, and coaching reports.
                </p>

                <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
                  <button
                    onClick={() => setQuery('recent calls')}
                    className="p-3 bg-gray-100 rounded-lg hover:bg-gray-200 text-left"
                  >
                    <div className="font-medium text-gray-900">Recent Calls</div>
                    <div className="text-gray-500 text-xs">
                      View latest transcripts
                    </div>
                  </button>
                  <button
                    onClick={() => setQuery('proposals')}
                    className="p-3 bg-gray-100 rounded-lg hover:bg-gray-200 text-left"
                  >
                    <div className="font-medium text-gray-900">Proposals</div>
                    <div className="text-gray-500 text-xs">
                      Find generated content
                    </div>
                  </button>
                  <button
                    onClick={() => setQuery('coaching')}
                    className="p-3 bg-gray-100 rounded-lg hover:bg-gray-200 text-left"
                  >
                    <div className="font-medium text-gray-900">Coaching</div>
                    <div className="text-gray-500 text-xs">
                      Review SPICED feedback
                    </div>
                  </button>
                </div>

                <div className="mt-8 flex items-center gap-2 text-xs text-gray-400">
                  <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300">
                    Enter
                  </kbd>
                  <span>to search</span>
                  <span className="mx-2">|</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300">
                    Esc
                  </kbd>
                  <span>to close</span>
                </div>
              </div>
            )}

            {/* Search results */}
            {(query || results) && (
              <SearchResults
                response={results}
                isLoading={isLoading}
                error={error}
                sortBy={sortBy}
                onSortChange={setSortBy}
                onPageChange={setPage}
                onResultClick={handleResultClick}
              />
            )}
          </div>
        </div>

        {/* Footer with search tips */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span>
              <strong>Tip:</strong> Use quotes for exact phrases:{' '}
              <code className="bg-gray-200 px-1 rounded">"sales deck"</code>
            </span>
            <span className="border-l border-gray-300 pl-4">
              Filter by type:{' '}
              <code className="bg-gray-200 px-1 rounded">type:transcript</code>
            </span>
            <span className="border-l border-gray-300 pl-4">
              Date range:{' '}
              <code className="bg-gray-200 px-1 rounded">date:last_7_days</code>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
