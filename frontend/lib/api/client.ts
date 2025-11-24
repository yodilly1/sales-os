import { ApiResponse, ApiError } from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/**
 * API client configuration
 */
interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

/**
 * Build URL with query parameters
 */
function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = new URL(`${API_BASE_URL}${path}`);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  return url.toString();
}

/**
 * Get auth token from storage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

/**
 * Main fetch wrapper with error handling
 */
async function request<T>(
  path: string,
  config: RequestConfig = {}
): Promise<T> {
  const { params, ...fetchConfig } = config;
  const url = buildUrl(path, params);

  const token = getAuthToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...config.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...fetchConfig,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    const error: ApiError = data.error || {
      code: 'UNKNOWN_ERROR',
      message: data.message || 'An unexpected error occurred',
    };
    throw new ApiClientError(error.message, error.code, response.status, error.details);
  }

  return data as T;
}

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

/**
 * API client methods
 */
export const apiClient = {
  get: <T>(path: string, config?: RequestConfig) =>
    request<T>(path, { ...config, method: 'GET' }),

  post: <T>(path: string, body?: unknown, config?: RequestConfig) =>
    request<T>(path, {
      ...config,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown, config?: RequestConfig) =>
    request<T>(path, {
      ...config,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown, config?: RequestConfig) =>
    request<T>(path, {
      ...config,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, config?: RequestConfig) =>
    request<T>(path, { ...config, method: 'DELETE' }),
};

/**
 * Upload file to API
 */
export async function uploadFile(
  path: string,
  file: File,
  additionalData?: Record<string, string>
): Promise<ApiResponse<unknown>> {
  const url = buildUrl(path);
  const token = getAuthToken();

  const formData = new FormData();
  formData.append('file', file);

  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    const error: ApiError = data.error || {
      code: 'UPLOAD_ERROR',
      message: data.message || 'Upload failed',
    };
    throw new ApiClientError(error.message, error.code, response.status, error.details);
  }

  return data;
}

/**
 * Deprecated: Legacy APIError export for backwards compatibility
 */
export const APIError = ApiClientError;
