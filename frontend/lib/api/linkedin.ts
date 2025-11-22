/**
 * LinkedIn API Client
 *
 * TypeScript client for interacting with the LinkedIn integration API.
 */

// ==================== Types ====================

export type ConnectionStatus =
  | 'not_connected'
  | 'pending_sent'
  | 'pending_received'
  | 'connected'
  | 'following';

export type OutreachType =
  | 'connection_request'
  | 'inmail'
  | 'message'
  | 'comment'
  | 'like'
  | 'share'
  | 'profile_view';

export type OutreachStatus =
  | 'pending'
  | 'sent'
  | 'delivered'
  | 'read'
  | 'replied'
  | 'accepted'
  | 'declined'
  | 'expired';

export type ActivityType =
  | 'post'
  | 'article'
  | 'reaction'
  | 'comment'
  | 'share'
  | 'job_change'
  | 'promotion'
  | 'work_anniversary'
  | 'new_connection';

export interface LinkedInExperience {
  title: string;
  company_name: string;
  company_linkedin_url?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  is_current: boolean;
  description?: string;
}

export interface LinkedInEducation {
  school_name: string;
  school_linkedin_url?: string;
  degree?: string;
  field_of_study?: string;
  start_year?: number;
  end_year?: number;
  description?: string;
}

export interface LinkedInSkill {
  name: string;
  endorsement_count: number;
}

export interface LinkedInProfile {
  linkedin_id?: string;
  linkedin_url: string;
  first_name: string;
  last_name: string;
  headline?: string;
  summary?: string;
  location?: string;
  country?: string;
  industry?: string;
  profile_picture_url?: string;
  banner_image_url?: string;
  current_title?: string;
  current_company?: string;
  current_company_linkedin_url?: string;
  email?: string;
  phone?: string;
  website?: string;
  twitter_handle?: string;
  connections_count?: number;
  followers_count?: number;
  experiences: LinkedInExperience[];
  education: LinkedInEducation[];
  skills: LinkedInSkill[];
  languages: string[];
  is_open_to_work: boolean;
  is_hiring: boolean;
  is_creator: boolean;
  connection_status: ConnectionStatus;
  last_enriched_at?: string;
  enrichment_source?: string;
}

export interface LinkedInProfileSummary {
  linkedin_url: string;
  first_name: string;
  last_name: string;
  headline?: string;
  current_company?: string;
  location?: string;
  profile_picture_url?: string;
  connection_status: ConnectionStatus;
}

export interface LinkedInCompany {
  linkedin_id?: string;
  linkedin_url: string;
  name: string;
  tagline?: string;
  description?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  employee_count?: number;
  headquarters_location?: string;
  headquarters_city?: string;
  headquarters_country?: string;
  founded_year?: number;
  company_type?: string;
  specialties: string[];
  logo_url?: string;
  followers_count?: number;
  last_enriched_at?: string;
  enrichment_source?: string;
}

export interface OutreachActivity {
  id: string;
  prospect_linkedin_url: string;
  prospect_name?: string;
  outreach_type: OutreachType;
  status: OutreachStatus;
  message_content?: string;
  subject?: string;
  created_at: string;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  replied_at?: string;
  response_content?: string;
  campaign_id?: string;
  sequence_step?: number;
  is_sales_navigator: boolean;
}

export interface OutreachCampaign {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  start_date?: string;
  end_date?: string;
  target_profiles: string[];
  message_templates: string[];
  total_prospects: number;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  replied_count: number;
  accepted_count: number;
  created_at: string;
  updated_at?: string;
}

export interface LinkedInActivity {
  id: string;
  profile_linkedin_url: string;
  activity_type: ActivityType;
  activity_url?: string;
  content_text?: string;
  likes_count: number;
  comments_count: number;
  shares_count: number;
  old_title?: string;
  old_company?: string;
  new_title?: string;
  new_company?: string;
  activity_date: string;
  discovered_at: string;
}

export interface ConnectionRecord {
  id: string;
  prospect_linkedin_url: string;
  prospect_name?: string;
  previous_status: ConnectionStatus;
  new_status: ConnectionStatus;
  changed_at: string;
  connection_note?: string;
}

export interface EnrichmentResponse {
  success: boolean;
  profile?: LinkedInProfile;
  company?: LinkedInCompany;
  error_message?: string;
  cached: boolean;
  enrichment_source?: string;
}

export interface BulkEnrichmentResponse {
  total_requested: number;
  successful: number;
  failed: number;
  results: EnrichmentResponse[];
}

export interface ProfileMatchResponse {
  matched: boolean;
  confidence_score: number;
  prospect_id?: string;
  profile?: LinkedInProfileSummary;
  match_reasons: string[];
}

export interface OutreachAnalytics {
  total_outreach: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  reply_rate: number;
  acceptance_rate: number;
  period_days: number;
}

// ==================== API Client ====================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}/linkedin${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ==================== Profile Enrichment ====================

