/**
 * Talk Track API Client
 *
 * Client library for interacting with the Talk Track API endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Types
// =============================================================================

export interface ProspectContext {
  name?: string;
  title?: string;
  company?: string;
  company_size?: string;
  industry?: string;
  known_pain_points?: string[];
  previous_interactions?: string;
}

export interface ProductContext {
  name?: string;
  key_features?: string[];
  value_propositions?: string[];
  differentiators?: string[];
  pricing_info?: string;
}

export interface ObjectionContext {
  objection: string;
  objection_category?: string;
  competitor_mentioned?: string;
}

export interface TalkTrackRequest {
  script_type: string;
  persona: string;
  industry: string;
  deal_stage: string;
  prospect?: ProspectContext;
  product?: ProductContext;
  objection?: ObjectionContext;
  spiced_context?: Record<string, string>;
  tone?: string;
  call_duration_minutes?: number;
  generate_variants?: boolean;
  include_coaching_notes?: boolean;
}

export interface ScriptSection {
  name: string;
  duration_seconds?: number;
  content: string;
  coaching_notes?: string;
  spiced_elements?: string[];
  transition_phrase?: string;
}

export interface DiscoveryQuestion {
  question: string;
  spiced_element: string;
  follow_up_questions?: string[];
  what_to_listen_for: string;
  coaching_tip?: string;
}

export interface ObjectionResponse {
  objection: string;
  category: string;
  response: string;
  acknowledge_phrase: string;
  reframe_strategy: string;
  transition_to_value: string;
  proof_points?: string[];
}

export interface TalkTrack {
  id: string;
  script_type: string;
  version: string;
  variant?: string;
  title: string;
  description?: string;
  persona: string;
  industry: string;
  deal_stage: string;
  opening: ScriptSection;
  sections: ScriptSection[];
  closing: ScriptSection;
  discovery_questions?: DiscoveryQuestion[];
  objection_responses?: ObjectionResponse[];
  key_tips?: string[];
  common_mistakes?: string[];
  success_metrics?: string[];
  total_duration_minutes?: number;
  created_at: string;
  updated_at: string;
}

export interface TalkTrackResponse {
  primary: TalkTrack;
  variants: TalkTrack[];
  generation_metadata: Record<string, unknown>;
}

export interface TalkTrackLibraryItem {
  id: string;
  title: string;
  script_type: string;
  persona: string;
  industry: string;
  version: string;
  total_uses: number;
  average_rating: number | null;
  created_at: string;
  updated_at: string;
}

export interface TalkTrackLibraryResponse {
  items: TalkTrackLibraryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScriptPerformanceMetrics {
  talktrack_id: string;
  total_uses: number;
  unique_users: number;
  meetings_scheduled_rate: number;
  deal_advancement_rate: number;
  average_call_duration?: number;
  variant_performance?: Record<string, Record<string, unknown>>;
  average_rating?: number;
  period_start: string;
  period_end: string;
}

export interface UsageEventRequest {
  talktrack_id: string;
  user_id: string;
  deal_id?: string;
  call_duration_minutes?: number;
  variant_used?: string;
  outcome?: string;
  next_step_scheduled?: boolean;
  deal_advanced?: boolean;
  user_rating?: number;
  user_notes?: string;
}

// =============================================================================
// API Functions
// =============================================================================

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Generate a new talk track
 */
