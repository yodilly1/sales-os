/**
 * Authentication utilities and API calls
 */

import { api } from './api';
import {
  setAccessToken,
  setRefreshToken,
  setStoredUser,
  clearAuthStorage,
  getStoredUser,
  hasAuthTokens,
} from './utils/storage';
import type {
  User,
  LoginCredentials,
  LoginResponse,
  RegisterData,
  ChangePasswordData,
  APIKey,
  APIKeyCreated,
  CreateAPIKeyData,
  TokenPair,
} from '../types/auth';
import { config, OAuthProvider } from './config';

/**
 * Register a new user
 */
export async function register(data: RegisterData): Promise<User> {
  const user = await api.post<User>('/api/auth/register', data, { skipAuth: true });
  return user;
}

/**
 * Login with credentials
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/api/auth/login', credentials, {
    skipAuth: true,
  });

  // Store tokens and user
  setAccessToken(response.access_token);
  setRefreshToken(response.refresh_token);
  setStoredUser(response.user);

  return response;
}

/**
 * Logout current user
 */
export async function logout(): Promise<void> {
  try {
    await api.post('/api/auth/logout');
  } catch {
    // Ignore errors, just clear local state
  } finally {
    clearAuthStorage();
  }
}

/**
 * Refresh tokens
 */
export async function refreshTokens(refreshToken: string): Promise<TokenPair> {
  const tokens = await api.post<TokenPair>(
    '/api/auth/refresh',
    { refresh_token: refreshToken },
    { skipAuth: true }
  );

  setAccessToken(tokens.access_token);
  setRefreshToken(tokens.refresh_token);

  return tokens;
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<User> {
  const user = await api.get<User>('/api/auth/me');
  setStoredUser(user);
  return user;
}

/**
 * Change password
 */
export async function changePassword(data: ChangePasswordData): Promise<void> {
  await api.post('/api/auth/change-password', data);
}

/**
 * Get cached user from storage
 */
export function getCachedUser(): User | null {
  return getStoredUser<User>();
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return hasAuthTokens();
}

// API Key management

/**
 * Create a new API key
 */
export async function createAPIKey(data: CreateAPIKeyData): Promise<APIKeyCreated> {
  return api.post<APIKeyCreated>('/api/auth/api-keys', data);
}

/**
 * List user's API keys
 */
export async function listAPIKeys(): Promise<APIKey[]> {
  return api.get<APIKey[]>('/api/auth/api-keys');
}

/**
 * Revoke an API key
 */
export async function revokeAPIKey(keyId: string): Promise<void> {
  await api.delete(`/api/auth/api-keys/${keyId}`);
}

// OAuth management

/**
 * Get OAuth authorization URL
 */
export async function getOAuthAuthorizationUrl(
  provider: OAuthProvider
): Promise<string> {
  const response = await api.get<{ authorization_url: string }>(
    `/api/auth/oauth/${provider}/authorize`
  );
  return response.authorization_url;
}

/**
 * Initiate OAuth flow (redirects to provider)
 */
export async function initiateOAuth(provider: OAuthProvider): Promise<void> {
  const url = await getOAuthAuthorizationUrl(provider);
  window.location.href = url;
}

/**
 * Disconnect OAuth provider
 */
export async function disconnectOAuth(provider: OAuthProvider): Promise<void> {
  await api.delete(`/api/auth/oauth/${provider}`);
}

/**
 * List connected OAuth providers
 */
export async function listOAuthConnections(): Promise<string[]> {
  return api.get<string[]>('/api/auth/oauth/connections');
}

// Role and permission helpers

/**
 * Check if user has a specific role
 */
export function hasRole(user: User | null, role: string): boolean {
  if (!user) return false;
  return user.roles.includes(role);
}

/**
 * Check if user is admin
 */
export function isAdmin(user: User | null): boolean {
  return hasRole(user, 'admin');
}

/**
 * Check if user is manager or admin
 */
export function isManagerOrAbove(user: User | null): boolean {
  return hasRole(user, 'admin') || hasRole(user, 'manager');
}

/**
 * Check if user has any of the given roles
 */
export function hasAnyRole(user: User | null, roles: string[]): boolean {
  if (!user) return false;
  return roles.some((role) => user.roles.includes(role));
}
