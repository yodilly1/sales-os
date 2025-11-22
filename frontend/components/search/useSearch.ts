/**
 * Custom hook for search functionality.
 *
 * Provides state management and API integration for search features.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import {
  search as searchApi,
  quickSearch,
  getAutocompleteSuggestions,
  SearchRequest,
  SearchResponse,
  SearchFilters,
  AutocompleteSuggestion,
  SortOrder,
} from '@/lib/api/search';

interface UseSearchOptions {
  debounceMs?: number;
  autoSearch?: boolean;
  initialFilters?: SearchFilters;
}

interface UseSearchReturn {
  // State
  query: string;
  results: SearchResponse | null;
  suggestions: AutocompleteSuggestion[];
  filters: SearchFilters;
  isLoading: boolean;
  isLoadingSuggestions: boolean;
  error: string | null;
  page: number;
  sortBy: SortOrder;

  // Actions
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  setSortBy: (sortBy: SortOrder) => void;
  setPage: (page: number) => void;
  executeSearch: () => Promise<void>;
  clearSearch: () => void;
  clearFilters: () => void;
}

/**
 * Hook for managing search state and operations.
 */
export function useSearch(options: UseSearchOptions = {}): UseSearchReturn {
  const { debounceMs = 300, autoSearch = true, initialFilters = {} } = options;

  // State
  const [query, setQueryState] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [filters, setFiltersState] = useState<SearchFilters>(initialFilters);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPageState] = useState(1);
  const [sortBy, setSortByState] = useState<SortOrder>('relevance');

  // Refs for debouncing
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const suggestionTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Execute search
  const executeSearch = useCallback(async () => {
    if (!query.trim()) {
      setResults(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: SearchRequest = {
        query: query.trim(),
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        page,
        page_size: 20,
        sort_by: sortBy,
        include_facets: true,
        highlight: true,
      };

      const response = await searchApi(request);
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  }, [query, filters, page, sortBy]);

  // Fetch autocomplete suggestions
  const fetchSuggestions = useCallback(async (prefix: string) => {
    if (prefix.length < 2) {
      setSuggestions([]);
      return;
    }

    setIsLoadingSuggestions(true);

    try {
      const response = await getAutocompleteSuggestions(prefix, {
        limit: 10,
        includeRecent: true,
      });
      setSuggestions(response.suggestions);
    } catch {
      setSuggestions([]);
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, []);

  // Set query with debounced suggestions
  const setQuery = useCallback(
    (newQuery: string) => {
      setQueryState(newQuery);

      // Debounce suggestion fetching
      if (suggestionTimerRef.current) {
        clearTimeout(suggestionTimerRef.current);
      }
      suggestionTimerRef.current = setTimeout(() => {
        fetchSuggestions(newQuery);
      }, 150);

      // Debounce auto-search
      if (autoSearch && newQuery.trim()) {
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
        debounceTimerRef.current = setTimeout(() => {
          executeSearch();
        }, debounceMs);
      }
    },
    [autoSearch, debounceMs, executeSearch, fetchSuggestions]
  );

  // Set filters and reset page
  const setFilters = useCallback((newFilters: SearchFilters) => {
    setFiltersState(newFilters);
    setPageState(1);
  }, []);

  // Set sort and reset page
  const setSortBy = useCallback((newSortBy: SortOrder) => {
    setSortByState(newSortBy);
    setPageState(1);
  }, []);

  // Set page
  const setPage = useCallback((newPage: number) => {
    setPageState(newPage);
  }, []);

  // Clear search
  const clearSearch = useCallback(() => {
    setQueryState('');
    setResults(null);
    setSuggestions([]);
    setError(null);
    setPageState(1);
  }, []);

  // Clear filters
  const clearFilters = useCallback(() => {
    setFiltersState({});
    setPageState(1);
  }, []);

  // Re-execute search when page or sort changes
  useEffect(() => {
    if (query.trim() && results) {
      executeSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sortBy]);

  // Re-execute search when filters change
  useEffect(() => {
    if (query.trim()) {
      executeSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (suggestionTimerRef.current) {
        clearTimeout(suggestionTimerRef.current);
      }
    };
  }, []);

  return {
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
  };
}
