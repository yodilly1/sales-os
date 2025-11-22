import type {
  SingleLookupRequest,
  SingleLookupResponse,
  BulkUploadResponse,
  EnrichmentProgress,
  EnrichmentBatch,
  Prospect,
  Company,
  CRMSyncRequest,
  CRMSyncResponse,
  ProspectFilters,
  SortConfig,
  ExportRequest,
  ExportFormat,
} from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new ApiError(
      errorData?.message || `Request failed with status ${response.status}`,
      response.status,
      errorData
    )
  }

  return response.json()
}

// Single prospect lookup
export async function lookupProspect(
  request: SingleLookupRequest
): Promise<SingleLookupResponse> {
  return fetchApi<SingleLookupResponse>('/enrichment/lookup', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Bulk upload
export async function uploadBulkFile(
  file: File,
  name: string
): Promise<BulkUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', name)

  const url = `${API_BASE_URL}/enrichment/bulk`
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new ApiError(
      errorData?.message || 'Failed to upload file',
      response.status,
      errorData
    )
  }

  return response.json()
}

// Get enrichment progress for a batch
export async function getEnrichmentProgress(
  batchId: string
): Promise<EnrichmentProgress> {
  return fetchApi<EnrichmentProgress>(`/enrichment/progress/${batchId}`)
}

// Get batch results
export async function getBatchResults(batchId: string): Promise<EnrichmentBatch> {
  return fetchApi<EnrichmentBatch>(`/enrichment/results/${batchId}`)
}

// List all batches
export async function listBatches(params?: {
  status?: string
  limit?: number
  offset?: number
}): Promise<{ batches: EnrichmentBatch[]; total: number }> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  return fetchApi(`/enrichment/batches${query ? `?${query}` : ''}`)
}

// Get all prospects with filtering and sorting
export async function getProspects(params?: {
  filters?: ProspectFilters
  sort?: SortConfig
  limit?: number
  offset?: number
}): Promise<{ prospects: Prospect[]; total: number }> {
  const searchParams = new URLSearchParams()

  if (params?.filters) {
    if (params.filters.search) searchParams.set('search', params.filters.search)
    if (params.filters.enrichmentStatus?.length) {
      searchParams.set('enrichmentStatus', params.filters.enrichmentStatus.join(','))
    }
    if (params.filters.crmSyncStatus?.length) {
      searchParams.set('crmSyncStatus', params.filters.crmSyncStatus.join(','))
    }
    if (params.filters.company) searchParams.set('company', params.filters.company)
    if (params.filters.industry) searchParams.set('industry', params.filters.industry)
    if (params.filters.companySize?.length) {
      searchParams.set('companySize', params.filters.companySize.join(','))
    }
    if (params.filters.dateRange) {
      searchParams.set('startDate', params.filters.dateRange.start)
      searchParams.set('endDate', params.filters.dateRange.end)
    }
  }

  if (params?.sort) {
    searchParams.set('sortBy', params.sort.field)
    searchParams.set('sortDir', params.sort.direction)
  }

  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  return fetchApi(`/enrichment/prospects${query ? `?${query}` : ''}`)
}

// Get single prospect by ID
export async function getProspect(id: string): Promise<Prospect> {
  return fetchApi<Prospect>(`/enrichment/prospects/${id}`)
}

// Get company by ID
export async function getCompany(id: string): Promise<Company> {
  return fetchApi<Company>(`/enrichment/companies/${id}`)
}

// Sync prospects to CRM
export async function syncToCRM(request: CRMSyncRequest): Promise<CRMSyncResponse> {
  return fetchApi<CRMSyncResponse>('/enrichment/sync-crm', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Re-enrich a prospect
export async function reEnrichProspect(prospectId: string): Promise<Prospect> {
  return fetchApi<Prospect>(`/enrichment/prospects/${prospectId}/re-enrich`, {
    method: 'POST',
  })
}

// Cancel a batch
export async function cancelBatch(batchId: string): Promise<void> {
  await fetchApi(`/enrichment/batches/${batchId}/cancel`, {
    method: 'POST',
  })
}

// Export prospects
export async function exportProspects(
  request: ExportRequest
): Promise<{ downloadUrl: string }> {
  return fetchApi('/enrichment/export', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// Generate export content locally (for client-side export)
export function generateExportContent(
  prospects: Prospect[],
  companies: Map<string, Company>,
  format: ExportFormat,
  includeCompanyData: boolean
): string {
  if (format === 'json') {
    const data = prospects.map(p => ({
      ...p,
      company: includeCompanyData && p.companyId ? companies.get(p.companyId) : undefined,
    }))
    return JSON.stringify(data, null, 2)
  }

  // CSV format
  const headers = [
    'Name',
    'Email',
    'Title',
    'Company',
    'Phone',
    'LinkedIn URL',
    'Location',
    'Enrichment Status',
    'CRM Sync Status',
    'Last Enriched',
  ]

  if (includeCompanyData) {
    headers.push(
      'Company Industry',
      'Company Size',
      'Company Website',
      'Company Funding'
    )
  }

  const rows = prospects.map(p => {
    const company = p.companyId ? companies.get(p.companyId) : null
    const row = [
      p.name,
      p.email || '',
      p.title || '',
      p.company || '',
      p.phone || '',
      p.linkedinUrl || '',
      p.location || '',
      p.enrichmentStatus,
      p.crmSyncStatus,
      p.lastEnrichedAt || '',
    ]

    if (includeCompanyData) {
      row.push(
        company?.industry || '',
        company?.size || '',
        company?.website || '',
        company?.funding?.totalRaised || ''
      )
    }

    return row
  })

  const escapeCSV = (value: string) => {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`
    }
    return value
  }

  return [
    headers.join(','),
    ...rows.map(row => row.map(escapeCSV).join(',')),
  ].join('\n')
}
