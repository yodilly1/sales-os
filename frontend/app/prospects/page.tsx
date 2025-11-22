'use client'

import { useState, useEffect, useCallback } from 'react'
import { Plus, Upload, List, RefreshCw } from 'lucide-react'
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

// Mock data for demonstration when API is not available
const mockProspects: Prospect[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@techcorp.com',
    title: 'VP of Engineering',
    company: 'TechCorp',
    companyId: 'c1',
    phone: '+1 (555) 123-4567',
    linkedinUrl: 'https://linkedin.com/in/sarahjohnson',
    location: 'San Francisco, CA',
    enrichmentStatus: 'completed',
    enrichmentData: {
      verifiedEmail: 'sarah.johnson@techcorp.com',
      verifiedPhone: '+1 (555) 123-4567',
      linkedinProfile: {
        url: 'https://linkedin.com/in/sarahjohnson',
        headline: 'VP of Engineering | Building amazing products',
        summary: 'Experienced engineering leader...',
        connections: 1247,
        profileImageUrl: null,
      },
      recentActivity: [
        {
          type: 'post',
          title: 'Excited to announce our new product launch',
          date: '2024-01-15',
          url: null,
          source: 'LinkedIn',
        },
      ],
      confidence: 92,
    },
    crmSyncStatus: 'synced',
    crmId: 'hub_12345',
    lastEnrichedAt: '2024-01-20T10:30:00Z',
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-20T10:30:00Z',
  },
  {
    id: '2',
    name: 'Michael Chen',
    email: 'mchen@innovate.io',
    title: 'Head of Sales',
    company: 'Innovate.io',
    companyId: 'c2',
    phone: null,
    linkedinUrl: 'https://linkedin.com/in/michaelchen',
    location: 'New York, NY',
    enrichmentStatus: 'completed',
    enrichmentData: {
      verifiedEmail: 'mchen@innovate.io',
      verifiedPhone: null,
      linkedinProfile: {
        url: 'https://linkedin.com/in/michaelchen',
        headline: 'Head of Sales at Innovate.io',
        summary: null,
        connections: 843,
        profileImageUrl: null,
      },
      recentActivity: [],
      confidence: 78,
    },
    crmSyncStatus: 'not_synced',
    crmId: null,
    lastEnrichedAt: '2024-01-18T14:20:00Z',
    createdAt: '2024-01-12T09:00:00Z',
    updatedAt: '2024-01-18T14:20:00Z',
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    email: null,
    title: 'CTO',
    company: 'StartupXYZ',
    companyId: 'c3',
    phone: null,
    linkedinUrl: null,
    location: null,
    enrichmentStatus: 'pending',
    enrichmentData: null,
    crmSyncStatus: 'not_synced',
    crmId: null,
    lastEnrichedAt: null,
    createdAt: '2024-01-22T11:00:00Z',
    updatedAt: '2024-01-22T11:00:00Z',
  },
]

const mockCompanies: Map<string, Company> = new Map([
  [
    'c1',
    {
      id: 'c1',
      name: 'TechCorp',
      domain: 'techcorp.com',
      industry: 'Software',
      size: '501-1000',
      employeeCount: 750,
      revenue: '$50M - $100M',
      funding: {
        totalRaised: '$45M',
        lastRoundType: 'Series C',
        lastRoundAmount: '$25M',
        lastRoundDate: '2023-06-15',
        investors: ['Sequoia', 'a16z', 'Greylock'],
      },
      techStack: ['React', 'Node.js', 'AWS', 'PostgreSQL', 'Kubernetes'],
      headquarters: 'San Francisco, CA',
      website: 'https://techcorp.com',
      linkedinUrl: 'https://linkedin.com/company/techcorp',
      description: 'Leading enterprise software company providing innovative solutions.',
      logoUrl: null,
      lastEnrichedAt: '2024-01-20T10:30:00Z',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-20T10:30:00Z',
    },
  ],
])

const mockBatches: EnrichmentBatch[] = [
  {
    id: 'batch1',
    name: 'Conference Attendees 2024',
    type: 'csv',
    status: 'processing',
    totalCount: 150,
    completedCount: 87,
    failedCount: 3,
    createdAt: '2024-01-22T09:00:00Z',
    updatedAt: '2024-01-22T10:30:00Z',
    completedAt: null,
    prospects: [],
  },
  {
    id: 'batch2',
    name: 'Event Leads - Jan',
    type: 'event_list',
    status: 'completed',
    totalCount: 45,
    completedCount: 43,
    failedCount: 2,
    createdAt: '2024-01-20T14:00:00Z',
    updatedAt: '2024-01-20T15:30:00Z',
    completedAt: '2024-01-20T15:30:00Z',
    prospects: [],
  },
]

