/**
 * Gong API Client
 *
 * Client functions for interacting with the Gong integration API endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Types
// =============================================================================

export interface GongConnectRequest {
  access_key: string;
  access_key_secret: string;
  workspace_id?: string;
}

export interface GongConnectResponse {
  status: 'connected' | 'disconnected' | 'error' | 'pending';
  message: string;
  connected_at?: string;
}

export interface GongStatusResponse {
  status: 'connected' | 'disconnected' | 'error' | 'pending';
  workspace_id?: string | null;
  last_sync_at?: string | null;
  total_calls_synced: number;
  last_error?: string | null;
}

export interface GongCallResponse {
  id: string;
  gong_call_id: string;
  title?: string;
  started_at?: string;
  duration_seconds?: number;
  duration_formatted: string;
  platform?: string;
  scope?: string;
  participants: GongParticipant[];
  has_transcript: boolean;
  has_spiced_analysis: boolean;
  external_url?: string;
}

export interface GongParticipant {
  id?: string;
  email?: string;
  name?: string;
  title?: string;
  is_internal: boolean;
  talk_time_percentage?: number;
}

export interface GongCallListResponse {
  calls: GongCallResponse[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface GongCallListParams {
  page?: number;
  page_size?: number;
  from_date?: string;
  to_date?: string;
  search?: string;
}

export interface GongSyncRequest {
  sync_type: 'incremental' | 'full' | 'historical';
  from_datetime?: string;
  to_datetime?: string;
  include_transcripts?: boolean;
  include_insights?: boolean;
}

export interface GongSyncResponse {
  status: 'success' | 'partial' | 'error' | 'queued';
  calls_synced: number;
  calls_skipped: number;
  calls_failed: number;
  errors: string[];
  sync_started_at: string;
  sync_completed_at?: string;
}

export interface GongTranscript {
  call_id: string;
  raw_text: string;
  formatted_text: string;
  segments: GongTranscriptSegment[];
  word_count: number;
}

export interface GongTranscriptSegment {
  speaker_id?: string;
  speaker_name?: string;
  start_time?: number;
  end_time?: number;
  text: string;
}

// =============================================================================
// API Error Handling
// =============================================================================

export class GongApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'GongApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Use default error message if response is not JSON
    }
    throw new GongApiError(errorMessage, response.status);
  }
  return response.json();
}

// =============================================================================
// Authentication & Connection
// =============================================================================

/**
 * Connect Gong integration with API credentials
 */
export async function connectGong(
  credentials: GongConnectRequest
): Promise<GongConnectResponse> {
  const response = await fetch(`${API_BASE}/api/gong/connect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(credentials),
  });
  return handleResponse<GongConnectResponse>(response);
}

/**
 * Disconnect Gong integration
 */
export async function disconnectGong(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/gong/disconnect`, {
    method: 'POST',
    credentials: 'include',
  });
  return handleResponse(response);
}

/**
 * Get current Gong integration status
 */
export async function getGongStatus(): Promise<GongStatusResponse> {
  const response = await fetch(`${API_BASE}/api/gong/status`, {
    credentials: 'include',
  });
  return handleResponse<GongStatusResponse>(response);
}

/**
 * Health check for Gong integration
 */
export async function checkGongHealth(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/gong/health`, {
    credentials: 'include',
  });
  return handleResponse(response);
}

// =============================================================================
// Call Retrieval
// =============================================================================

/**
 * Get list of synced Gong calls
 */
export async function getGongCalls(
  params: GongCallListParams = {}
): Promise<GongCallListResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', params.page.toString());
  if (params.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params.from_date) searchParams.set('from_date', params.from_date);
  if (params.to_date) searchParams.set('to_date', params.to_date);
  if (params.search) searchParams.set('search', params.search);

  const queryString = searchParams.toString();
  const url = `${API_BASE}/api/gong/calls${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    credentials: 'include',
  });
  return handleResponse<GongCallListResponse>(response);
}

/**
 * Get details for a specific call
 */
export async function getGongCall(callId: string): Promise<GongCallResponse> {
  const response = await fetch(`${API_BASE}/api/gong/calls/${callId}`, {
    credentials: 'include',
  });
  return handleResponse<GongCallResponse>(response);
}

/**
 * Get transcript for a specific call
 */
export async function getGongCallTranscript(callId: string): Promise<GongTranscript> {
  const response = await fetch(`${API_BASE}/api/gong/calls/${callId}/transcript`, {
    credentials: 'include',
  });
  return handleResponse<GongTranscript>(response);
}

/**
 * Get participants for a specific call
 */
export async function getGongCallParticipants(
  callId: string
): Promise<GongParticipant[]> {
  const response = await fetch(`${API_BASE}/api/gong/calls/${callId}/participants`, {
    credentials: 'include',
  });
  return handleResponse<GongParticipant[]>(response);
}

/**
 * Trigger processing/analysis for a call
 */
export async function processGongCall(
  callId: string
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/gong/calls/${callId}/process`, {
    method: 'POST',
    credentials: 'include',
  });
  return handleResponse(response);
}

// =============================================================================
// Sync Operations
// =============================================================================

/**
 * Trigger a sync operation
 */
export async function triggerGongSync(
  request: GongSyncRequest
): Promise<GongSyncResponse> {
  const response = await fetch(`${API_BASE}/api/gong/sync`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });
  return handleResponse<GongSyncResponse>(response);
}

/**
 * Get current sync status
 */
export async function getGongSyncStatus(): Promise<{
  is_syncing: boolean;
  last_sync?: unknown;
  next_scheduled_sync?: string;
}> {
  const response = await fetch(`${API_BASE}/api/gong/sync/status`, {
    credentials: 'include',
  });
  return handleResponse(response);
}

/**
 * Get sync history
 */
export async function getGongSyncHistory(
  page: number = 1,
  pageSize: number = 20
): Promise<{
  syncs: unknown[];
  total: number;
  page: number;
  page_size: number;
}> {
  const response = await fetch(
    `${API_BASE}/api/gong/sync/history?page=${page}&page_size=${pageSize}`,
    {
      credentials: 'include',
    }
  );
  return handleResponse(response);
}

// =============================================================================
// Direct API Proxy (for debugging/preview)
// =============================================================================

/**
 * Directly fetch calls from Gong API (proxy)
 */
export async function proxyGongCalls(params: {
  from_datetime?: string;
  to_datetime?: string;
  cursor?: string;
}): Promise<{
  calls: unknown[];
  cursor?: string;
  total_records?: number;
}> {
  const searchParams = new URLSearchParams();
  if (params.from_datetime) searchParams.set('from_datetime', params.from_datetime);
  if (params.to_datetime) searchParams.set('to_datetime', params.to_datetime);
  if (params.cursor) searchParams.set('cursor', params.cursor);

  const queryString = searchParams.toString();
  const url = `${API_BASE}/api/gong/proxy/calls${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    credentials: 'include',
  });
  return handleResponse(response);
}
