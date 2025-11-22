/**
 * Notification API client for Sales OS.
 *
 * Provides functions for interacting with the notification endpoints,
 * including fetching, marking as read, and managing preferences.
 */

// =============================================================================
// Types
// =============================================================================

export type NotificationType =
  | "transcript_processed"
  | "content_generated"
  | "enrichment_complete"
  | "coaching_feedback_ready"
  | "integration_sync_status"
  | "system_alert"
  | "team_update";

export type NotificationChannel =
  | "in_app"
  | "email_instant"
  | "email_digest"
  | "websocket";

export type NotificationPriority = "low" | "normal" | "high" | "urgent";

export type NotificationStatus =
  | "pending"
  | "sent"
  | "delivered"
  | "read"
  | "archived"
  | "failed";

export interface Notification {
  id: string;
  user_id: string;
  organization_id: string;
  type: NotificationType;
  title: string;
  body: string;
  priority: NotificationPriority;
  entity_type?: string;
  entity_id?: string;
  metadata?: Record<string, unknown>;
  status: NotificationStatus;
  channel: NotificationChannel;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface UnreadCountResponse {
  count: number;
  by_type: Record<string, number>;
}

export interface NotificationPreference {
  id?: string;
  user_id: string;
  notification_type: NotificationType;
  channel: NotificationChannel;
  enabled: boolean;
  digest_frequency?: string;
  digest_time?: string;
  digest_timezone?: string;
  created_at: string;
  updated_at: string;
}

export interface ListNotificationsParams {
  page?: number;
  page_size?: number;
  type?: NotificationType;
  is_read?: boolean;
  priority?: NotificationPriority;
}

// =============================================================================
// API Client
// =============================================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Create request headers with authentication.
 */
function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Add auth token if available
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Handle API response errors.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `API error: ${response.status} ${response.statusText}`
    );
  }
  return response.json();
}

/**
 * Fetch a paginated list of notifications.
 */
export async function listNotifications(
  params: ListNotificationsParams = {}
): Promise<NotificationListResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set("page", params.page.toString());
  if (params.page_size)
    searchParams.set("page_size", params.page_size.toString());
  if (params.type) searchParams.set("type", params.type);
  if (params.is_read !== undefined)
    searchParams.set("is_read", params.is_read.toString());
  if (params.priority) searchParams.set("priority", params.priority);

  const url = `${API_BASE_URL}/notifications?${searchParams.toString()}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getHeaders(),
  });

  return handleResponse<NotificationListResponse>(response);
}

/**
 * Get a single notification by ID.
 */
export async function getNotification(
  notificationId: string
): Promise<Notification> {
  const response = await fetch(
    `${API_BASE_URL}/notifications/${notificationId}`,
    {
      method: "GET",
      headers: getHeaders(),
    }
  );

  return handleResponse<Notification>(response);
}

/**
 * Get the count of unread notifications.
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const response = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
    method: "GET",
    headers: getHeaders(),
  });

  return handleResponse<UnreadCountResponse>(response);
}

/**
 * Mark specific notifications as read.
 */
export async function markAsRead(
  notificationIds: string[]
): Promise<{ marked_read: number }> {
  const response = await fetch(`${API_BASE_URL}/notifications/mark-read`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ notification_ids: notificationIds }),
  });

  return handleResponse<{ marked_read: number }>(response);
}

/**
 * Mark all notifications as read.
 */
export async function markAllAsRead(options?: {
  before_date?: string;
  notification_type?: NotificationType;
}): Promise<{ marked_read: number }> {
  const response = await fetch(`${API_BASE_URL}/notifications/mark-all-read`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(options || {}),
  });

  return handleResponse<{ marked_read: number }>(response);
}

/**
 * Archive notifications.
 */
export async function archiveNotifications(
  notificationIds: string[]
): Promise<{ archived: number }> {
  const response = await fetch(`${API_BASE_URL}/notifications/archive`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ notification_ids: notificationIds }),
  });

  return handleResponse<{ archived: number }>(response);
}

/**
 * Delete a notification.
 */
export async function deleteNotification(
  notificationId: string
): Promise<{ deleted: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/notifications/${notificationId}`,
    {
      method: "DELETE",
      headers: getHeaders(),
    }
  );

  return handleResponse<{ deleted: boolean }>(response);
}

/**
 * Get all notification preferences.
 */
export async function getPreferences(): Promise<NotificationPreference[]> {
  const response = await fetch(`${API_BASE_URL}/notifications/preferences`, {
    method: "GET",
    headers: getHeaders(),
  });

  return handleResponse<NotificationPreference[]>(response);
}

/**
 * Update notification preferences in bulk.
 */
export async function updatePreferences(
  preferences: Omit<NotificationPreference, "id" | "user_id" | "created_at" | "updated_at">[]
): Promise<NotificationPreference[]> {
  const response = await fetch(`${API_BASE_URL}/notifications/preferences`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify({ preferences }),
  });

  return handleResponse<NotificationPreference[]>(response);
}

/**
 * Update a single preference.
 */
export async function updatePreference(
  notificationType: NotificationType,
  channel: NotificationChannel,
  settings: {
    enabled: boolean;
    digest_frequency?: string;
    digest_time?: string;
    digest_timezone?: string;
  }
): Promise<NotificationPreference> {
  const searchParams = new URLSearchParams({
    enabled: settings.enabled.toString(),
  });

  if (settings.digest_frequency)
    searchParams.set("digest_frequency", settings.digest_frequency);
  if (settings.digest_time)
    searchParams.set("digest_time", settings.digest_time);
  if (settings.digest_timezone)
    searchParams.set("digest_timezone", settings.digest_timezone);

  const response = await fetch(
    `${API_BASE_URL}/notifications/preferences/${notificationType}/${channel}?${searchParams.toString()}`,
    {
      method: "PUT",
      headers: getHeaders(),
    }
  );

  return handleResponse<NotificationPreference>(response);
}