export async function enrichProfile(
  linkedinUrl: string,
  options: {
    forceRefresh?: boolean;
    includeExperiences?: boolean;
    includeEducation?: boolean;
    includeSkills?: boolean;
  } = {}
): Promise<EnrichmentResponse> {
  return fetchAPI<EnrichmentResponse>('/profiles/enrich', {
    method: 'POST',
    body: JSON.stringify({
      linkedin_url: linkedinUrl,
      force_refresh: options.forceRefresh ?? false,
      include_experiences: options.includeExperiences ?? true,
      include_education: options.includeEducation ?? true,
      include_skills: options.includeSkills ?? true,
    }),
  });
}

export async function bulkEnrichProfiles(
  linkedinUrls: string[],
  forceRefresh = false
): Promise<BulkEnrichmentResponse> {
  return fetchAPI<BulkEnrichmentResponse>('/profiles/enrich/bulk', {
    method: 'POST',
    body: JSON.stringify({
      linkedin_urls: linkedinUrls,
      force_refresh: forceRefresh,
    }),
  });
}

export async function getProfile(
  username: string,
  forceRefresh = false
): Promise<EnrichmentResponse> {
  const params = new URLSearchParams();
  if (forceRefresh) params.set('force_refresh', 'true');
  return fetchAPI<EnrichmentResponse>(
    `/profiles/${username}?${params.toString()}`
  );
}

// ==================== Company Enrichment ====================

export async function enrichCompany(
  linkedinUrl: string,
  options: {
    forceRefresh?: boolean;
    includeKeyEmployees?: boolean;
  } = {}
): Promise<EnrichmentResponse> {
  return fetchAPI<EnrichmentResponse>('/companies/enrich', {
    method: 'POST',
    body: JSON.stringify({
      linkedin_url: linkedinUrl,
      force_refresh: options.forceRefresh ?? false,
      include_key_employees: options.includeKeyEmployees ?? false,
    }),
  });
}

export async function getCompany(
  slug: string,
  forceRefresh = false
): Promise<EnrichmentResponse> {
  const params = new URLSearchParams();
  if (forceRefresh) params.set('force_refresh', 'true');
  return fetchAPI<EnrichmentResponse>(
    `/companies/${slug}?${params.toString()}`
  );
}

// ==================== Outreach Tracking ====================

export async function trackOutreach(data: {
  prospectLinkedinUrl: string;
  outreachType: OutreachType;
  messageContent?: string;
  subject?: string;
  campaignId?: string;
  isSalesNavigator?: boolean;
}): Promise<OutreachActivity> {
  return fetchAPI<OutreachActivity>('/outreach/track', {
    method: 'POST',
    body: JSON.stringify({
      prospect_linkedin_url: data.prospectLinkedinUrl,
      outreach_type: data.outreachType,
      message_content: data.messageContent,
      subject: data.subject,
      campaign_id: data.campaignId,
      is_sales_navigator: data.isSalesNavigator ?? false,
    }),
  });
}

