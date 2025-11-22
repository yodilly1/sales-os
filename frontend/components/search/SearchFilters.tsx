'use client';

/**
 * SearchFilters component for faceted filtering.
 *
 * Features:
 * - Entity type filter
 * - Date range presets and custom dates
 * - Status filter
 * - Tag filter
 * - Facet counts display
 */

import React, { useState } from 'react';
import {
  SearchFilters as SearchFiltersType,
  FacetResult,
  EntityType,
  DateRangePreset,
} from '@/lib/api/search';

interface SearchFiltersProps {
  filters: SearchFiltersType;
  facets?: FacetResult[];
  onFiltersChange: (filters: SearchFiltersType) => void;
  onClearFilters: () => void;
}

export function SearchFilters({
  filters,
  facets = [],
  onFiltersChange,
  onClearFilters,
}: SearchFiltersProps) {
  const [showCustomDates, setShowCustomDates] = useState(false);

  // Get facet by name
  const getFacet = (name: string) => facets.find((f) => f.name === name);

  // Toggle entity type filter
  const toggleEntityType = (type: EntityType) => {
    const current = filters.entity_types || [];
    const newTypes = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];

    onFiltersChange({
      ...filters,
      entity_types: newTypes.length > 0 ? newTypes : undefined,
    });
  };

  // Set date preset
  const setDatePreset = (preset: DateRangePreset | undefined) => {
    setShowCustomDates(preset === 'custom');
    onFiltersChange({
      ...filters,
      date_preset: preset,
      date_from: preset === 'custom' ? filters.date_from : undefined,
      date_to: preset === 'custom' ? filters.date_to : undefined,
    });
  };

  // Toggle status filter
  const toggleStatus = (status: string) => {
    const current = filters.status || [];
    const newStatuses = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];

    onFiltersChange({
      ...filters,
      status: newStatuses.length > 0 ? newStatuses : undefined,
    });
  };

  // Toggle tag filter
  const toggleTag = (tag: string) => {
    const current = filters.tags || [];
    const newTags = current.includes(tag)
      ? current.filter((t) => t !== tag)
      : [...current, tag];

    onFiltersChange({
      ...filters,
      tags: newTags.length > 0 ? newTags : undefined,
    });
  };

  // Check if any filters are applied
  const hasFilters =
    (filters.entity_types && filters.entity_types.length > 0) ||
    filters.date_preset ||
    (filters.status && filters.status.length > 0) ||
    (filters.tags && filters.tags.length > 0);

  const entityTypeFacet = getFacet('entity_type');
  const statusFacet = getFacet('status');
  const tagsFacet = getFacet('tags');
  const dateFacet = getFacet('date_range');

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-gray-900">Filters</h3>
        {hasFilters && (
          <button
            onClick={onClearFilters}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Entity Type Filter */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Type</h4>
        <div className="space-y-2">
          {(entityTypeFacet?.values || defaultEntityTypes).map((item) => {
            const value =
              typeof item === 'string' ? item : item.value;
            const count = typeof item === 'string' ? null : item.count;
            const isSelected = filters.entity_types?.includes(
              value as EntityType
            );

            return (
              <label
                key={value}
                className="flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={isSelected || false}
                  onChange={() => toggleEntityType(value as EntityType)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 capitalize">
                  {value.replace('_', ' ')}
                </span>
                {count !== null && (
                  <span className="text-xs text-gray-400 ml-auto">
                    {count}
                  </span>
                )}
              </label>
            );
          })}
        </div>
      </div>

      {/* Date Filter */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Date</h4>
        <div className="space-y-2">
          {datePresets.map((preset) => {
            const facetValue = dateFacet?.values.find(
              (v) => v.value === preset.value
            );
            const isSelected = filters.date_preset === preset.value;

            return (
              <label
                key={preset.value}
                className="flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="radio"
                  name="date_preset"
                  checked={isSelected}
                  onChange={() =>
                    setDatePreset(
                      isSelected ? undefined : (preset.value as DateRangePreset)
                    )
                  }
                  className="border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{preset.label}</span>
                {facetValue && (
                  <span className="text-xs text-gray-400 ml-auto">
                    {facetValue.count}
                  </span>
                )}
              </label>
            );
          })}

          {/* Custom date option */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="date_preset"
              checked={showCustomDates || filters.date_preset === 'custom'}
              onChange={() => setDatePreset('custom')}
              className="border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Custom range</span>
          </label>

          {/* Custom date inputs */}
          {(showCustomDates || filters.date_preset === 'custom') && (
            <div className="ml-6 mt-2 space-y-2">
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  From
                </label>
                <input
                  type="date"
                  value={filters.date_from?.split('T')[0] || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      date_preset: 'custom',
                      date_from: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    })
                  }
                  className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">To</label>
                <input
                  type="date"
                  value={filters.date_to?.split('T')[0] || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      date_preset: 'custom',
                      date_to: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    })
                  }
                  className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status Filter */}
      {statusFacet && statusFacet.values.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Status</h4>
          <div className="space-y-2">
            {statusFacet.values.map((item) => {
              const isSelected = filters.status?.includes(item.value);

              return (
                <label
                  key={item.value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={isSelected || false}
                    onChange={() => toggleStatus(item.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">
                    {item.value}
                  </span>
                  <span className="text-xs text-gray-400 ml-auto">
                    {item.count}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Tags Filter */}
      {tagsFacet && tagsFacet.values.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Tags</h4>
          <div className="flex flex-wrap gap-2">
            {tagsFacet.values.map((item) => {
              const isSelected = filters.tags?.includes(item.value);

              return (
                <button
                  key={item.value}
                  onClick={() => toggleTag(item.value)}
                  className={`px-2 py-1 text-xs rounded-full border transition-colors ${
                    isSelected
                      ? 'bg-blue-100 border-blue-300 text-blue-800'
                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {item.value}
                  <span className="ml-1 text-gray-400">{item.count}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Applied filters summary */}
      {hasFilters && (
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Applied Filters
          </h4>
          <div className="flex flex-wrap gap-2">
            {filters.entity_types?.map((type) => (
              <span
                key={type}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded-full"
              >
                {type.replace('_', ' ')}
                <button
                  onClick={() => toggleEntityType(type)}
                  className="hover:text-blue-900"
                >
                  <svg
                    className="w-3 h-3"
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
              </span>
            ))}
            {filters.date_preset && (
              <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-green-50 text-green-700 rounded-full">
                {
                  datePresets.find((p) => p.value === filters.date_preset)
                    ?.label || filters.date_preset
                }
                <button
                  onClick={() => setDatePreset(undefined)}
                  className="hover:text-green-900"
                >
                  <svg
                    className="w-3 h-3"
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
              </span>
            )}
            {filters.status?.map((status) => (
              <span
                key={status}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded-full"
              >
                {status}
                <button
                  onClick={() => toggleStatus(status)}
                  className="hover:text-purple-900"
                >
                  <svg
                    className="w-3 h-3"
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
              </span>
            ))}
            {filters.tags?.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-orange-50 text-orange-700 rounded-full"
              >
                #{tag}
                <button
                  onClick={() => toggleTag(tag)}
                  className="hover:text-orange-900"
                >
                  <svg
                    className="w-3 h-3"
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
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Default entity types when facets are not available
const defaultEntityTypes = [
  'transcript',
  'call',
  'content',
  'prospect',
  'company',
  'coaching_report',
];

// Date presets
const datePresets = [
  { value: 'today', label: 'Today' },
  { value: 'last_7_days', label: 'Last 7 days' },
  { value: 'last_30_days', label: 'Last 30 days' },
  { value: 'last_90_days', label: 'Last 90 days' },
  { value: 'this_year', label: 'This year' },
];
