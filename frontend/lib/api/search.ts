/**
 * Search API client for Sales OS frontend.
 *
 * Provides type-safe API calls for search functionality.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// =============================================================================
// Types
// =============================================================================

export type EntityType =
  | 'transcript'
  | 'call'
  | 'content'
  | 'prospect'
  | 'company'
  | 'coaching_report'
  | 'all';

export type SortOrder =
  | 'relevance'
  | 'date_desc'
  | 'date_asc'
  | 'title_asc'
  | 'title_desc';

export type DateRangePreset =
  | 'today'
  | 'yesterday'
  | 'last_7_days'
  | 'last_30_days'
  | 'last_90_days'
  | 'this_month'
  | 'last_month'
  | 'this_quarter'
  | 'this_year'
  | 'custom';

export interface SearchFilters {
  entity_types?: EntityType[];
  date_preset?: DateRangePreset;
  date_from?: string;
  date_to?: string;
  status?: string[];
  tags?: string[];
  tags_any?: string[];
  content_types?: string[];
  prospect_id?: number;
  company_id?: number;
  user_id?: number;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  page?: number;
  page_size?: number;
  sort_by?: SortOrder;
  include_facets?: boolean;
  highlight?: boolean;
}

export interface SearchResult {
  id: number;
  entity_type: string;
  title: string;
  summary?: string;
  highlighted_title?: string;
  highlighted_summary?: string;
  status?: string;
  tags: string[];
  date?: string;
  relevance_score: number;
  metadata?: Record<string, unknown>;
}

export interface FacetValue {
  value: string;
  count: number;
  selected: boolean;
}

export interface FacetResult {
  name: string;
  display_name: string;
  values: FacetValue[];
}

export interface SearchResponse {
  query: string;
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: SearchResult[];
  facets?: FacetResult[];
  search_time_ms: number;
  filters_applied?: SearchFilters;
}

export interface AutocompleteSuggestion {
  text: string;
  type: 'recent' | 'popular' | 'entity';
  entity_type?: string;
  entity_id?: number;
  frequency?: number;
}

export interface AutocompleteResponse {
  prefix: string;
  suggestions: AutocompleteSuggestion[];
}

export interface SearchHistoryItem {
  id: number;
  query: string;
  filters?: Record<string, unknown>;
  result_count: number;
  entity_types?: string[];
  created_at: string;
}

export interface SavedSearch {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  query: string;
  filters?: Record<string, unknown>;
  entity_types?: string[];
  is_default: boolean;
  use_count: number;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
}

export interface CreateSavedSearchRequest {
  name: string;
  description?: string;
  query: string;
  filters?: SearchFilters;
  entity_types?: EntityType[];
  is_default?: boolean;
}

export interface UpdateSavedSearchRequest {
  name?: string;
  description?: string;
  query?: string;
  filters?: SearchFilters;
  entity_types?: EntityType[];
  is_default?: boolean;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Execute a search query.
 */
export async function search(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Execute a quick search for instant results.
 */
export async function quickSearch(
  query: string,
  limit: number = 5
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const response = await fetch(`${API_BASE}/search/quick?${params}`);

  if (!response.ok) {
    throw new Error(`Quick search failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get autocomplete suggestions.
 */
export async function getAutocompleteSuggestions(
  prefix: string,
  options: {
    limit?: number;
    entityTypes?: EntityType[];
    includeRecent?: boolean;
  } = {}
): Promise<AutocompleteResponse> {
  const params = new URLSearchParams({
    prefix,
    limit: String(options.limit || 10),
    include_recent: String(options.includeRecent !== false),
  });

  if (options.entityTypes) {
    options.entityTypes.forEach((type) => params.append('entity_types', type));
  }

  const response = await fetch(`${API_BASE}/search/autocomplete?${params}`);

  if (!response.ok) {
    throw new Error(`Autocomplete failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get search history.
 */
export async function getSearchHistory(
  limit: number = 20,
  offset: number = 0
): Promise<{ items: SearchHistoryItem[]; total: number }> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response = await fetch(`${API_BASE}/search/history?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to get search history: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Clear all search history.
 */
export async function clearSearchHistory(): Promise<void> {
  const response = await fetch(`${API_BASE}/search/history`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to clear search history: ${response.statusText}`);
  }
}

/**
 * Delete a specific history item.
 */
export async function deleteSearchHistoryItem(historyId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/search/history/${historyId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete history item: ${response.statusText}`);
  }
}

/**
 * Create a saved search.
 */
export async function createSavedSearch(
  data: CreateSavedSearchRequest
): Promise<SavedSearch> {
  const response = await fetch(`${API_BASE}/search/saved`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to create saved search: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get all saved searches.
 */
export async function getSavedSearches(
  limit: number = 50,
  offset: number = 0
): Promise<{ items: SavedSearch[]; total: number }> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response = await fetch(`${API_BASE}/search/saved?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to get saved searches: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a specific saved search.
 */
export async function getSavedSearch(searchId: number): Promise<SavedSearch> {
  const response = await fetch(`${API_BASE}/search/saved/${searchId}`);

  if (!response.ok) {
    throw new Error(`Failed to get saved search: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update a saved search.
 */
export async function updateSavedSearch(
  searchId: number,
  data: UpdateSavedSearchRequest
): Promise<SavedSearch> {
  const response = await fetch(`${API_BASE}/search/saved/${searchId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to update saved search: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a saved search.
 */
export async function deleteSavedSearch(searchId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/search/saved/${searchId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete saved search: ${response.statusText}`);
  }
}

/**
 * Execute a saved search.
 */
export async function executeSavedSearch(
  searchId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(
    `${API_BASE}/search/saved/${searchId}/execute?${params}`,
    { method: 'POST' }
  );

  if (!response.ok) {
    throw new Error(`Failed to execute saved search: ${response.statusText}`);
  }

  return response.json();
}
