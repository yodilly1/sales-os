'use client';

/**
 * SavedSearches component for managing saved search queries.
 *
 * Features:
 * - List saved searches
 * - Execute saved search
 * - Edit saved search
 * - Delete saved search
 * - Create new saved search
 */

import React, { useState, useEffect } from 'react';
import {
  SavedSearch,
  getSavedSearches,
  deleteSavedSearch,
  createSavedSearch,
  updateSavedSearch,
  CreateSavedSearchRequest,
  SearchFilters,
} from '@/lib/api/search';

interface SavedSearchesProps {
  onExecute: (searchId: number) => void;
  currentQuery?: string;
  currentFilters?: SearchFilters;
}

interface SaveModalState {
  isOpen: boolean;
  mode: 'create' | 'edit';
  search?: SavedSearch;
}

export function SavedSearches({
  onExecute,
  currentQuery,
  currentFilters,
}: SavedSearchesProps) {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveModal, setSaveModal] = useState<SaveModalState>({
    isOpen: false,
    mode: 'create',
  });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  // Load saved searches
  useEffect(() => {
    loadSearches();
  }, []);

  const loadSearches = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getSavedSearches();
      setSearches(response.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load saved searches'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Open save modal for new search
  const openSaveModal = () => {
    if (!currentQuery) {
      alert('Enter a search query first');
      return;
    }

    setFormData({ name: '', description: '' });
    setSaveModal({ isOpen: true, mode: 'create' });
  };

  // Open edit modal
  const openEditModal = (search: SavedSearch) => {
    setFormData({
      name: search.name,
      description: search.description || '',
    });
    setSaveModal({ isOpen: true, mode: 'edit', search });
  };

  // Close modal
  const closeModal = () => {
    setSaveModal({ isOpen: false, mode: 'create' });
    setFormData({ name: '', description: '' });
  };

  // Save search
  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert('Please enter a name');
      return;
    }

    try {
      if (saveModal.mode === 'create' && currentQuery) {
        const data: CreateSavedSearchRequest = {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined,
          query: currentQuery,
          filters: currentFilters,
        };

        const newSearch = await createSavedSearch(data);
        setSearches((prev) => [newSearch, ...prev]);
      } else if (saveModal.mode === 'edit' && saveModal.search) {
        const updated = await updateSavedSearch(saveModal.search.id, {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined,
        });
        setSearches((prev) =>
          prev.map((s) => (s.id === updated.id ? updated : s))
        );
      }

      closeModal();
    } catch (err) {
      console.error('Failed to save search:', err);
      alert('Failed to save search');
    }
  };

  // Delete search
  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this saved search?')) {
      return;
    }

    try {
      await deleteSavedSearch(id);
      setSearches((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error('Failed to delete search:', err);
    }
  };

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header with save button */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
        <h3 className="text-sm font-medium text-gray-700">Saved Searches</h3>
        <button
          onClick={openSaveModal}
          disabled={!currentQuery}
          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed"
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Save current
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 text-center">
          <p className="text-red-500 text-sm">{error}</p>
          <button
            onClick={loadSearches}
            className="mt-2 text-blue-600 text-sm hover:underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!error && searches.length === 0 && (
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
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
          <p className="text-gray-500 text-sm">No saved searches yet</p>
          <p className="text-gray-400 text-xs mt-1">
            Save searches for quick access
          </p>
        </div>
      )}

      {/* Saved searches list */}
      {!error && searches.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {searches.map((search) => (
            <li
              key={search.id}
              className="px-4 py-3 hover:bg-gray-50 group"
            >
              <div className="flex items-start gap-3">
                {/* Bookmark icon */}
                <svg
                  className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                    search.is_default
                      ? 'text-yellow-500 fill-current'
                      : 'text-gray-400'
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                  />
                </svg>

                {/* Search info */}
                <button
                  onClick={() => onExecute(search.id)}
                  className="flex-1 min-w-0 text-left"
                >
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {search.name}
                  </div>
                  {search.description && (
                    <div className="text-xs text-gray-500 truncate">
                      {search.description}
                    </div>
                  )}
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                    <span className="truncate max-w-[150px]">
                      "{search.query}"
                    </span>
                    <span>-</span>
                    <span>Used {search.use_count}x</span>
                  </div>
                </button>

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => openEditModal(search)}
                    className="p-1 text-gray-400 hover:text-blue-600"
                    title="Edit"
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
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                      />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(search.id)}
                    className="p-1 text-gray-400 hover:text-red-600"
                    title="Delete"
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Save/Edit Modal */}
      {saveModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                {saveModal.mode === 'create'
                  ? 'Save Search'
                  : 'Edit Saved Search'}
              </h3>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="e.g., Active Prospects Q4"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  placeholder="Optional description..."
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {saveModal.mode === 'create' && currentQuery && (
                <div className="bg-gray-50 rounded-md p-3">
                  <div className="text-xs text-gray-500 mb-1">Query:</div>
                  <div className="text-sm text-gray-900">"{currentQuery}"</div>
                  {currentFilters &&
                    Object.keys(currentFilters).length > 0 && (
                      <div className="text-xs text-gray-500 mt-2">
                        + {Object.keys(currentFilters).length} filter(s)
                      </div>
                    )}
                </div>
              )}
            </div>

            <div className="px-4 py-3 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={closeModal}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                {saveModal.mode === 'create' ? 'Save' : 'Update'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
