/**
 * Calendar API Client
 *
 * Frontend API client for calendar integration endpoints.
 */

import {
  CalendarProvider,
  CalendarIntegration,
  CalendarEvent,
  CalendarEventListResponse,
  CalendarWidgetData,
  SyncResult,
  OAuthURLResponse,
  CalendarInfo,
} from '../../components/calendar/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class CalendarAPIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'CalendarAPIError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new CalendarAPIError(
      error.detail || error.message || 'An error occurred',
      response.status,
      error
    );
  }
  return response.json();
}

function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add auth token if available
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

// OAuth & Connection

export async function connectCalendar(
  provider: CalendarProvider,
  redirectUri?: string
): Promise<OAuthURLResponse> {
  const params = new URLSearchParams();
  if (redirectUri) {
    params.append('redirect_uri', redirectUri);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/calendar/oauth/connect/${provider}?${params}`,
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  return handleResponse<OAuthURLResponse>(response);
}

export async function disconnectCalendar(integrationId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/calendar/oauth/disconnect/${integrationId}`,
    {
      method: 'DELETE',
      headers: getHeaders(),
    }
  );

  await handleResponse(response);
}

// Integrations

export async function listIntegrations(): Promise<CalendarIntegration[]> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/integrations`, {
    method: 'GET',
    headers: getHeaders(),
  });

  const data = await handleResponse<CalendarIntegration[]>(response);

  // Convert date strings to Date objects
  return data.map((integration) => ({
    ...integration,
    lastSyncAt: integration.lastSyncAt
      ? new Date(integration.lastSyncAt)
      : undefined,
    createdAt: new Date(integration.createdAt),
  }));
}

export async function getIntegration(
  integrationId: string
): Promise<CalendarIntegration> {
  const response = await fetch(
    `${API_BASE_URL}/api/calendar/integrations/${integrationId}`,
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  const data = await handleResponse<CalendarIntegration>(response);

  return {
    ...data,
    lastSyncAt: data.lastSyncAt ? new Date(data.lastSyncAt) : undefined,
    createdAt: new Date(data.createdAt),
  };
}

export async function listAvailableCalendars(
  integrationId: string
): Promise<CalendarInfo[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/calendar/calendars?integration_id=${integrationId}`,
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  const data = await handleResponse<{ success: boolean; data: { calendars: CalendarInfo[] } }>(response);
  return data.data.calendars;
}

// Events

export interface ListEventsParams {
  provider?: CalendarProvider;
  startDate?: Date;
  endDate?: Date;
  hasTranscript?: boolean;
  search?: string;
  page?: number;
  pageSize?: number;
}

export async function listEvents(
  params: ListEventsParams = {}
): Promise<CalendarEventListResponse> {
  const searchParams = new URLSearchParams();

  if (params.provider) searchParams.append('provider', params.provider);
  if (params.startDate)
    searchParams.append('start_date', params.startDate.toISOString());
  if (params.endDate)
    searchParams.append('end_date', params.endDate.toISOString());
  if (params.hasTranscript !== undefined)
    searchParams.append('has_transcript', String(params.hasTranscript));
  if (params.search) searchParams.append('search', params.search);
  if (params.page) searchParams.append('page', String(params.page));
  if (params.pageSize) searchParams.append('page_size', String(params.pageSize));

  const response = await fetch(
    `${API_BASE_URL}/api/calendar/events?${searchParams}`,
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  const data = await handleResponse<CalendarEventListResponse>(response);

  // Convert date strings to Date objects
  return {
    ...data,
    items: data.items.map((event) => ({
      ...event,
      startTime: new Date(event.startTime),
      endTime: new Date(event.endTime),
    })),
  };
}

export async function getEvent(eventId: string): Promise<CalendarEvent> {
  const response = await fetch(
    `${API_BASE_URL}/api/calendar/events/${eventId}`,
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  const data = await handleResponse<CalendarEvent>(response);

  return {
    ...data,
    startTime: new Date(data.startTime),
    endTime: new Date(data.endTime),
  };
}

// Sync

export interface SyncParams {
  integrationId: string;
  fullSync?: boolean;
  startDate?: Date;
  endDate?: Date;
}

export async function syncCalendar(params: SyncParams): Promise<SyncResult> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/sync`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({
      integration_id: params.integrationId,
      full_sync: params.fullSync ?? false,
      start_date: params.startDate?.toISOString(),
      end_date: params.endDate?.toISOString(),
    }),
  });

  const data = await handleResponse<SyncResult>(response);

  return {
    ...data,
    syncedAt: new Date(data.syncedAt),
  };
}

// Meeting-Transcript Linking

export async function linkMeetingToTranscript(
  eventId: string,
  transcriptId: string,
  notes?: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/calendar/events/${eventId}/link-transcript?transcript_id=${transcriptId}`,
    {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ notes }),
    }
  );

  await handleResponse(response);
}

export async function unlinkMeetingFromTranscript(
  eventId: string,
  transcriptId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/calendar/events/${eventId}/unlink-transcript/${transcriptId}`,
    {
      method: 'DELETE',
      headers: getHeaders(),
    }
  );

  await handleResponse(response);
}

// Dashboard Widget

export async function getCalendarWidgetData(
  days?: number,
  limit?: number
): Promise<CalendarWidgetData> {
  const params = new URLSearchParams();
  if (days) params.append('days', String(days));
  if (limit) params.append('limit', String(limit));

  const response = await fetch(
    `${API_BASE_URL}/api/calendar/widget/upcoming?${params}`,
    {
      method: 'GET',
      headers: getHeaders(),
    }
  );

  const data = await handleResponse<CalendarWidgetData>(response);

  // Convert date strings to Date objects
  return {
    ...data,
    upcomingMeetings: data.upcomingMeetings.map((meeting) => ({
      ...meeting,
      startTime: new Date(meeting.startTime),
      endTime: new Date(meeting.endTime),
    })),
    nextMeeting: data.nextMeeting
      ? {
          ...data.nextMeeting,
          startTime: new Date(data.nextMeeting.startTime),
          endTime: new Date(data.nextMeeting.endTime),
        }
      : undefined,
  };
}

// Export all functions as a namespace
const calendarAPI = {
  // OAuth
  connectCalendar,
  disconnectCalendar,
  // Integrations
  listIntegrations,
  getIntegration,
  listAvailableCalendars,
  // Events
  listEvents,
  getEvent,
  // Sync
  syncCalendar,
  // Linking
  linkMeetingToTranscript,
  unlinkMeetingFromTranscript,
  // Widget
  getCalendarWidgetData,
};

export default calendarAPI;
