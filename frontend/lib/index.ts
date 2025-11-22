/**
 * Main library exports
 */

// Config
export { config } from './config';
export type { OAuthProvider } from './config';

// API client
export { api, apiRequest, APIError } from './api';

// Auth utilities
export {
  login,
  logout,
  register,
  refreshTokens,
  getCurrentUser,
  changePassword,
  getCachedUser,
  isAuthenticated,
  createAPIKey,
  listAPIKeys,
  revokeAPIKey,
  initiateOAuth,
  disconnectOAuth,
  listOAuthConnections,
  hasRole,
  isAdmin,
  isManagerOrAbove,
  hasAnyRole,
} from './auth';

// Storage utilities
export {
  getAccessToken,
  setAccessToken,
  removeAccessToken,
  getRefreshToken,
  setRefreshToken,
  removeRefreshToken,
  clearAuthStorage,
  hasAuthTokens,
  parseJwt,
  isTokenExpired,
  tokenNeedsRefresh,
} from './utils/storage';

// Hooks
export {
  AuthProvider,
  useAuth,
  useUser,
  useIsAuthenticated,
  useAuthLoading,
  useAPIKeys,
  useOAuth,
} from './hooks';
