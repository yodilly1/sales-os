/**
 * Deal Room API Client
 *
 * Client library for interacting with the deal room backend API.
 */

// Types
export interface DealRoomBranding {
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  custom_css?: string;
  favicon_url?: string;
}

export interface DealRoomSettings {
  show_action_plan: boolean;
  show_timeline: boolean;
  enable_comments: boolean;
  notify_on_view: boolean;
  require_nda: boolean;
}

export interface AccessControl {
  access_level: 'public' | 'password' | 'email_gate' | 'invite_only';
  password?: string;
  expires_at?: string;
  max_views?: number;
  allowed_emails?: string[];
}

export interface DealRoom {
  id: string;
  slug: string;
  title: string;
  description?: string;
  deal_id?: string;
  deal_name?: string;
  deal_value?: number;
  prospect_company?: string;
  prospect_name?: string;
  prospect_email?: string;
  status: 'draft' | 'active' | 'archived' | 'expired';
  access_level: 'public' | 'password' | 'email_gate' | 'invite_only';
  expires_at?: string;
  branding: DealRoomBranding;
  settings: DealRoomSettings;
  owner_id: string;
  team_id?: string;
  created_at: string;
  updated_at: string;
  published_at?: string;
  last_viewed_at?: string;
  share_url?: string;
  total_views: number;
  unique_viewers: number;
}

export interface DealRoomCreateRequest {
  title: string;
  description?: string;
  deal_id?: string;
  deal_name?: string;
  deal_value?: number;
  prospect_company?: string;
  prospect_name?: string;
  prospect_email?: string;
  branding?: Partial<DealRoomBranding>;
  settings?: Partial<DealRoomSettings>;
  access_control?: Partial<AccessControl>;
}

export interface DealRoomUpdateRequest extends Partial<DealRoomCreateRequest> {
  status?: 'draft' | 'active' | 'archived';
}

export interface Section {
  id: string;
  deal_room_id: string;
  parent_id?: string;
  name: string;
  description?: string;
  icon?: string;
  order_index: number;
  is_collapsed: boolean;
  created_at: string;
  updated_at: string;
}

export interface SectionCreateRequest {
  name: string;
  description?: string;
  icon?: string;
  parent_id?: string;
  order_index?: number;
}

export interface Content {
  id: string;
  deal_room_id: string;
  section_id?: string;
  title: string;
  description?: string;
  content_type: 'proposal' | 'deck' | 'case_study' | 'pricing' | 'contract' | 'video' | 'document' | 'link';
  file_url?: string;
  file_name?: string;
  file_size?: number;
  file_mime_type?: string;
  external_link?: string;
  thumbnail_url?: string;
  order_index: number;
  is_featured: boolean;
  is_pinned: boolean;
  is_hidden: boolean;
  version: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  view_count: number;
  download_count: number;
}

