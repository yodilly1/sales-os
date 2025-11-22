// Common types for analytics data

export interface DateRange {
  startDate: string
  endDate: string
}

export interface MetricValue {
  value: number
  change: number
  changePercent: number
  trend: 'up' | 'down' | 'stable'
}

// Call Analytics Types
export interface CallMetrics {
  totalCalls: MetricValue
  avgDuration: MetricValue
  avgSpicedScore: MetricValue
  conversionRate: MetricValue
}

export interface CallVolumeData {
  date: string
  calls: number
  answered: number
  missed: number
}

export interface CallDurationData {
  date: string
  avgDuration: number
  minDuration: number
  maxDuration: number
}

export interface SpicedScoreData {
  date: string
  situation: number
  pain: number
  impact: number
  criticalEvent: number
  decision: number
  overall: number
}

export interface SpicedDistribution {
  range: string
  count: number
  percentage: number
}

// Content Analytics Types
export interface ContentMetrics {
  totalGenerated: MetricValue
  totalDownloaded: MetricValue
  totalShared: MetricValue
  engagementRate: MetricValue
}

export interface ContentTypeData {
  type: string
  generated: number
  downloaded: number
  shared: number
}

export interface ContentTrendData {
  date: string
  generated: number
  downloaded: number
  shared: number
}

export interface ContentPerformance {
  id: string
  title: string
  type: string
  generatedAt: string
  downloads: number
  shares: number
  views: number
}

// Pipeline Analytics Types
export interface PipelineMetrics {
  prospectsEnriched: MetricValue
  conversionRate: MetricValue
  avgDealSize: MetricValue
  pipelineValue: MetricValue
}

export interface PipelineStageData {
  stage: string
  count: number
  value: number
  conversionRate: number
}

export interface EnrichmentTrendData {
  date: string
  enriched: number
  converted: number
  value: number
}

export interface ProspectSource {
  source: string
  count: number
  conversionRate: number
  avgDealSize: number
}

// Team Performance Types
export interface TeamMetrics {
  totalMembers: number
  avgCallsPerRep: MetricValue
  avgContentPerRep: MetricValue
  avgDealsPerRep: MetricValue
}

export interface TeamMemberPerformance {
  id: string
  name: string
  avatar?: string
  calls: number
  contentGenerated: number
  prospectsEnriched: number
  dealsWon: number
  dealValue: number
  spicedScore: number
  rank: number
  trend: 'up' | 'down' | 'stable'
}

export interface TeamTrendData {
  date: string
  calls: number
  content: number
  deals: number
}

export interface LeaderboardEntry {
  rank: number
  userId: string
  name: string
  avatar?: string
  metric: number
  change: number
}

// Export Types
export interface ExportOptions {
  format: 'csv' | 'pdf'
  dateRange: DateRange
  metrics: string[]
}

// API Response Types
export interface AnalyticsResponse<T> {
  data: T
  dateRange: DateRange
  generatedAt: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}
