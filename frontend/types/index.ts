// Prospect types
export interface Prospect {
  id: string
  name: string
  email: string | null
  title: string | null
  company: string | null
  companyId: string | null
  phone: string | null
  linkedinUrl: string | null
  location: string | null
  enrichmentStatus: EnrichmentStatus
  enrichmentData: EnrichmentData | null
  crmSyncStatus: CRMSyncStatus
  crmId: string | null
  lastEnrichedAt: string | null
  createdAt: string
  updatedAt: string
}

export interface EnrichmentData {
  verifiedEmail: string | null
  verifiedPhone: string | null
  linkedinProfile: LinkedInProfile | null
  recentActivity: ActivityItem[]
  confidence: number // 0-100
}

export interface LinkedInProfile {
  url: string
  headline: string | null
  summary: string | null
  connections: number | null
  profileImageUrl: string | null
}

export interface ActivityItem {
  type: 'news' | 'post' | 'job_change' | 'funding' | 'event'
  title: string
  date: string
  url: string | null
  source: string
}

// Company types
export interface Company {
  id: string
  name: string
  domain: string | null
  industry: string | null
  size: CompanySize | null
  employeeCount: number | null
  revenue: string | null
  funding: FundingInfo | null
  techStack: string[]
  headquarters: string | null
  website: string | null
  linkedinUrl: string | null
  description: string | null
  logoUrl: string | null
  lastEnrichedAt: string | null
  createdAt: string
  updatedAt: string
}

export interface FundingInfo {
  totalRaised: string | null
  lastRoundType: string | null
  lastRoundAmount: string | null
  lastRoundDate: string | null
  investors: string[]
}

export type CompanySize =
  | '1-10'
  | '11-50'
  | '51-200'
  | '201-500'
  | '501-1000'
  | '1001-5000'
  | '5001-10000'
  | '10000+'

// Enrichment types
export type EnrichmentStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'partial'

export type CRMSyncStatus =
  | 'not_synced'
  | 'synced'
  | 'pending'
  | 'failed'
  | 'out_of_sync'

export interface EnrichmentBatch {
  id: string
  name: string
  type: 'csv' | 'event_list' | 'manual'
  status: BatchStatus
  totalCount: number
  completedCount: number
  failedCount: number
  createdAt: string
  updatedAt: string
  completedAt: string | null
  prospects: Prospect[]
}

export type BatchStatus =
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface EnrichmentProgress {
  batchId: string
  status: BatchStatus
  totalCount: number
  completedCount: number
  failedCount: number
  currentProspect: string | null
  estimatedTimeRemaining: number | null // seconds
  errors: EnrichmentError[]
}

export interface EnrichmentError {
  prospectId: string
  prospectName: string
  error: string
  timestamp: string
}

// API Request/Response types
export interface SingleLookupRequest {
  name: string
  email?: string
  company?: string
  title?: string
  linkedinUrl?: string
}

export interface SingleLookupResponse {
  success: boolean
  prospect: Prospect | null
  company: Company | null
  error: string | null
}

export interface BulkUploadRequest {
  file: File
  name: string
}

export interface BulkUploadResponse {
  success: boolean
  batchId: string
  totalRecords: number
  validRecords: number
  invalidRecords: number
  errors: string[]
}

export interface CRMSyncRequest {
  prospectIds: string[]
  targetCRM: 'hubspot' | 'salesforce'
}

export interface CRMSyncResponse {
  success: boolean
  syncedCount: number
  failedCount: number
  errors: {
    prospectId: string
    error: string
  }[]
}

// Filter and sort types
export interface ProspectFilters {
  search?: string
  enrichmentStatus?: EnrichmentStatus[]
  crmSyncStatus?: CRMSyncStatus[]
  company?: string
  industry?: string
  companySize?: CompanySize[]
  dateRange?: {
    start: string
    end: string
  }
}

export interface SortConfig {
  field: keyof Prospect | 'company.name' | 'company.industry'
  direction: 'asc' | 'desc'
}

// Export types
export type ExportFormat = 'csv' | 'xlsx' | 'json'

export interface ExportRequest {
  prospectIds: string[]
  format: ExportFormat
  includeCompanyData: boolean
  fields?: string[]
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  SALES_REP = 'sales_rep',
  VIEWER = 'viewer',
}

export enum InvitationStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  EXPIRED = 'expired',
  REVOKED = 'revoked',
}
