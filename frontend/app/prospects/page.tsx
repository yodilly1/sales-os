'use client'

import { useState, useEffect, useCallback } from 'react'
import { Plus, Upload, List, RefreshCw, AlertCircle } from 'lucide-react'
import {
  ProspectCard,
  CompanyCard,
  BulkUploader,
  EnrichmentQueue,
  ProspectsTable,
  SingleLookupForm,
  ExportMenu,
} from '@/components/prospects'
import {
  lookupProspect,
  uploadBulkFile,
  getProspects,
  getEnrichmentProgress,
  listBatches,
  syncToCRM,
  reEnrichProspect,
  cancelBatch,
  generateExportContent,
  getCompany,
} from '@/lib/api/enrichment'
import { downloadFile } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type {
  Prospect,
  Company,
  EnrichmentBatch,
  ProspectFilters,
  SortConfig,
  SingleLookupResponse,
  ExportFormat,
} from '@/types'

type ViewMode = 'table' | 'lookup' | 'bulk' | 'queue'

export default function ProspectsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('lookup') // Default to lookup for easier testing
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [companies, setCompanies] = useState<Map<string, Company>>(new Map())
  const [batches, setBatches] = useState<EnrichmentBatch[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<ProspectFilters>({})
  const [sort, setSort] = useState<SortConfig | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const [lookupResult, setLookupResult] = useState<SingleLookupResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch prospects from real API
  const fetchProspects = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await getProspects({ filters, sort, limit: 100, offset: 0 })
      setProspects(response.prospects || [])
    } catch (err) {
      console.error('Failed to fetch prospects:', err)
      setProspects([])
      // Don't show error for empty state - this is expected when starting fresh
    } finally {
      setIsLoading(false)
    }
  }, [filters, sort])

  // Fetch batches from real API
  const fetchBatches = useCallback(async () => {
    try {
      const response = await listBatches({ limit: 10 })
      setBatches(response.batches || [])
    } catch (err) {
      console.error('Failed to fetch batches:', err)
      setBatches([])
    }
  }, [])

  useEffect(() => {
    fetchProspects()
    fetchBatches()
  }, [fetchProspects, fetchBatches])

  // Handle single lookup - calls real API
  const handleLookup = async (request: Parameters<typeof lookupProspect>[0]) => {
    setError(null)
    try {
      const response = await lookupProspect(request)
      setLookupResult(response)
      if (response.success && response.prospect) {
        // Add to prospects list
        setProspects((prev) => [response.prospect!, ...prev.filter((p) => p.id !== response.prospect!.id)])
        if (response.company) {
          setCompanies((prev) => new Map(prev).set(response.company!.id, response.company!))
        }
      }
      return response
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to lookup prospect'
      setError(errorMsg)
      throw err
    }
  }

  // Handle bulk upload - calls real API
  const handleBulkUpload = async (file: File, name: string) => {
    setError(null)
    try {
      const response = await uploadBulkFile(file, name)
      fetchBatches()
      return response
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to upload file'
      setError(errorMsg)
      throw err
    }
  }

  // Handle CRM sync - calls real API
  const handleSyncCRM = async (prospectIds: string[]) => {
    setError(null)
    try {
      await syncToCRM({ prospectIds, targetCRM: 'hubspot' })
      // Update local state
      setProspects((prev) =>
        prev.map((p) =>
          prospectIds.includes(p.id) ? { ...p, crmSyncStatus: 'synced' as const } : p
        )
      )
      setSelectedIds(new Set())
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to sync to CRM'
      setError(errorMsg)
    }
  }

  // Handle re-enrich - calls real API
  const handleReEnrich = async (prospectId: string) => {
    setError(null)
    try {
      const updated = await reEnrichProspect(prospectId)
      setProspects((prev) => prev.map((p) => (p.id === prospectId ? updated : p)))
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to re-enrich prospect'
      setError(errorMsg)
    }
  }

  // Handle cancel batch - calls real API
  const handleCancelBatch = async (batchId: string) => {
    setError(null)
    try {
      await cancelBatch(batchId)
      setBatches((prev) =>
        prev.map((b) => (b.id === batchId ? { ...b, status: 'cancelled' as const } : b))
      )
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to cancel batch'
      setError(errorMsg)
    }
  }

  // Handle export
  const handleExport = async (
    format: ExportFormat,
    includeCompanyData: boolean,
    selectedOnly: boolean
  ) => {
    setIsExporting(true)
    try {
      const prospectsToExport = selectedOnly
        ? prospects.filter((p) => selectedIds.has(p.id))
        : prospects

      const content = generateExportContent(
        prospectsToExport,
        companies,
        format,
        includeCompanyData
      )

      const mimeTypes: Record<ExportFormat, string> = {
        csv: 'text/csv',
        xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        json: 'application/json',
      }

      const timestamp = new Date().toISOString().split('T')[0]
      downloadFile(content, `prospects-${timestamp}.${format}`, mimeTypes[format])
    } finally {
      setIsExporting(false)
    }
  }

  // Handle prospect click
  const handleProspectClick = async (prospect: Prospect) => {
    setSelectedProspect(prospect)
    if (prospect.companyId) {
      try {
        const company = await getCompany(prospect.companyId)
        setSelectedCompany(company)
        setCompanies((prev) => new Map(prev).set(company.id, company))
      } catch {
        setSelectedCompany(companies.get(prospect.companyId) || null)
      }
    } else {
      setSelectedCompany(null)
    }
  }

  // Get progress for batches - calls real API
  const handleGetProgress = async (batchId: string) => {
    try {
      return await getEnrichmentProgress(batchId)
    } catch (err) {
      console.error('Failed to get progress:', err)
      throw err
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prospects</h1>
          <p className="text-sm text-gray-600 mt-1">
            Research and enrich prospect data, sync to your CRM.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ExportMenu
            selectedCount={selectedIds.size}
            totalCount={prospects.length}
            onExport={handleExport}
            isExporting={isExporting}
          />
          <button
            onClick={() => fetchProspects()}
            disabled={isLoading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-red-800">Error</h4>
            <p className="text-sm text-red-700">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}

      {/* View Mode Tabs */}
      <div className="flex items-center gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setViewMode('table')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
            viewMode === 'table'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <List className="w-4 h-4" />
          All Prospects ({prospects.length})
        </button>
        <button
          onClick={() => setViewMode('lookup')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
            viewMode === 'lookup'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <Plus className="w-4 h-4" />
          Single Lookup
        </button>
        <button
          onClick={() => setViewMode('bulk')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
            viewMode === 'bulk'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          <Upload className="w-4 h-4" />
          Bulk Upload
        </button>
        <button
          onClick={() => setViewMode('queue')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
            viewMode === 'queue'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          )}
        >
          Queue
          {batches.filter((b) => b.status === 'processing').length > 0 && (
            <span className="w-5 h-5 bg-primary-600 text-white text-xs rounded-full flex items-center justify-center">
              {batches.filter((b) => b.status === 'processing').length}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className={cn('lg:col-span-2', selectedProspect && viewMode === 'table' ? '' : 'lg:col-span-3')}>
          {viewMode === 'table' && (
            <ProspectsTable
              prospects={prospects}
              selectedIds={selectedIds}
              onSelectChange={setSelectedIds}
              onProspectClick={handleProspectClick}
              onSyncCRM={handleSyncCRM}
              onReEnrich={handleReEnrich}
              filters={filters}
              onFiltersChange={setFilters}
              sort={sort}
              onSortChange={setSort}
              isLoading={isLoading}
            />
          )}

          {viewMode === 'lookup' && (
            <div className="space-y-6">
              <SingleLookupForm
                onLookup={handleLookup}
                onResult={(result) => {
                  setLookupResult(result)
                  if (result.success && result.prospect) {
                    setSelectedProspect(result.prospect)
                    setSelectedCompany(result.company)
                  }
                }}
              />

              {lookupResult?.success && lookupResult.prospect && (
                <div className="grid md:grid-cols-2 gap-6">
                  <ProspectCard
                    prospect={lookupResult.prospect}
                    company={lookupResult.company}
                    onReEnrich={handleReEnrich}
                    onSyncCRM={(id) => handleSyncCRM([id])}
                  />
                  {lookupResult.company && (
                    <CompanyCard company={lookupResult.company} />
                  )}
                </div>
              )}
            </div>
          )}

          {viewMode === 'bulk' && (
            <BulkUploader
              onUpload={handleBulkUpload}
              onUploadComplete={() => {
                setViewMode('queue')
                fetchBatches()
              }}
            />
          )}

          {viewMode === 'queue' && (
            <EnrichmentQueue
              batches={batches}
              getProgress={handleGetProgress}
              onCancel={handleCancelBatch}
              onViewResults={(batchId) => {
                console.log('View results for batch:', batchId)
                setViewMode('table')
              }}
            />
          )}
        </div>

        {/* Side Panel - Selected Prospect Details */}
        {selectedProspect && viewMode === 'table' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Prospect Details</h3>
              <button
                onClick={() => {
                  setSelectedProspect(null)
                  setSelectedCompany(null)
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Close
              </button>
            </div>
            <ProspectCard
              prospect={selectedProspect}
              company={selectedCompany}
              onReEnrich={handleReEnrich}
              onSyncCRM={(id) => handleSyncCRM([id])}
            />
            {selectedCompany && (
              <CompanyCard company={selectedCompany} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
