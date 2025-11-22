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
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
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
