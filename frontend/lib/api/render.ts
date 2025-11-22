/**
 * API client for rendering service
 */

const API_BASE = '/api/render';

export interface BrandConfig {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  text_color?: string;
  light_color?: string;
  heading_font?: string;
  body_font?: string;
  logo_url?: string;
}

export interface SlideContent {
  layout?: string;
  title?: string;
  subtitle?: string;
  body?: Array<{ content: string; style?: string }>;
  bullets?: { items: string[]; style?: string };
  image?: { url: string; alt_text?: string };
  metrics?: Array<{ value: string; label: string; trend?: string }>;
  quote?: string;
  quote_author?: string;
  cta_text?: string;
  cta_url?: string;
  speaker_notes?: string;
}

export interface Slide {
  id?: string;
  content: SlideContent;
  transition?: string;
}

export interface DeckRenderRequest {
  content_type: 'pitch_deck' | 'qbr_deck';
  format: 'pdf' | 'pptx' | 'html';
  title: string;
  subtitle?: string;
  slides: Slide[];
  brand?: BrandConfig;
  show_slide_numbers?: boolean;
}

export interface WebDeckConfig {
  enable_navigation?: boolean;
  enable_fullscreen?: boolean;
  enable_presenter_mode?: boolean;
  enable_download?: boolean;
  auto_advance?: boolean;
  auto_advance_interval?: number;
  theme?: 'light' | 'dark';
}

export interface WebDeckRenderRequest extends DeckRenderRequest {
  config?: WebDeckConfig;
  share_id?: string;
}

export interface RenderResult {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  content_type: string;
  format: string;
  created_at: string;
  completed_at?: string;
  file_path?: string;
  file_url?: string;
  file_size?: number;
  page_count?: number;
  error_message?: string;
}

export interface WebDeckResult extends RenderResult {
  share_url?: string;
  embed_code?: string;
  expires_at?: string;
}

/**
 * Render a slide deck
 */
export async function renderDeck(request: DeckRenderRequest): Promise<RenderResult> {
  const response = await fetch(`${API_BASE}/deck`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to render deck');
  }

  return response.json();
}

/**
 * Create an interactive web deck
 */
export async function createWebDeck(request: WebDeckRenderRequest): Promise<WebDeckResult> {
  const response = await fetch(`${API_BASE}/web-deck`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create web deck');
  }

  return response.json();
}

/**
 * Get a web deck by share ID
 */
export async function getWebDeck(shareId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/deck/${shareId}`);

  if (!response.ok) {
    throw new Error('Deck not found');
  }

  return response.text();
}

/**
 * Get available export formats for a content type
 */
export async function getSupportedFormats(contentType: string): Promise<string[]> {
  const response = await fetch(`${API_BASE}/formats/${contentType}`);

  if (!response.ok) {
    throw new Error('Failed to get formats');
  }

  return response.json();
}

/**
 * Get available templates
 */
export async function getTemplates(contentType?: string): Promise<any[]> {
  const url = contentType
    ? `${API_BASE}/templates?content_type=${contentType}`
    : `${API_BASE}/templates`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to get templates');
  }

  const data = await response.json();
  return data.templates;
}

/**
 * Download a rendered file
 */
export function getDownloadUrl(filename: string): string {
  return `/downloads/${filename}`;
}
