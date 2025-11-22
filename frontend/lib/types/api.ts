/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  error?: ApiError;
  timestamp: string;
}

/**
 * API error structure
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

/**
 * Sort options
 */
export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

/**
 * Filter options
 */
export interface FilterOptions {
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'in';
  value: unknown;
}

/**
 * Query parameters for list endpoints
 */
export interface ListQueryParams {
  page?: number;
  pageSize?: number;
  sort?: SortOptions;
  filters?: FilterOptions[];
  search?: string;
}
