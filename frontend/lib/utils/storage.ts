/**
 * Local storage utilities for auth tokens
 */

import { config } from '../config';

const isBrowser = typeof window !== 'undefined';

/**
 * Get access token from storage
 */
export function getAccessToken(): string | null {
  if (!isBrowser) return null;
  return localStorage.getItem(config.auth.tokenKey);
}

/**
 * Set access token in storage
 */
export function setAccessToken(token: string): void {
  if (!isBrowser) return;
  localStorage.setItem(config.auth.tokenKey, token);
}

/**
 * Remove access token from storage
 */
export function removeAccessToken(): void {
  if (!isBrowser) return;
  localStorage.removeItem(config.auth.tokenKey);
}

/**
 * Get refresh token from storage
 */
export function getRefreshToken(): string | null {
  if (!isBrowser) return null;
  return localStorage.getItem(config.auth.refreshTokenKey);
}

/**
 * Set refresh token in storage
 */
export function setRefreshToken(token: string): void {
  if (!isBrowser) return;
  localStorage.setItem(config.auth.refreshTokenKey, token);
}

/**
 * Remove refresh token from storage
 */
export function removeRefreshToken(): void {
  if (!isBrowser) return;
  localStorage.removeItem(config.auth.refreshTokenKey);
}

/**
 * Get stored user data
 */
export function getStoredUser<T>(): T | null {
  if (!isBrowser) return null;
  const data = localStorage.getItem(config.auth.userKey);
  if (!data) return null;
  try {
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
}

/**
 * Set user data in storage
 */
export function setStoredUser<T>(user: T): void {
  if (!isBrowser) return;
  localStorage.setItem(config.auth.userKey, JSON.stringify(user));
}

/**
 * Remove user data from storage
 */
export function removeStoredUser(): void {
  if (!isBrowser) return;
  localStorage.removeItem(config.auth.userKey);
}

/**
 * Clear all auth data from storage
 */
export function clearAuthStorage(): void {
  removeAccessToken();
  removeRefreshToken();
  removeStoredUser();
}

/**
 * Check if user is authenticated (has tokens)
 */
export function hasAuthTokens(): boolean {
  return !!getAccessToken();
}

/**
 * Parse JWT token payload
 */
export function parseJwt(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string): boolean {
  const payload = parseJwt(token);
  if (!payload || typeof payload.exp !== 'number') return true;

  const expirationTime = payload.exp * 1000; // Convert to milliseconds
  return Date.now() >= expirationTime;
}

/**
 * Check if token needs refresh (expires within threshold)
 */
export function tokenNeedsRefresh(token: string): boolean {
  const payload = parseJwt(token);
  if (!payload || typeof payload.exp !== 'number') return true;

  const expirationTime = payload.exp * 1000;
  const threshold = config.auth.tokenRefreshThreshold;
  return Date.now() >= expirationTime - threshold;
}