export default function ProspectsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [prospects, setProspects] = useState<Prospect[]>(mockProspects)
  const [batches, setBatches] = useState<EnrichmentBatch[]>(mockBatches)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<ProspectFilters>({})
  const [sort, setSort] = useState<SortConfig | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const [lookupResult, setLookupResult] = useState<SingleLookupResponse | null>(null)

  // Fetch prospects (with mock data fallback)
  const fetchProspects = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await getProspects({ filters, sort, limit: 100, offset: 0 })
      setProspects(response.prospects)
    } catch {
      // Use mock data if API fails
      console.log('Using mock data - API not available')
      setProspects(mockProspects)
    } finally {
      setIsLoading(false)
    }
  }, [filters, sort])

  // Fetch batches
  const fetchBatches = useCallback(async () => {
    try {
      const response = await listBatches({ limit: 10 })
      setBatches(response.batches)
    } catch {
      // Use mock data
      setBatches(mockBatches)
    }
  }, [])

  useEffect(() => {
    fetchProspects()
    fetchBatches()
  }, [fetchProspects, fetchBatches])

  // Handle single lookup
  const handleLookup = async (request: Parameters<typeof lookupProspect>[0]) => {
    try {
      const response = await lookupProspect(request)
      setLookupResult(response)
      if (response.success && response.prospect) {
        // Add to prospects list
        setProspects((prev) => [response.prospect!, ...prev.filter((p) => p.id !== response.prospect!.id)])
      }
      return response
    } catch (err) {
      // Return mock response for demo
      const mockResponse: SingleLookupResponse = {
        success: true,
        prospect: {
          id: 'new_' + Date.now(),
          name: request.name,
          email: request.email || null,
          title: request.title || null,
          company: request.company || null,
          companyId: null,
          phone: null,
          linkedinUrl: request.linkedinUrl || null,
          location: null,
          enrichmentStatus: 'pending',
          enrichmentData: null,
          crmSyncStatus: 'not_synced',
          crmId: null,
          lastEnrichedAt: null,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
        company: null,
        error: null,
      }
      setLookupResult(mockResponse)
      if (mockResponse.prospect) {
        setProspects((prev) => [mockResponse.prospect!, ...prev])
      }
      return mockResponse
    }
  }

  // Handle bulk upload
  const handleBulkUpload = async (file: File, name: string) => {
    try {
      const response = await uploadBulkFile(file, name)
      fetchBatches()
      return response
    } catch {
      // Return mock response
      const mockResponse = {
        success: true,
        batchId: 'batch_' + Date.now(),
        totalRecords: 50,
        validRecords: 48,
        invalidRecords: 2,
        errors: ['Row 15: Invalid email format', 'Row 32: Missing required name field'],
      }
      const newBatch: EnrichmentBatch = {
        id: mockResponse.batchId,
        name,
        type: 'csv',
        status: 'queued',
        totalCount: mockResponse.totalRecords,
        completedCount: 0,
        failedCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        completedAt: null,
        prospects: [],
      }
      setBatches((prev) => [newBatch, ...prev])
      return mockResponse
    }
  }

  // Handle CRM sync
  const handleSyncCRM = async (prospectIds: string[]) => {
    try {
      await syncToCRM({ prospectIds, targetCRM: 'hubspot' })
      // Update local state
      setProspects((prev) =>
        prev.map((p) =>
          prospectIds.includes(p.id) ? { ...p, crmSyncStatus: 'synced' as const } : p
        )
      )
      setSelectedIds(new Set())
    } catch {
      // Mock update
      setProspects((prev) =>
        prev.map((p) =>
          prospectIds.includes(p.id) ? { ...p, crmSyncStatus: 'synced' as const } : p
        )
      )
      setSelectedIds(new Set())
    }
  }

  // Handle re-enrich
  const handleReEnrich = async (prospectId: string) => {
    try {
      const updated = await reEnrichProspect(prospectId)
      setProspects((prev) => prev.map((p) => (p.id === prospectId ? updated : p)))
    } catch {
      // Mock update
      setProspects((prev) =>
        prev.map((p) =>
          p.id === prospectId ? { ...p, enrichmentStatus: 'in_progress' as const } : p
        )
      )
    }
  }

  // Handle cancel batch
  const handleCancelBatch = async (batchId: string) => {
    try {
      await cancelBatch(batchId)
      setBatches((prev) =>
        prev.map((b) => (b.id === batchId ? { ...b, status: 'cancelled' as const } : b))
      )
    } catch {
      setBatches((prev) =>
        prev.map((b) => (b.id === batchId ? { ...b, status: 'cancelled' as const } : b))
      )
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
        mockCompanies,
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
      } catch {
        setSelectedCompany(mockCompanies.get(prospect.companyId) || null)
      }
    } else {
      setSelectedCompany(null)
    }
  }

  // Get progress for batches
  const handleGetProgress = async (batchId: string) => {
    try {
      return await getEnrichmentProgress(batchId)
    } catch {
      // Return mock progress
      const batch = batches.find((b) => b.id === batchId)
      return {
        batchId,
        status: batch?.status || 'processing',
        totalCount: batch?.totalCount || 0,
        completedCount: (batch?.completedCount || 0) + Math.floor(Math.random() * 5),
        failedCount: batch?.failedCount || 0,
        currentProspect: 'John Doe',
        estimatedTimeRemaining: 120,
        errors: [],
      }
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
          All Prospects
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
