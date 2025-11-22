/**
 * Authentication types
 */

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  roles: string[];
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse extends TokenPair {
  user: User;
}

export interface LoginCredentials {
  email_or_username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[] | null;
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
}

export interface APIKeyCreated extends APIKey {
  key: string;
}

export interface CreateAPIKeyData {
  name: string;
  scopes?: string[];
  expires_in_days?: number;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export type UserRole = 'admin' | 'manager' | 'rep' | 'viewer';

export interface Permission {
  resource: string;
  action: string;
}
