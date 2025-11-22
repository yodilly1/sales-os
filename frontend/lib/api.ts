import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Organization,
  User,
  Team,
  TeamWithMembers,
  TeamMember,
  Invitation,
  PaginatedResponse,
  AuthTokens,
  CreateTeamForm,
  UpdateTeamForm,
  InviteUserForm,
  AcceptInvitationForm,
  UpdateUserForm,
  UserRole,
  InvitationStatus,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth header interceptor
    this.client.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    // Add response error handler
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - could redirect to login
          this.accessToken = null;
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            window.location.href = '/auth/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('access_token', token);
      } else {
        localStorage.removeItem('access_token');
      }
    }
  }

  loadTokenFromStorage() {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        this.accessToken = token;
      }
    }
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<AuthTokens> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await this.client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    this.setAccessToken(response.data.access_token);
    return response.data;
  }

  async register(
    organizationName: string,
    organizationSlug: string,
    email: string,
    password: string,
    fullName: string
  ): Promise<{ organization: Organization; user: User } & AuthTokens> {
    const response = await this.client.post('/auth/register', {
      organization_name: organizationName,
      organization_slug: organizationSlug,
      email,
      password,
      full_name: fullName,
    });
    this.setAccessToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
    this.setAccessToken(null);
  }

  // Organization endpoints
  async getCurrentOrganization(): Promise<Organization> {
    const response = await this.client.get('/organizations/current');
    return response.data;
  }

  async updateOrganization(
    orgId: string,
    data: Partial<Organization>
  ): Promise<Organization> {
    const response = await this.client.patch(`/organizations/${orgId}`, data);
    return response.data;
  }

  async getOrganizationStats(orgId: string): Promise<Record<string, unknown>> {
    const response = await this.client.get(`/organizations/${orgId}/stats`);
    return response.data;
  }

  // Team endpoints
  async listTeams(
    page = 1,
    perPage = 20,
    activeOnly = true
  ): Promise<PaginatedResponse<Team>> {
    const response = await this.client.get('/teams', {
      params: { page, per_page: perPage, active_only: activeOnly },
    });
    return response.data;
  }

  async getTeam(teamId: string): Promise<TeamWithMembers> {
    const response = await this.client.get(`/teams/${teamId}`);
    return response.data;
  }

  async createTeam(data: CreateTeamForm): Promise<Team> {
    const response = await this.client.post('/teams', data);
    return response.data;
  }

  async updateTeam(teamId: string, data: UpdateTeamForm): Promise<Team> {
    const response = await this.client.patch(`/teams/${teamId}`, data);
    return response.data;
  }

  async deleteTeam(teamId: string): Promise<void> {
    await this.client.delete(`/teams/${teamId}`);
  }

  // Team member endpoints
  async addTeamMember(
    teamId: string,
    userId: string,
    isTeamLead = false
  ): Promise<TeamMember> {
    const response = await this.client.post(`/teams/${teamId}/members`, {
      user_id: userId,
      is_team_lead: isTeamLead,
    });
    return response.data;
  }

  async removeTeamMember(teamId: string, userId: string): Promise<void> {
    await this.client.delete(`/teams/${teamId}/members/${userId}`);
  }

  async updateTeamMember(
    teamId: string,
    userId: string,
    data: { is_team_lead?: boolean; is_active?: boolean }
  ): Promise<TeamMember> {
    const response = await this.client.patch(
      `/teams/${teamId}/members/${userId}`,
      data
    );
    return response.data;
  }

  async getTeamPerformance(teamId: string): Promise<Record<string, unknown>> {
    const response = await this.client.get(`/teams/${teamId}/performance`);
    return response.data;
  }

  // User endpoints
  async listUsers(
    page = 1,
    perPage = 20,
    activeOnly = true,
    role?: UserRole,
    search?: string
  ): Promise<PaginatedResponse<User>> {
    const response = await this.client.get('/teams/users/all', {
      params: { page, per_page: perPage, active_only: activeOnly, role, search },
    });
    return response.data;
  }

  async getUser(userId: string): Promise<User> {
    const response = await this.client.get(`/teams/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: string, data: UpdateUserForm): Promise<User> {
    const response = await this.client.patch(`/teams/users/${userId}`, data);
    return response.data;
  }

  async deactivateUser(userId: string): Promise<void> {
    await this.client.post(`/teams/users/${userId}/deactivate`);
  }

  async reactivateUser(userId: string): Promise<void> {
    await this.client.post(`/teams/users/${userId}/reactivate`);
  }

  // Invitation endpoints
  async listInvitations(
    page = 1,
    perPage = 20,
    status?: InvitationStatus
  ): Promise<PaginatedResponse<Invitation>> {
    const response = await this.client.get('/teams/invitations', {
      params: { page, per_page: perPage, status },
    });
    return response.data;
  }

  async createInvitation(data: InviteUserForm): Promise<Invitation> {
    const response = await this.client.post('/teams/invitations', data);
    return response.data;
  }

  async acceptInvitation(
    data: AcceptInvitationForm
  ): Promise<{ user: User } & AuthTokens> {
    const response = await this.client.post('/teams/invitations/accept', data);
    this.setAccessToken(response.data.access_token);
    return response.data;
  }

  async revokeInvitation(invitationId: string): Promise<void> {
    await this.client.delete(`/teams/invitations/${invitationId}`);
  }

  async resendInvitation(invitationId: string): Promise<Invitation> {
    const response = await this.client.post(
      `/teams/invitations/${invitationId}/resend`
    );
    return response.data;
  }
}

export const api = new ApiClient();