export interface ContentCreateRequest {
  title: string;
  description?: string;
  content_type: Content['content_type'];
  section_id?: string;
  file_url?: string;
  file_name?: string;
  file_size?: number;
  file_mime_type?: string;
  external_link?: string;
  thumbnail_url?: string;
  order_index?: number;
  is_featured?: boolean;
  is_pinned?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ActionPlanItem {
  id: string;
  deal_room_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  owner: 'seller' | 'buyer' | 'both';
  assignee_name?: string;
  assignee_email?: string;
  due_date?: string;
  completed_at?: string;
  order_index: number;
  is_milestone: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActionPlanItemCreateRequest {
  title: string;
  description?: string;
  owner?: 'seller' | 'buyer' | 'both';
  assignee_name?: string;
  assignee_email?: string;
  due_date?: string;
  order_index?: number;
  is_milestone?: boolean;
}

export interface Invitation {
  id: string;
  deal_room_id: string;
  email: string;
  name?: string;
  message?: string;
  token: string;
  sent_at?: string;
  opened_at?: string;
  accepted_at?: string;
  expires_at?: string;
  created_at: string;
}

export interface InvitationCreateRequest {
  email: string;
  name?: string;
  message?: string;
  expires_at?: string;
}

export interface AnalyticsSummary {
  deal_room_id: string;
  total_views: number;
  unique_viewers: number;
  total_time_spent_seconds: number;
  avg_time_per_visit_seconds: number;
  most_viewed_content: ContentViewStats[];
  recent_views: ViewEvent[];
  views_by_day: Record<string, number>;
  views_by_device: Record<string, number>;
}

export interface ContentViewStats {
  content_id: string;
  content_title: string;
  view_count: number;
  unique_viewers: number;
  total_time_spent: number;
  avg_scroll_depth: number;
  download_count: number;
}

export interface ViewEvent {
  id: string;
  deal_room_id: string;
  viewer_email?: string;
  viewer_name?: string;
  device_type?: string;
  browser?: string;
  country?: string;
  city?: string;
  time_spent_seconds: number;
  pages_viewed: number;
  viewed_at: string;
  last_activity_at: string;
}

export interface EngagementScore {
  overall_score: number;
  breakdown: {
    view_score: number;
    viewer_score: number;
    time_score: number;
    scroll_score: number;
    download_score: number;
  };
  interpretation: string;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// API Base URL - will be configured via environment
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

// Helper function for API requests
async function fetchApi<T>(
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
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// Deal Room API
// =============================================================================

export const dealRoomApi = {
  // Deal Rooms
  async list(params?: {
    status?: DealRoom['status'];
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<ListResponse<DealRoom>> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return fetchApi(`/dealrooms${query ? `?${query}` : ''}`);
  },

  async get(id: string): Promise<DealRoom> {
    return fetchApi(`/dealrooms/${id}`);
  },

  async create(data: DealRoomCreateRequest): Promise<DealRoom> {
    return fetchApi('/dealrooms', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: DealRoomUpdateRequest): Promise<DealRoom> {
    return fetchApi(`/dealrooms/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async delete(id: string): Promise<void> {
    return fetchApi(`/dealrooms/${id}`, {
      method: 'DELETE',
    });
  },

  async publish(id: string): Promise<DealRoom> {
    return fetchApi(`/dealrooms/${id}/publish`, {
      method: 'POST',
    });
  },

  async archive(id: string): Promise<DealRoom> {
    return fetchApi(`/dealrooms/${id}/archive`, {
      method: 'POST',
    });
  },

  async duplicate(id: string, newTitle: string): Promise<DealRoom> {
    return fetchApi(`/dealrooms/${id}/duplicate?new_title=${encodeURIComponent(newTitle)}`, {
      method: 'POST',
    });
  },

  // Sections
  async listSections(dealRoomId: string): Promise<Section[]> {
    return fetchApi(`/dealrooms/${dealRoomId}/sections`);
  },

  async createSection(dealRoomId: string, data: SectionCreateRequest): Promise<Section> {
    return fetchApi(`/dealrooms/${dealRoomId}/sections`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateSection(
    dealRoomId: string,
    sectionId: string,
    data: Partial<SectionCreateRequest>
  ): Promise<Section> {
    return fetchApi(`/dealrooms/${dealRoomId}/sections/${sectionId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deleteSection(dealRoomId: string, sectionId: string): Promise<void> {
    return fetchApi(`/dealrooms/${dealRoomId}/sections/${sectionId}`, {
      method: 'DELETE',
    });
  },

  async reorderSections(dealRoomId: string, sectionIds: string[]): Promise<void> {
    return fetchApi(`/dealrooms/${dealRoomId}/sections/reorder`, {
      method: 'POST',
      body: JSON.stringify(sectionIds),
    });
  },

  // Contents
  async listContents(
    dealRoomId: string,
    params?: { section_id?: string; content_type?: Content['content_type'] }
  ): Promise<Content[]> {
    const searchParams = new URLSearchParams();
    if (params?.section_id) searchParams.set('section_id', params.section_id);
    if (params?.content_type) searchParams.set('content_type', params.content_type);

    const query = searchParams.toString();
    return fetchApi(`/dealrooms/${dealRoomId}/contents${query ? `?${query}` : ''}`);
  },

  async getContent(dealRoomId: string, contentId: string): Promise<Content> {
    return fetchApi(`/dealrooms/${dealRoomId}/contents/${contentId}`);
  },

  async addContent(dealRoomId: string, data: ContentCreateRequest): Promise<Content> {
    return fetchApi(`/dealrooms/${dealRoomId}/contents`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateContent(
    dealRoomId: string,
    contentId: string,
    data: Partial<ContentCreateRequest>
  ): Promise<Content> {
    return fetchApi(`/dealrooms/${dealRoomId}/contents/${contentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deleteContent(dealRoomId: string, contentId: string): Promise<void> {
    return fetchApi(`/dealrooms/${dealRoomId}/contents/${contentId}`, {
      method: 'DELETE',
    });
  },

  async reorderContents(dealRoomId: string, contentIds: string[]): Promise<void> {
    return fetchApi(`/dealrooms/${dealRoomId}/contents/reorder`, {
      method: 'POST',
      body: JSON.stringify(contentIds),
    });
  },

  // Action Plan
  async listActionPlanItems(dealRoomId: string): Promise<ActionPlanItem[]> {
    return fetchApi(`/dealrooms/${dealRoomId}/action-plan`);
  },

  async addActionPlanItem(
    dealRoomId: string,
    data: ActionPlanItemCreateRequest
  ): Promise<ActionPlanItem> {
    return fetchApi(`/dealrooms/${dealRoomId}/action-plan`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateActionPlanItem(
    dealRoomId: string,
    itemId: string,
    data: Partial<ActionPlanItemCreateRequest & { status: ActionPlanItem['status'] }>
  ): Promise<ActionPlanItem> {
    return fetchApi(`/dealrooms/${dealRoomId}/action-plan/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deleteActionPlanItem(dealRoomId: string, itemId: string): Promise<void> {
    return fetchApi(`/dealrooms/${dealRoomId}/action-plan/${itemId}`, {
      method: 'DELETE',
    });
  },

  // Invitations
  async listInvitations(
    dealRoomId: string,
    includeAccepted = false
  ): Promise<Invitation[]> {
    return fetchApi(
      `/dealrooms/${dealRoomId}/invitations?include_accepted=${includeAccepted}`
    );
  },

  async createInvitation(
    dealRoomId: string,
    data: InvitationCreateRequest
  ): Promise<Invitation> {
    return fetchApi(`/dealrooms/${dealRoomId}/invitations`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async resendInvitation(dealRoomId: string, invitationId: string): Promise<Invitation> {
    return fetchApi(`/dealrooms/${dealRoomId}/invitations/${invitationId}/resend`, {
      method: 'POST',
    });
  },

  async deleteInvitation(dealRoomId: string, invitationId: string): Promise<void> {
    return fetchApi(`/dealrooms/${dealRoomId}/invitations/${invitationId}`, {
      method: 'DELETE',
    });
  },

  // Analytics
  async getAnalytics(dealRoomId: string): Promise<AnalyticsSummary> {
    return fetchApi(`/dealrooms/${dealRoomId}/analytics`);
  },

  async getEngagementScore(dealRoomId: string): Promise<EngagementScore> {
    return fetchApi(`/dealrooms/${dealRoomId}/analytics/engagement`);
  },

  async getWeeklyReport(dealRoomId: string): Promise<Record<string, unknown>> {
    return fetchApi(`/dealrooms/${dealRoomId}/analytics/weekly-report`);
  },

  async getViewerJourney(
    dealRoomId: string,
    viewerEmail: string
  ): Promise<Record<string, unknown>[]> {
    return fetchApi(
      `/dealrooms/${dealRoomId}/analytics/viewer/${encodeURIComponent(viewerEmail)}`
    );
  },

  async exportAnalytics(dealRoomId: string): Promise<Blob> {
    const response = await fetch(
      `${API_BASE_URL}/dealrooms/${dealRoomId}/analytics/export`,
      { credentials: 'include' }
    );
    return response.blob();
  },
};

// =============================================================================
// Public Room API
// =============================================================================

export interface PublicDealRoom {
  slug: string;
  title: string;
  description?: string;
  prospect_company?: string;
  branding: DealRoomBranding;
  show_action_plan: boolean;
  show_timeline: boolean;
  enable_comments: boolean;
  sections: PublicSection[];
  action_plan: PublicActionPlanItem[];
}

export interface PublicSection {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  order_index: number;
  contents: PublicContent[];
  children: PublicSection[];
}

export interface PublicContent {
  id: string;
  title: string;
  description?: string;
  content_type: Content['content_type'];
  file_url?: string;
  external_link?: string;
  thumbnail_url?: string;
  order_index: number;
  is_featured: boolean;
}

export interface PublicActionPlanItem {
  id: string;
  title: string;
  description?: string;
  status: ActionPlanItem['status'];
  owner: ActionPlanItem['owner'];
  due_date?: string;
  is_milestone: boolean;
  order_index: number;
}

export interface AccessVerificationResponse {
  granted: boolean;
  access_token?: string;
  expires_at?: string;
  message?: string;
}

export const publicRoomApi = {
  async get(slug: string): Promise<PublicDealRoom | { requires_auth: true; auth_requirements: Record<string, boolean> }> {
    return fetchApi(`/room/${slug}`);
  },

  async verifyAccess(
    slug: string,
    data: { password?: string; email?: string; invitation_token?: string }
  ): Promise<AccessVerificationResponse> {
    return fetchApi(`/room/${slug}/verify`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async trackView(
    slug: string,
    data: { viewer_email?: string; viewer_name?: string; session_id?: string }
  ): Promise<{ session_id: string; view_event_id: string }> {
    return fetchApi(`/room/${slug}/track-view`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async trackContentView(
    slug: string,
    data: {
      content_id: string;
      view_event_id: string;
      time_spent_seconds?: number;
      scroll_depth_percent?: number;
      downloaded?: boolean;
    }
  ): Promise<{ success: boolean; content_view_id: string }> {
    const params = new URLSearchParams({
      content_id: data.content_id,
      view_event_id: data.view_event_id,
      time_spent_seconds: (data.time_spent_seconds || 0).toString(),
      scroll_depth_percent: (data.scroll_depth_percent || 0).toString(),
      downloaded: (data.downloaded || false).toString(),
    });

    return fetchApi(`/room/${slug}/track-content-view?${params}`, {
      method: 'POST',
    });
  },

  async updateSessionTime(
    slug: string,
    sessionId: string,
    timeSpentSeconds: number
  ): Promise<{ success: boolean }> {
    const params = new URLSearchParams({
      session_id: sessionId,
      time_spent_seconds: timeSpentSeconds.toString(),
    });

    return fetchApi(`/room/${slug}/update-session-time?${params}`, {
      method: 'POST',
    });
  },
};

export default dealRoomApi;
