// Settings types for Sales OS

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'manager' | 'member';
  organizationId: string;
  preferences: UserPreferences;
  createdAt: string;
  updatedAt: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  dateFormat: string;
  defaultView: 'dashboard' | 'transcripts' | 'prospects';
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo?: string;
  primaryColor?: string;
  secondaryColor?: string;
  defaults: OrganizationDefaults;
  createdAt: string;
  updatedAt: string;
}

export interface OrganizationDefaults {
  spicedMethodology: 'standard' | 'custom';
  contentTone: 'formal' | 'casual' | 'professional';
  enrichmentProvider: string;
  crmSyncEnabled: boolean;
  autoAnalyzeTranscripts: boolean;
}

export interface Integration {
  id: string;
  type: 'hubspot' | 'avoma' | 'salesforce' | 'gong' | 'zoom';
  name: string;
  description: string;
  status: 'connected' | 'disconnected' | 'error' | 'pending';
  connectedAt?: string;
  lastSyncAt?: string;
  errorMessage?: string;
  config?: Record<string, unknown>;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  createdAt: string;
  lastUsedAt?: string;
  expiresAt?: string;
  scopes: string[];
  isActive: boolean;
}

export interface ApiKeyCreate {
  name: string;
  scopes: string[];
  expiresAt?: string;
}

export interface ApiKeyCreateResponse {
  key: ApiKey;
  secret: string; // Only returned once on creation
}

export interface NotificationPreferences {
  email: EmailNotifications;
  inApp: InAppNotifications;
  digest: DigestSettings;
}

export interface EmailNotifications {
  transcriptAnalyzed: boolean;
  contentGenerated: boolean;
  prospectEnriched: boolean;
  weeklyReport: boolean;
  teamUpdates: boolean;
  securityAlerts: boolean;
}

export interface InAppNotifications {
  transcriptAnalyzed: boolean;
  contentGenerated: boolean;
  prospectEnriched: boolean;
  coachingFeedback: boolean;
  mentions: boolean;
}

export interface DigestSettings {
  enabled: boolean;
  frequency: 'daily' | 'weekly' | 'monthly';
  dayOfWeek?: number; // 0-6 for weekly
  timeOfDay: string; // HH:MM format
}

// API Response types
export interface SettingsResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface UpdateUserRequest {
  name?: string;
  avatar?: string;
  preferences?: Partial<UserPreferences>;
}

export interface UpdateOrganizationRequest {
  name?: string;
  logo?: string;
  primaryColor?: string;
  secondaryColor?: string;
  defaults?: Partial<OrganizationDefaults>;
}
