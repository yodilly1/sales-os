'use client'

import { useState, useMemo } from 'react'
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Search,
  Filter,
  X,
  Building2,
  Mail,
  RefreshCw,
  ExternalLink,
} from 'lucide-react'
import type {
  Prospect,
  ProspectFilters,
  SortConfig,
  EnrichmentStatus,
  CRMSyncStatus,
} from '@/types'
import { cn, formatDate, getInitials, truncate } from '@/lib/utils'

interface ProspectsTableProps {
  prospects: Prospect[]
  selectedIds: Set<string>
  onSelectChange: (ids: Set<string>) => void
  onProspectClick?: (prospect: Prospect) => void
  onSyncCRM?: (prospectIds: string[]) => void
  onReEnrich?: (prospectId: string) => void
  filters: ProspectFilters
  onFiltersChange: (filters: ProspectFilters) => void
  sort: SortConfig | null
  onSortChange: (sort: SortConfig) => void
  isLoading?: boolean
}

const enrichmentStatusOptions: { value: EnrichmentStatus; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'partial', label: 'Partial' },
]

const crmSyncStatusOptions: { value: CRMSyncStatus; label: string }[] = [
  { value: 'not_synced', label: 'Not Synced' },
  { value: 'synced', label: 'Synced' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
  { value: 'out_of_sync', label: 'Out of Sync' },
]

function EnrichmentStatusBadge({ status }: { status: EnrichmentStatus }) {
  const config: Record<EnrichmentStatus, string> = {
    pending: 'badge-gray',
    in_progress: 'badge-primary',
    completed: 'badge-success',
    failed: 'badge-error',
    partial: 'badge-warning',
  }
  return <span className={config[status]}>{status.replace('_', ' ')}</span>
}

function CRMSyncBadge({ status }: { status: CRMSyncStatus }) {
  const config: Record<CRMSyncStatus, string> = {
    not_synced: 'badge-gray',
    synced: 'badge-success',
    pending: 'badge-primary',
    failed: 'badge-error',
    out_of_sync: 'badge-warning',
  }
  return <span className={config[status]}>{status.replace('_', ' ')}</span>
}

function SortIcon({ field, currentSort }: { field: string; currentSort: SortConfig | null }) {
  if (!currentSort || currentSort.field !== field) {
    return <ChevronsUpDown className="w-4 h-4 text-gray-400" />
  }
  return currentSort.direction === 'asc' ? (
    <ChevronUp className="w-4 h-4 text-primary-600" />
  ) : (
    <ChevronDown className="w-4 h-4 text-primary-600" />
  )
}

export function ProspectsTable({
  prospects,
  selectedIds,
  onSelectChange,
  onProspectClick,
  onSyncCRM,
  onReEnrich,
  filters,
  onFiltersChange,
  sort,
  onSortChange,
  isLoading,
}: ProspectsTableProps) {
  const [showFilters, setShowFilters] = useState(false)

  const handleSort = (field: SortConfig['field']) => {
    if (sort?.field === field) {
      onSortChange({ field, direction: sort.direction === 'asc' ? 'desc' : 'asc' })
    } else {
      onSortChange({ field, direction: 'asc' })
    }
  }

  const handleSelectAll = () => {
    if (selectedIds.size === prospects.length) {
      onSelectChange(new Set())
    } else {
      onSelectChange(new Set(prospects.map((p) => p.id)))
    }
  }

  const handleSelectOne = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    onSelectChange(newSelected)
  }

  const hasActiveFilters = useMemo(() => {
    return (
      (filters.enrichmentStatus && filters.enrichmentStatus.length > 0) ||
      (filters.crmSyncStatus && filters.crmSyncStatus.length > 0) ||
      filters.company ||
      filters.industry
    )
  }, [filters])

  const clearFilters = () => {
    onFiltersChange({
      search: filters.search,
    })
  }

  return (
    <div className="card overflow-hidden">
      {/* Search and Filter Bar */}
      <div className="p-4 border-b border-gray-200 space-y-3">
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search prospects by name, email, or company..."
              value={filters.search || ''}
              onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
              className="input pl-10"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'btn-secondary flex items-center gap-2',
              hasActiveFilters && 'border-primary-500 text-primary-600'
            )}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="w-5 h-5 bg-primary-600 text-white text-xs rounded-full flex items-center justify-center">
                !
              </span>
            )}
          </button>

          {/* Bulk Actions */}
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">{selectedIds.size} selected</span>
              {onSyncCRM && (
                <button
                  onClick={() => onSyncCRM(Array.from(selectedIds))}
                  className="btn-primary text-sm"
                >
                  Sync to CRM
                </button>
              )}
            </div>
          )}
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="p-4 bg-gray-50 rounded-lg space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Enrichment Status */}
              <div>
                <label className="label">Enrichment Status</label>
                <select
                  multiple
                  value={filters.enrichmentStatus || []}
                  onChange={(e) => {
                    const values = Array.from(e.target.selectedOptions, (o) => o.value) as EnrichmentStatus[]
                    onFiltersChange({ ...filters, enrichmentStatus: values.length ? values : undefined })
                  }}
                  className="input h-24"
                >
                  {enrichmentStatusOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* CRM Sync Status */}
              <div>
                <label className="label">CRM Sync Status</label>
                <select
                  multiple
                  value={filters.crmSyncStatus || []}
                  onChange={(e) => {
                    const values = Array.from(e.target.selectedOptions, (o) => o.value) as CRMSyncStatus[]
                    onFiltersChange({ ...filters, crmSyncStatus: values.length ? values : undefined })
                  }}
                  className="input h-24"
                >
                  {crmSyncStatusOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Company */}
              <div>
                <label className="label">Company</label>
                <input
                  type="text"
                  value={filters.company || ''}
                  onChange={(e) =>
                    onFiltersChange({ ...filters, company: e.target.value || undefined })
                  }
                  placeholder="Filter by company"
                  className="input"
                />
              </div>

              {/* Industry */}
              <div>
                <label className="label">Industry</label>
                <input
                  type="text"
                  value={filters.industry || ''}
                  onChange={(e) =>
                    onFiltersChange({ ...filters, industry: e.target.value || undefined })
                  }
                  placeholder="Filter by industry"
                  className="input"
                />
              </div>
            </div>

            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
              >
                <X className="w-3 h-3" />
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 w-12">
                <input
                  type="checkbox"
                  checked={selectedIds.size === prospects.length && prospects.length > 0}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-1">
                  Name
                  <SortIcon field="name" currentSort={sort} />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('company')}
              >
                <div className="flex items-center gap-1">
                  Company
                  <SortIcon field="company" currentSort={sort} />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('enrichmentStatus')}
              >
                <div className="flex items-center gap-1">
                  Enrichment
                  <SortIcon field="enrichmentStatus" currentSort={sort} />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('crmSyncStatus')}
              >
                <div className="flex items-center gap-1">
                  CRM Status
                  <SortIcon field="crmSyncStatus" currentSort={sort} />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center">
                  <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Loading prospects...</p>
                </td>
              </tr>
            ) : prospects.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center">
                  <Building2 className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-gray-500">No prospects found</p>
                  <p className="text-sm text-gray-400">
                    Try adjusting your filters or add new prospects.
                  </p>
                </td>
              </tr>
            ) : (
              prospects.map((prospect) => (
                <tr
                  key={prospect.id}
                  className={cn(
                    'hover:bg-gray-50 cursor-pointer',
                    selectedIds.has(prospect.id) && 'bg-primary-50'
                  )}
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(prospect.id)}
                      onChange={() => handleSelectOne(prospect.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                  <td
                    className="px-4 py-3"
                    onClick={() => onProspectClick?.(prospect)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-medium text-primary-700">
                          {getInitials(prospect.name)}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{prospect.name}</p>
                        {prospect.title && (
                          <p className="text-xs text-gray-500">{truncate(prospect.title, 30)}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td
                    className="px-4 py-3"
                    onClick={() => onProspectClick?.(prospect)}
                  >
                    {prospect.company ? (
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-gray-400" />
                        <span className="text-sm text-gray-700">{prospect.company}</span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td
                    className="px-4 py-3"
                    onClick={() => onProspectClick?.(prospect)}
                  >
                    <div className="space-y-1">
                      {prospect.email && (
                        <div className="flex items-center gap-1.5">
                          <Mail className="w-3.5 h-3.5 text-gray-400" />
                          <a
                            href={`mailto:${prospect.email}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-sm text-primary-600 hover:underline"
                          >
                            {truncate(prospect.email, 25)}
                          </a>
                        </div>
                      )}
                      {prospect.linkedinUrl && (
                        <a
                          href={prospect.linkedinUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-primary-600 hover:underline flex items-center gap-1"
                        >
                          LinkedIn
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <EnrichmentStatusBadge status={prospect.enrichmentStatus} />
                  </td>
                  <td className="px-4 py-3">
                    <CRMSyncBadge status={prospect.crmSyncStatus} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {onReEnrich && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onReEnrich(prospect.id)
                          }}
                          className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded"
                          title="Re-enrich"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer with count */}
      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-500">
        Showing {prospects.length} prospect{prospects.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}

export default ProspectsTable
