/**
 * Battlecard API Client
 *
 * Client-side API functions for battlecard management.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export type BattlecardType =
  | 'competitive'
  | 'objection_handling'
  | 'feature_comparison'
  | 'win_loss_analysis';

export type BattlecardStatus = 'draft' | 'published' | 'archived';

export type FeatureRating = 'superior' | 'comparable' | 'inferior' | 'not_available';

export interface CompetitorStrength {
  area: string;
  description: string;
  impact: string;
}

export interface CompetitorWeakness {
  area: string;
  description: string;
  talking_point: string;
}

export interface Competitor {
  id: string;
  name: string;
  website?: string;
  description: string;
  target_market: string;
  pricing_model?: string;
  key_products: string[];
  strengths: CompetitorStrength[];
  weaknesses: CompetitorWeakness[];
  win_rate_against?: number;
  common_objections: string[];
  last_updated?: string;
  created_at?: string;
}

export interface TalkingPoint {
  category: string;
  point: string;
  supporting_evidence?: string;
}

export interface CompetitiveBattlecard {
  competitor_name: string;
  competitor_overview: string;
  our_positioning: string;
  key_differentiators: string[];
  competitor_strengths: CompetitorStrength[];
  competitor_weaknesses: CompetitorWeakness[];
  talking_points: TalkingPoint[];
  landmines: string[];
  proof_points: string[];
  when_we_win: string[];
  when_we_lose: string[];
}

export interface ObjectionResponse {
  acknowledge: string;
  clarify: string;
  respond: string;
  proof?: string;
  redirect: string;
}

export interface ObjectionCard {
  objection: string;
  category: string;
  severity: string;
  root_cause: string;
  response: ObjectionResponse;
  alternative_responses: string[];
  success_rate?: number;
}

export interface ObjectionHandlingBattlecard {
  context: string;
  objections: ObjectionCard[];
  general_tips: string[];
}

export interface FeatureComparison {
  feature_name: string;
  feature_category: string;
  our_capability: string;
  our_rating: FeatureRating;
  competitor_capabilities: Record<string, string>;
  competitor_ratings: Record<string, FeatureRating>;
  talking_point?: string;
}

export interface FeatureComparisonMatrix {
  title: string;
  our_product: string;
  competitors: string[];
  categories: string[];
  comparisons: FeatureComparison[];
  summary: string;
  key_advantages: string[];
  areas_for_improvement: string[];
}

export interface WinLossFactor {
  factor: string;
  impact: string;
  description: string;
  frequency?: number;
}

export interface WinLossDeal {
  deal_id?: string;
  deal_name: string;
  outcome: 'won' | 'lost';
  competitor?: string;
  deal_size?: number;
  sales_cycle_days?: number;
  key_factors: string[];
  lessons_learned: string;
  date?: string;
}

export interface WinLossAnalysisBattlecard {
  analysis_period: string;
  total_deals_analyzed: number;
  win_rate: number;
  avg_deal_size_won?: number;
  avg_deal_size_lost?: number;
  avg_sales_cycle_won?: number;
  avg_sales_cycle_lost?: number;
  top_win_factors: WinLossFactor[];
  top_loss_factors: WinLossFactor[];
  competitor_breakdown: Record<string, number>;
  recommendations: string[];
  notable_deals: WinLossDeal[];
}

export interface BattlecardContent {
  competitive?: CompetitiveBattlecard;
  objection_handling?: ObjectionHandlingBattlecard;
  feature_comparison?: FeatureComparisonMatrix;
  win_loss_analysis?: WinLossAnalysisBattlecard;
}

export interface Battlecard {
  id: string;
  title: string;
  type: BattlecardType;
  status: BattlecardStatus;
  description?: string;
  content: BattlecardContent;
  tags: string[];
  created_by?: string;
  team_id?: string;
  is_shared: boolean;
  shared_with_teams: string[];
  favorited_by: string[];
  version: number;
  last_updated?: string;
  created_at?: string;
  view_count: number;
  competitor_ids: string[];
}

export interface BattlecardGenerateRequest {
  type: BattlecardType;
  title: string;
  competitor_id?: string;
  competitor_name?: string;
  objection_context?: string;
  objection_categories?: string[];
  competitors_to_compare?: string[];
  feature_categories?: string[];
  analysis_period_days?: number;
  product_context?: string;
  additional_context?: string;
  auto_publish?: boolean;
}

export interface BattlecardResponse {
  success: boolean;
  battlecard?: Battlecard;
  message?: string;
}

export interface BattlecardListResponse {
  success: boolean;
  battlecards: Battlecard[];
  total: number;
  page: number;
  page_size: number;
}

export interface CompetitorListResponse {
  success: boolean;
  competitors: Competitor[];
  total: number;
}

// API Functions

export async function generateBattlecard(
  request: BattlecardGenerateRequest,
  userId?: string,
  teamId?: string
): Promise<BattlecardResponse> {
  const params = new URLSearchParams();
  if (userId) params.set('user_id', userId);
  if (teamId) params.set('team_id', teamId);

  const response = await fetch(
    `${API_BASE}/battlecards/generate?${params.toString()}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  );

  return response.json();
}

export async function getBattlecard(id: string): Promise<BattlecardResponse> {
  const response = await fetch(`${API_BASE}/battlecards/${id}`);
  return response.json();
}

export async function listBattlecards(params?: {
  query?: string;
  type?: BattlecardType;
  status?: BattlecardStatus;
  competitor_id?: string;
  tags?: string[];
  team_id?: string;
  favorites_only?: boolean;
  page?: number;
  page_size?: number;
}): Promise<BattlecardListResponse> {
  const searchParams = new URLSearchParams();

  if (params) {
    if (params.query) searchParams.set('query', params.query);
    if (params.type) searchParams.set('type', params.type);
    if (params.status) searchParams.set('status', params.status);
    if (params.competitor_id) searchParams.set('competitor_id', params.competitor_id);
    if (params.tags) searchParams.set('tags', params.tags.join(','));
    if (params.team_id) searchParams.set('team_id', params.team_id);
    if (params.favorites_only) searchParams.set('favorites_only', 'true');
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());
  }

  const response = await fetch(`${API_BASE}/battlecards/?${searchParams.toString()}`);
  return response.json();
}

export async function updateBattlecard(
  id: string,
  updates: Partial<Battlecard>,
  userId?: string
): Promise<BattlecardResponse> {
  const params = new URLSearchParams();
  if (userId) params.set('user_id', userId);

  const response = await fetch(
    `${API_BASE}/battlecards/${id}?${params.toString()}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    }
  );

  return response.json();
}

export async function deleteBattlecard(id: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/battlecards/${id}`, {
    method: 'DELETE',
  });
  return response.json();
}

export async function shareBattlecard(
  id: string,
  teamIds: string[]
): Promise<BattlecardResponse> {
  const response = await fetch(`${API_BASE}/battlecards/${id}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(teamIds),
  });
  return response.json();
}

export async function toggleFavorite(
  id: string,
  userId: string
): Promise<BattlecardResponse> {
  const response = await fetch(
    `${API_BASE}/battlecards/${id}/favorite?user_id=${userId}`,
    { method: 'POST' }
  );
  return response.json();
}

export async function getFavorites(
  userId: string,
  page = 1,
  pageSize = 20
): Promise<BattlecardListResponse> {
  const response = await fetch(
    `${API_BASE}/battlecards/favorites/list?user_id=${userId}&page=${page}&page_size=${pageSize}`
  );
  return response.json();
}

export async function exportBattlecard(
  id: string,
  format: 'markdown' | 'html' | 'json' | 'pdf' = 'markdown'
): Promise<{ success: boolean; data?: string; error?: string }> {
  const response = await fetch(
    `${API_BASE}/battlecards/${id}/export?format=${format}`,
    { method: 'POST' }
  );
  return response.json();
}

// Competitor API Functions

export async function listCompetitors(params?: {
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<CompetitorListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set('search', params.search);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const response = await fetch(
    `${API_BASE}/battlecards/competitors/?${searchParams.toString()}`
  );
  return response.json();
}

export async function getCompetitor(id: string): Promise<Competitor> {
  const response = await fetch(`${API_BASE}/battlecards/competitors/${id}`);
  return response.json();
}

export async function createCompetitor(competitor: Omit<Competitor, 'id'>): Promise<Competitor> {
  const response = await fetch(`${API_BASE}/battlecards/competitors/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(competitor),
  });
  return response.json();
}

export async function updateCompetitor(
  id: string,
  updates: Partial<Competitor>
): Promise<Competitor> {
  const response = await fetch(`${API_BASE}/battlecards/competitors/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  return response.json();
}

export async function deleteCompetitor(id: string): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE}/battlecards/competitors/${id}`, {
    method: 'DELETE',
  });
  return response.json();
}
