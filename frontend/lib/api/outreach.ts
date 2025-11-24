import type {
  GenerateCampaignRequest,
  GenerateCampaignResponse,
  BulkGenerateRequest,
  BulkGenerateResponse,
  OutreachCampaign,
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

/**
 * Generate an outreach campaign for a single prospect
 */
export async function generateCampaign(
  request: GenerateCampaignRequest
): Promise<GenerateCampaignResponse> {
  return fetchApi<GenerateCampaignResponse>('/v1/outreach/generate', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Generate outreach campaigns for multiple prospects
 */
export async function generateBulkCampaigns(
  request: BulkGenerateRequest
): Promise<BulkGenerateResponse> {
  return fetchApi<BulkGenerateResponse>('/v1/outreach/generate/bulk', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Get campaign details by ID
 */
export async function getCampaign(campaignId: string): Promise<OutreachCampaign> {
  return fetchApi<OutreachCampaign>(`/v1/outreach/campaign/${campaignId}`)
}

/**
 * Download Instantly CSV for a campaign
 */
export function getInstantlyExportUrl(campaignId: string): string {
  return `${API_BASE_URL}/v1/outreach/export/instantly/${campaignId}`
}

/**
 * Download HeyReach CSV for a campaign
 */
export function getHeyReachExportUrl(campaignId: string): string {
  return `${API_BASE_URL}/v1/outreach/export/heyreach/${campaignId}`
}

/**
 * Download Instantly CSV and trigger browser download
 */
export async function downloadInstantlyCSV(campaignId: string, filename?: string): Promise<void> {
  const url = getInstantlyExportUrl(campaignId)
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to download CSV', response.status)
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename || `instantly_campaign_${campaignId.slice(0, 8)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(downloadUrl)
}

/**
 * Download HeyReach CSV and trigger browser download
 */
export async function downloadHeyReachCSV(campaignId: string, filename?: string): Promise<void> {
  const url = getHeyReachExportUrl(campaignId)
  const response = await fetch(url)

  if (!response.ok) {
    throw new ApiError('Failed to download CSV', response.status)
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename || `heyreach_campaign_${campaignId.slice(0, 8)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(downloadUrl)
}

/**
 * Bulk export campaigns to Instantly CSV
 */
export async function downloadBulkInstantlyCSV(
  campaignIds: string[],
  filename?: string
): Promise<void> {
  const url = `${API_BASE_URL}/v1/outreach/export/instantly/bulk`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campaignIds),
  })

  if (!response.ok) {
    throw new ApiError('Failed to download CSV', response.status)
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename || 'instantly_campaigns_bulk.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(downloadUrl)
}

/**
 * Bulk export campaigns to HeyReach CSV
 */
export async function downloadBulkHeyReachCSV(
  campaignIds: string[],
  filename?: string
): Promise<void> {
  const url = `${API_BASE_URL}/v1/outreach/export/heyreach/bulk`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campaignIds),
  })

  if (!response.ok) {
    throw new ApiError('Failed to download CSV', response.status)
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename || 'heyreach_campaigns_bulk.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(downloadUrl)
}