export async function generateTalkTrack(
  request: TalkTrackRequest
): Promise<TalkTrackResponse> {
  const response = await apiRequest<{ success: boolean; data: TalkTrackResponse }>(
    '/api/talktracks/generate',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
  return response.data;
}

/**
 * Get a specific talk track by ID
 */
export async function getTalkTrack(id: string): Promise<TalkTrack> {
  return apiRequest<TalkTrack>(`/api/talktracks/library/${id}`);
}

/**
 * Get talk track library with optional filters
 */
export async function getTalkTrackLibrary(params: {
  script_type?: string;
  persona?: string;
  industry?: string;
  page?: number;
  page_size?: number;
} = {}): Promise<TalkTrackLibraryResponse> {
  const searchParams = new URLSearchParams();

  if (params.script_type) searchParams.set('script_type', params.script_type);
  if (params.persona) searchParams.set('persona', params.persona);
  if (params.industry) searchParams.set('industry', params.industry);
  if (params.page) searchParams.set('page', params.page.toString());
  if (params.page_size) searchParams.set('page_size', params.page_size.toString());

  const query = searchParams.toString();
  return apiRequest<TalkTrackLibraryResponse>(
    `/api/talktracks/library${query ? `?${query}` : ''}`
  );
}

/**
 * Get recommended talk tracks based on context
 */
export async function getRecommendations(params: {
  script_type: string;
  persona: string;
  industry: string;
  deal_stage?: string;
}): Promise<TalkTrackLibraryItem[]> {
  const searchParams = new URLSearchParams({
    script_type: params.script_type,
    persona: params.persona,
    industry: params.industry,
  });

  if (params.deal_stage) searchParams.set('deal_stage', params.deal_stage);

  return apiRequest<TalkTrackLibraryItem[]>(
    `/api/talktracks/recommendations?${searchParams}`
  );
}

/**
 * Record a talk track usage event
 */
export async function recordUsage(event: UsageEventRequest): Promise<{ success: boolean; event_id: string }> {
  return apiRequest('/api/talktracks/usage', {
    method: 'POST',
    body: JSON.stringify(event),
  });
}

/**
 * Get performance metrics for a talk track
 */
export async function getPerformanceMetrics(
  talkTrackId: string,
  periodDays: number = 30
): Promise<ScriptPerformanceMetrics> {
  return apiRequest<ScriptPerformanceMetrics>(
    `/api/talktracks/performance/${talkTrackId}?period_days=${periodDays}`
  );
}

/**
 * Get performance trends for a talk track
 */
export async function getTrends(
  talkTrackId: string,
  periodDays: number = 90,
  intervalDays: number = 7
): Promise<{
  talktrack_id: string;
  period_days: number;
  interval_days: number;
  data_points: Array<{
    period_start: string;
    period_end: string;
    total_uses: number;
    meetings_scheduled_rate: number;
    deal_advancement_rate: number;
  }>;
}> {
  return apiRequest(
    `/api/talktracks/performance/${talkTrackId}/trends?period_days=${periodDays}&interval_days=${intervalDays}`
  );
}

/**
 * Get A/B test results for a talk track
 */
export async function getABTestResults(
  talkTrackId: string,
  periodDays: number = 30
): Promise<{
  talktrack_id: string;
  period_days: number;
  variants: Array<{
    variant: string;
    total_uses: number;
    meetings_scheduled_rate: number;
    deal_advancement_rate: number;
    average_rating: number | null;
    is_winner: boolean;
  }>;
}> {
  return apiRequest(
    `/api/talktracks/performance/${talkTrackId}/ab-test?period_days=${periodDays}`
  );
}

/**
 * Get best performing talk tracks
 */
export async function getBestPerformers(params: {
  script_type?: string;
  persona?: string;
  industry?: string;
  limit?: number;
} = {}): Promise<TalkTrackLibraryItem[]> {
  const searchParams = new URLSearchParams();

  if (params.script_type) searchParams.set('script_type', params.script_type);
  if (params.persona) searchParams.set('persona', params.persona);
  if (params.industry) searchParams.set('industry', params.industry);
  if (params.limit) searchParams.set('limit', params.limit.toString());

  const query = searchParams.toString();
  return apiRequest<TalkTrackLibraryItem[]>(
    `/api/talktracks/best-performers${query ? `?${query}` : ''}`
  );
}

/**
 * Get available script types
 */
export async function getScriptTypes(): Promise<{
  script_types: Array<{ value: string; name: string; description: string }>;
}> {
  return apiRequest('/api/talktracks/types');
}

/**
 * Get available personas
 */
export async function getPersonas(): Promise<{
  personas: Array<{ value: string; name: string; description: string }>;
}> {
  return apiRequest('/api/talktracks/personas');
}

/**
 * Get available industries
 */
export async function getIndustries(): Promise<{
  industries: Array<{ value: string; name: string }>;
}> {
  return apiRequest('/api/talktracks/industries');
}

/**
 * Health check for talk track service
 */
export async function healthCheck(): Promise<{
  status: string;
  service: string;
  version: string;
}> {
  return apiRequest('/api/talktracks/health');
}
