'use client';

/**
 * SearchResults component displays search results with pagination.
 *
 * Features:
 * - Result cards with highlighted matches
 * - Entity type badges
 * - Pagination controls
 * - Empty state handling
 */

import React from 'react';
import { SearchResult, SearchResponse, SortOrder } from '@/lib/api/search';

interface SearchResultsProps {
  response: SearchResponse | null;
  isLoading?: boolean;
  error?: string | null;
  sortBy: SortOrder;
  onSortChange: (sort: SortOrder) => void;
  onPageChange: (page: number) => void;
  onResultClick?: (result: SearchResult) => void;
}

export function SearchResults({
  response,
  isLoading = false,
  error = null,
  sortBy,
  onSortChange,
  onPageChange,
  onResultClick,
}: SearchResultsProps) {
  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-500 mb-2">
          <svg
            className="w-12 h-12 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p className="text-gray-600">{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-200 rounded w-1/2 mb-4" />
            <div className="h-3 bg-gray-200 rounded w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (!response || response.results.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="w-16 h-16 mx-auto text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          No results found
        </h3>
        <p className="text-gray-500">
          Try adjusting your search or filters to find what you're looking for.
        </p>
      </div>
    );
  }

  // Entity type colors
  const getEntityColor = (type: string) => {
    const colors: Record<string, string> = {
      transcript: 'bg-blue-100 text-blue-800',
      call: 'bg-green-100 text-green-800',
      content: 'bg-purple-100 text-purple-800',
      prospect: 'bg-orange-100 text-orange-800',
      company: 'bg-indigo-100 text-indigo-800',
      coaching_report: 'bg-pink-100 text-pink-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  // Format date
  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-4">
      {/* Results header */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          {response.total_count.toLocaleString()} results
          <span className="text-gray-400 ml-1">
            ({response.search_time_ms}ms)
          </span>
        </div>

        {/* Sort dropdown */}
        <div className="flex items-center gap-2">
          <label htmlFor="sort" className="text-sm text-gray-600">
            Sort by:
          </label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as SortOrder)}
            className="border border-gray-300 rounded-md text-sm py-1 px-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="relevance">Relevance</option>
            <option value="date_desc">Newest first</option>
            <option value="date_asc">Oldest first</option>
            <option value="title_asc">Title A-Z</option>
            <option value="title_desc">Title Z-A</option>
          </select>
        </div>
      </div>

      {/* Results list */}
      <div className="space-y-3">
        {response.results.map((result) => (
          <button
            key={`${result.entity_type}-${result.id}`}
            onClick={() => onResultClick?.(result)}
            className="w-full text-left bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-4">
              <div className="flex-1 min-w-0">
                {/* Title with highlights */}
                <h3
                  className="text-lg font-medium text-gray-900 mb-1 truncate"
                  dangerouslySetInnerHTML={{
                    __html: result.highlighted_title || result.title,
                  }}
                />

                {/* Meta info */}
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getEntityColor(
                      result.entity_type
                    )}`}
                  >
                    {result.entity_type.replace('_', ' ')}
                  </span>

                  {result.status && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                      {result.status}
                    </span>
                  )}

                  {result.date && (
                    <span className="text-xs text-gray-500">
                      {formatDate(result.date)}
                    </span>
                  )}
                </div>

                {/* Summary with highlights */}
                {result.summary && (
                  <p
                    className="text-sm text-gray-600 line-clamp-2"
                    dangerouslySetInnerHTML={{
                      __html: result.highlighted_summary || result.summary,
                    }}
                  />
                )}

                {/* Tags */}
                {result.tags.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {result.tags.slice(0, 5).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-50 text-gray-600 border border-gray-200"
                      >
                        {tag}
                      </span>
                    ))}
                    {result.tags.length > 5 && (
                      <span className="text-xs text-gray-400">
                        +{result.tags.length - 5} more
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Arrow icon */}
              <svg
                className="w-5 h-5 text-gray-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </button>
        ))}
      </div>

      {/* Pagination */}
      {response.total_pages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            Page {response.page} of {response.total_pages}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(response.page - 1)}
              disabled={response.page <= 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>

            {/* Page numbers */}
            <div className="flex gap-1">
              {getPageNumbers(response.page, response.total_pages).map(
                (pageNum, idx) =>
                  pageNum === '...' ? (
                    <span key={`ellipsis-${idx}`} className="px-2 py-1">
                      ...
                    </span>
                  ) : (
                    <button
                      key={pageNum}
                      onClick={() => onPageChange(pageNum as number)}
                      className={`px-3 py-1 text-sm rounded-md ${
                        pageNum === response.page
                          ? 'bg-blue-500 text-white'
                          : 'border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
              )}
            </div>

            <button
              onClick={() => onPageChange(response.page + 1)}
              disabled={response.page >= response.total_pages}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper to generate page number array
function getPageNumbers(
  current: number,
  total: number
): (number | string)[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | string)[] = [];

  // Always show first page
  pages.push(1);

  if (current > 3) {
    pages.push('...');
  }

  // Show pages around current
  for (
    let i = Math.max(2, current - 1);
    i <= Math.min(total - 1, current + 1);
    i++
  ) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push('...');
  }

  // Always show last page
  pages.push(total);

  return pages;
}
