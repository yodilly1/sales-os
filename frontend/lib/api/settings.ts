// Settings API client for Sales OS

import type {
  User,
  Organization,
  Integration,
  ApiKey,
  ApiKeyCreate,
  ApiKeyCreateResponse,
  NotificationPreferences,
  SettingsResponse,
  UpdateUserRequest,
  UpdateOrganizationRequest,
} from '../types/settings';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<SettingsResponse<T>> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API Error: ${response.status}`);
  }

  return response.json();
}

// User Profile API
export async function getUser(): Promise<User> {
  const response = await fetchApi<User>('/settings/user');
  return response.data;
}

export async function updateUser(data: UpdateUserRequest): Promise<User> {
  const response = await fetchApi<User>('/settings/user', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  return response.data;
}

export async function uploadAvatar(file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append('avatar', file);

  const response = await fetch(`${API_BASE}/settings/user/avatar`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to upload avatar');
  }

  return response.json();
}

// Organization API
export async function getOrganization(): Promise<Organization> {
  const response = await fetchApi<Organization>('/settings/organization');
  return response.data;
}

export async function updateOrganization(
  data: UpdateOrganizationRequest
): Promise<Organization> {
  const response = await fetchApi<Organization>('/settings/organization', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  return response.data;
}

export async function uploadOrganizationLogo(file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append('logo', file);

  const response = await fetch(`${API_BASE}/settings/organization/logo`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to upload logo');
  }

  return response.json();
}

// Integrations API
export async function getIntegrations(): Promise<Integration[]> {
  const response = await fetchApi<Integration[]>('/settings/integrations');
  return response.data;
}

export async function connectIntegration(
  type: Integration['type']
): Promise<{ authUrl: string }> {
  const response = await fetchApi<{ authUrl: string }>(
    `/settings/integrations/${type}/connect`,
    { method: 'POST' }
  );
  return response.data;
}

export async function disconnectIntegration(
  type: Integration['type']
): Promise<void> {
  await fetchApi(`/settings/integrations/${type}/disconnect`, {
    method: 'POST',
  });
}

export async function syncIntegration(
  type: Integration['type']
): Promise<{ syncId: string }> {
  const response = await fetchApi<{ syncId: string }>(
    `/settings/integrations/${type}/sync`,
    { method: 'POST' }
  );
  return response.data;
}

// API Keys API
export async function getApiKeys(): Promise<ApiKey[]> {
  const response = await fetchApi<ApiKey[]>('/settings/api-keys');
  return response.data;
}

export async function createApiKey(
  data: ApiKeyCreate
): Promise<ApiKeyCreateResponse> {
  const response = await fetchApi<ApiKeyCreateResponse>('/settings/api-keys', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return response.data;
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await fetchApi(`/settings/api-keys/${keyId}`, {
    method: 'DELETE',
  });
}

export async function updateApiKey(
  keyId: string,
  data: { name?: string; isActive?: boolean }
): Promise<ApiKey> {
  const response = await fetchApi<ApiKey>(`/settings/api-keys/${keyId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  return response.data;
}

// Notifications API
export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const response = await fetchApi<NotificationPreferences>(
    '/settings/notifications'
  );
  return response.data;
}

export async function updateNotificationPreferences(
  data: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  const response = await fetchApi<NotificationPreferences>(
    '/settings/notifications',
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    }
  );
  return response.data;
}

// Available scopes for API keys
export const API_KEY_SCOPES = [
  { id: 'transcripts:read', label: 'Read Transcripts', description: 'View transcripts and SPICED analysis' },
  { id: 'transcripts:write', label: 'Write Transcripts', description: 'Upload and modify transcripts' },
  { id: 'content:read', label: 'Read Content', description: 'View generated content' },
  { id: 'content:write', label: 'Write Content', description: 'Generate and modify content' },
  { id: 'prospects:read', label: 'Read Prospects', description: 'View prospect data' },
  { id: 'prospects:write', label: 'Write Prospects', description: 'Enrich and modify prospects' },
  { id: 'coaching:read', label: 'Read Coaching', description: 'View coaching analytics' },
  { id: 'integrations:read', label: 'Read Integrations', description: 'View integration status' },
  { id: 'integrations:write', label: 'Write Integrations', description: 'Manage integrations' },
] as const;
