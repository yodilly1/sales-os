// API Types for Team Management

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  REP = 'rep',
}

export enum InvitationStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  EXPIRED = 'expired',
  REVOKED = 'revoked',
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  primary_color?: string;
  settings: Record<string, unknown>;
  is_active: boolean;
  plan: string;
  max_users: number;
  max_teams: number;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  organization_id: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  title?: string;
  bio?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  description?: string;
  organization_id: string;
  settings: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  member_count: number;
}

export interface TeamMember {
  id: string;
  user_id: string;
  team_id: string;
  is_team_lead: boolean;
  is_active: boolean;
  created_at: string;
  user_email?: string;
  user_name?: string;
}

export interface TeamWithMembers extends Team {
  members: TeamMember[];
}

export interface Invitation {
  id: string;
  email: string;
  role: UserRole;
  organization_id: string;
  team_id?: string;
  status: InvitationStatus;
  expires_at: string;
  created_at: string;
  invited_by_email?: string;
  invited_by_name?: string;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Form Types
export interface CreateTeamForm {
  name: string;
  slug: string;
  description?: string;
}

export interface UpdateTeamForm {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface InviteUserForm {
  email: string;
  role: UserRole;
  team_id?: string;
  message?: string;
}

export interface AcceptInvitationForm {
  token: string;
  full_name: string;
  password: string;
}

export interface UpdateUserForm {
  full_name?: string;
  title?: string;
  role?: UserRole;
  is_active?: boolean;
}