export async function updateOutreachStatus(
  activityId: string,
  status: OutreachStatus,
  responseContent?: string
): Promise<OutreachActivity> {
  return fetchAPI<OutreachActivity>(`/outreach/${activityId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({
      status,
      response_content: responseContent,
    }),
  });
}

export async function listOutreachActivities(filters: {
  prospectLinkedinUrl?: string;
  campaignId?: string;
  outreachType?: OutreachType;
  limit?: number;
} = {}): Promise<OutreachActivity[]> {
  const params = new URLSearchParams();
  if (filters.prospectLinkedinUrl)
    params.set('prospect_linkedin_url', filters.prospectLinkedinUrl);
  if (filters.campaignId) params.set('campaign_id', filters.campaignId);
  if (filters.outreachType) params.set('outreach_type', filters.outreachType);
  if (filters.limit) params.set('limit', filters.limit.toString());
  return fetchAPI<OutreachActivity[]>(`/outreach?${params.toString()}`);
}

export async function getOutreachAnalytics(
  campaignId?: string,
  days = 30
): Promise<OutreachAnalytics> {
  const params = new URLSearchParams();
  if (campaignId) params.set('campaign_id', campaignId);
  params.set('days', days.toString());
  return fetchAPI<OutreachAnalytics>(
    `/outreach/analytics?${params.toString()}`
  );
}

// ==================== Connection Tracking ====================

export async function updateConnectionStatus(
  prospectLinkedinUrl: string,
  status: ConnectionStatus,
  note?: string
): Promise<ConnectionRecord> {
  return fetchAPI<ConnectionRecord>('/connections/status', {
    method: 'POST',
    body: JSON.stringify({
      prospect_linkedin_url: prospectLinkedinUrl,
      status,
      note,
    }),
  });
}

export async function getConnectionStatus(
  prospectLinkedinUrl: string
): Promise<{ status: ConnectionStatus }> {
  const params = new URLSearchParams({
    prospect_linkedin_url: prospectLinkedinUrl,
  });
  return fetchAPI<{ status: ConnectionStatus }>(
    `/connections/status?${params.toString()}`
  );
}

export async function getConnectionHistory(
  prospectLinkedinUrl: string
): Promise<ConnectionRecord[]> {
  const params = new URLSearchParams({
    prospect_linkedin_url: prospectLinkedinUrl,
  });
  return fetchAPI<ConnectionRecord[]>(
    `/connections/history?${params.toString()}`
  );
}

// ==================== Campaign Management ====================

export async function createCampaign(data: {
  name: string;
  description?: string;
  targetProfiles?: string[];
  messageTemplates?: string[];
}): Promise<OutreachCampaign> {
  return fetchAPI<OutreachCampaign>('/campaigns', {
    method: 'POST',
    body: JSON.stringify({
      name: data.name,
      description: data.description,
      target_profiles: data.targetProfiles,
      message_templates: data.messageTemplates,
    }),
  });
}

export async function listCampaigns(
  activeOnly = false
): Promise<OutreachCampaign[]> {
  const params = new URLSearchParams();
  if (activeOnly) params.set('active_only', 'true');
  return fetchAPI<OutreachCampaign[]>(`/campaigns?${params.toString()}`);
}

export async function getCampaign(campaignId: string): Promise<OutreachCampaign> {
  return fetchAPI<OutreachCampaign>(`/campaigns/${campaignId}`);
}

export async function updateCampaign(
  campaignId: string,
  updates: {
    name?: string;
    description?: string;
    isActive?: boolean;
  }
): Promise<OutreachCampaign> {
  const params = new URLSearchParams();
  if (updates.name) params.set('name', updates.name);
  if (updates.description) params.set('description', updates.description);
  if (updates.isActive !== undefined)
    params.set('is_active', updates.isActive.toString());
  return fetchAPI<OutreachCampaign>(
    `/campaigns/${campaignId}?${params.toString()}`,
    { method: 'PATCH' }
  );
}

// ==================== Activity Monitoring ====================

export async function recordActivity(data: {
  profileLinkedinUrl: string;
  activityType: ActivityType;
  contentText?: string;
  activityUrl?: string;
  activityDate?: string;
  oldTitle?: string;
  oldCompany?: string;
  newTitle?: string;
  newCompany?: string;
}): Promise<LinkedInActivity> {
  return fetchAPI<LinkedInActivity>('/activities', {
    method: 'POST',
    body: JSON.stringify({
      profile_linkedin_url: data.profileLinkedinUrl,
      activity_type: data.activityType,
      content_text: data.contentText,
      activity_url: data.activityUrl,
      activity_date: data.activityDate,
      old_title: data.oldTitle,
      old_company: data.oldCompany,
      new_title: data.newTitle,
      new_company: data.newCompany,
    }),
  });
}

export async function listActivities(filters: {
  prospectLinkedinUrl: string;
  activityType?: ActivityType;
  sinceDays?: number;
  limit?: number;
}): Promise<LinkedInActivity[]> {
  const params = new URLSearchParams({
    prospect_linkedin_url: filters.prospectLinkedinUrl,
  });
  if (filters.activityType) params.set('activity_type', filters.activityType);
  if (filters.sinceDays) params.set('since_days', filters.sinceDays.toString());
  if (filters.limit) params.set('limit', filters.limit.toString());
  return fetchAPI<LinkedInActivity[]>(`/activities?${params.toString()}`);
}

export async function getJobChanges(
  sinceDays = 30,
  limit = 50
): Promise<LinkedInActivity[]> {
  const params = new URLSearchParams({
    since_days: sinceDays.toString(),
    limit: limit.toString(),
  });
  return fetchAPI<LinkedInActivity[]>(
    `/activities/job-changes?${params.toString()}`
  );
}

// ==================== Profile Matching ====================

export async function matchProfileToProspect(data: {
  linkedinUrl: string;
  prospectId?: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  company?: string;
}): Promise<ProfileMatchResponse> {
  return fetchAPI<ProfileMatchResponse>('/profiles/match', {
    method: 'POST',
    body: JSON.stringify({
      linkedin_url: data.linkedinUrl,
      prospect_id: data.prospectId,
      email: data.email,
      first_name: data.firstName,
      last_name: data.lastName,
      company: data.company,
    }),
  });
}

// ==================== Search ====================

export async function searchProfiles(filters: {
  query?: string;
  firstName?: string;
  lastName?: string;
  company?: string;
  title?: string;
  location?: string;
  limit?: number;
}): Promise<LinkedInProfileSummary[]> {
  const params = new URLSearchParams();
  if (filters.query) params.set('query', filters.query);
  if (filters.firstName) params.set('first_name', filters.firstName);
  if (filters.lastName) params.set('last_name', filters.lastName);
  if (filters.company) params.set('company', filters.company);
  if (filters.title) params.set('title', filters.title);
  if (filters.location) params.set('location', filters.location);
  if (filters.limit) params.set('limit', filters.limit.toString());
  return fetchAPI<LinkedInProfileSummary[]>(
    `/search/profiles?${params.toString()}`
  );
}

// ==================== Health Check ====================

export async function checkHealth(): Promise<{
  status: string;
  service: string;
  rate_limit: Record<string, any>;
  cache_enabled: boolean;
  enrichment_provider: string;
}> {
  return fetchAPI('/health');
}
