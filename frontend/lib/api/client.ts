<<<<<<< HEAD
<<<<<<< HEAD
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
=======
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'APIError';
=======
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ApiError {
  message: string
  status: number
  details?: unknown
}

export class ApiClientError extends Error {
  status: number
  details?: unknown

  constructor(message: string, status: number, details?: unknown) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.details = details
>>>>>>> origin/claude/analytics-dashboard-01M24DLkEb1rR8wBY9c26gKw
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
<<<<<<< HEAD
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }

    throw new APIError(
      `HTTP error ${response.status}`,
      response.status,
      errorData
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const apiClient = {
  async get<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options;
    let url = `${API_BASE_URL}${endpoint}`;

    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
      ...fetchOptions,
    });

    return handleResponse<T>(response);
  },

  async post<T>(endpoint: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });

    return handleResponse<T>(response);
  },

  async put<T>(endpoint: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });

    return handleResponse<T>(response);
  },

  async delete<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    return handleResponse<T>(response);
  },
};

export { APIError };
>>>>>>> origin/claude/frontend-content-ui-01SUCiGQU6dN2Z9rPASZfehV
=======
    let errorMessage = 'An error occurred'
    let details: unknown

    try {
      const errorData = await response.json()
      errorMessage = errorData.message || errorData.detail || errorMessage
      details = errorData
    } catch {
      errorMessage = response.statusText || errorMessage
    }

    throw new ApiClientError(errorMessage, response.status, details)
  }

  return response.json()
}

export async function apiGet<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`)

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value)
      }
    })
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })

  return handleResponse<T>(response)
}

export async function apiPost<T, D = unknown>(endpoint: string, data?: D): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: data ? JSON.stringify(data) : undefined,
  })

  return handleResponse<T>(response)
}

export function buildQueryParams(params: Record<string, unknown>): Record<string, string> {
  const result: Record<string, string> = {}

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (value instanceof Date) {
        result[key] = value.toISOString()
      } else if (Array.isArray(value)) {
        result[key] = value.join(',')
      } else {
        result[key] = String(value)
      }
    }
  })

  return result
}
>>>>>>> origin/claude/analytics-dashboard-01M24DLkEb1rR8wBY9c26gKw
