/**
 * Frontend configuration
 */

export const config = {
  // API configuration
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',

  // Auth configuration
  auth: {
    tokenKey: 'sales_os_access_token',
    refreshTokenKey: 'sales_os_refresh_token',
    userKey: 'sales_os_user',
    tokenRefreshThreshold: 5 * 60 * 1000, // 5 minutes before expiry
  },

  // OAuth providers
  oauth: {
    hubspot: {
      name: 'HubSpot',
      icon: 'hubspot',
    },
    avoma: {
      name: 'Avoma',
      icon: 'avoma',
    },
  },
} as const;

export type OAuthProvider = keyof typeof config.oauth;
