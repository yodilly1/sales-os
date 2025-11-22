import { apiGet, buildQueryParams } from './client'
import type {
  DateRange,
  CallMetrics,
  CallVolumeData,
  CallDurationData,
  SpicedScoreData,
  SpicedDistribution,
  ContentMetrics,
  ContentTypeData,
  ContentTrendData,
  ContentPerformance,
  PipelineMetrics,
  PipelineStageData,
  EnrichmentTrendData,
  ProspectSource,
  TeamMetrics,
  TeamMemberPerformance,
  TeamTrendData,
  LeaderboardEntry,
  AnalyticsResponse,
  PaginatedResponse,
} from '@/lib/types/analytics'

// ============================================
// Call Analytics API
// ============================================

export async function getCallMetrics(dateRange: DateRange): Promise<AnalyticsResponse<CallMetrics>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<CallMetrics>>('/api/analytics/calls/metrics', params)
}

export async function getCallVolume(dateRange: DateRange): Promise<AnalyticsResponse<CallVolumeData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<CallVolumeData[]>>('/api/analytics/calls/volume', params)
}

export async function getCallDuration(dateRange: DateRange): Promise<AnalyticsResponse<CallDurationData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<CallDurationData[]>>('/api/analytics/calls/duration', params)
}

export async function getSpicedScores(dateRange: DateRange): Promise<AnalyticsResponse<SpicedScoreData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<SpicedScoreData[]>>('/api/analytics/calls/spiced-scores', params)
}

export async function getSpicedDistribution(dateRange: DateRange): Promise<AnalyticsResponse<SpicedDistribution[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<SpicedDistribution[]>>('/api/analytics/calls/spiced-distribution', params)
}

// ============================================
// Content Analytics API
// ============================================

export async function getContentMetrics(dateRange: DateRange): Promise<AnalyticsResponse<ContentMetrics>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<ContentMetrics>>('/api/analytics/content/metrics', params)
}

export async function getContentByType(dateRange: DateRange): Promise<AnalyticsResponse<ContentTypeData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<ContentTypeData[]>>('/api/analytics/content/by-type', params)
}

export async function getContentTrends(dateRange: DateRange): Promise<AnalyticsResponse<ContentTrendData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<ContentTrendData[]>>('/api/analytics/content/trends', params)
}

export async function getTopContent(
  dateRange: DateRange,
  page = 1,
  pageSize = 10
): Promise<PaginatedResponse<ContentPerformance>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    page,
    pageSize,
  })
  return apiGet<PaginatedResponse<ContentPerformance>>('/api/analytics/content/top', params)
}

// ============================================
// Pipeline Analytics API
// ============================================

export async function getPipelineMetrics(dateRange: DateRange): Promise<AnalyticsResponse<PipelineMetrics>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<PipelineMetrics>>('/api/analytics/pipeline/metrics', params)
}

export async function getPipelineStages(dateRange: DateRange): Promise<AnalyticsResponse<PipelineStageData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<PipelineStageData[]>>('/api/analytics/pipeline/stages', params)
}

export async function getEnrichmentTrends(dateRange: DateRange): Promise<AnalyticsResponse<EnrichmentTrendData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<EnrichmentTrendData[]>>('/api/analytics/pipeline/enrichment-trends', params)
}

export async function getProspectSources(dateRange: DateRange): Promise<AnalyticsResponse<ProspectSource[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<ProspectSource[]>>('/api/analytics/pipeline/sources', params)
}

// ============================================
// Team Performance API
// ============================================

export async function getTeamMetrics(dateRange: DateRange): Promise<AnalyticsResponse<TeamMetrics>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<TeamMetrics>>('/api/analytics/team/metrics', params)
}

export async function getTeamPerformance(
  dateRange: DateRange,
  sortBy = 'deals',
  page = 1,
  pageSize = 10
): Promise<PaginatedResponse<TeamMemberPerformance>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    sortBy,
    page,
    pageSize,
  })
  return apiGet<PaginatedResponse<TeamMemberPerformance>>('/api/analytics/team/performance', params)
}

export async function getTeamTrends(dateRange: DateRange): Promise<AnalyticsResponse<TeamTrendData[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
  })
  return apiGet<AnalyticsResponse<TeamTrendData[]>>('/api/analytics/team/trends', params)
}

export async function getLeaderboard(
  dateRange: DateRange,
  metric: 'calls' | 'content' | 'deals' | 'spiced'
): Promise<AnalyticsResponse<LeaderboardEntry[]>> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    metric,
  })
  return apiGet<AnalyticsResponse<LeaderboardEntry[]>>('/api/analytics/team/leaderboard', params)
}

// ============================================
// Export API
// ============================================

export async function exportAnalytics(
  type: 'calls' | 'content' | 'pipeline' | 'team',
  dateRange: DateRange,
  format: 'csv' | 'pdf'
): Promise<Blob> {
  const params = buildQueryParams({
    startDate: dateRange.startDate,
    endDate: dateRange.endDate,
    format,
  })

  const url = new URL(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/analytics/${type}/export`)
  Object.entries(params).forEach(([key, value]) => url.searchParams.append(key, value))

  const response = await fetch(url.toString(), {
    method: 'GET',
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error('Export failed')
  }

  return response.blob()
}
