/**
 * Calendar Component Types
 *
 * TypeScript interfaces for calendar-related data structures.
 */

export type CalendarProvider = 'google' | 'outlook';

export type SyncStatus = 'active' | 'paused' | 'error' | 'disconnected';

export type EventStatus = 'confirmed' | 'tentative' | 'cancelled';

export type AttendeeStatus = 'accepted' | 'declined' | 'tentative' | 'needs_action';

export interface Attendee {
  email: string;
  name?: string;
  status: AttendeeStatus;
  isOrganizer: boolean;
  isOptional: boolean;
}

export interface MeetingLink {
  url: string;
  provider?: string;
  meetingId?: string;
  passcode?: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  startTime: Date;
  endTime: Date;
  timezone: string;
  location?: string;
  isAllDay: boolean;
  attendees: Attendee[];
  meetingLink?: MeetingLink;
  status: EventStatus;
  htmlLink?: string;
  provider: CalendarProvider;
  transcriptId?: string;
  hasTranscript: boolean;
}

export interface CalendarIntegration {
  id: string;
  provider: CalendarProvider;
  calendarId?: string;
  status: SyncStatus;
  syncEnabled: boolean;
  lastSyncAt?: Date;
  createdAt: Date;
}

export interface UpcomingMeeting {
  id: string;
  title: string;
  startTime: Date;
  endTime: Date;
  attendeesCount: number;
  hasTranscript: boolean;
  meetingLink?: string;
  provider: CalendarProvider;
}

export interface CalendarWidgetData {
  upcomingMeetings: UpcomingMeeting[];
  meetingsToday: number;
  meetingsThisWeek: number;
  totalIntegrations: number;
  nextMeeting?: UpcomingMeeting;
}

export interface SyncResult {
  integrationId: string;
  eventsSynced: number;
  eventsCreated: number;
  eventsUpdated: number;
  eventsDeleted: number;
  errors: string[];
  syncedAt: Date;
}

export interface CalendarInfo {
  id: string;
  name: string;
  isPrimary: boolean;
  isSelected: boolean;
  color?: string;
  accessRole?: string;
}

// API Response types
export interface CalendarEventListResponse {
  items: CalendarEvent[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface OAuthURLResponse {
  authorizationUrl: string;
  state: string;
  provider: CalendarProvider;
}
