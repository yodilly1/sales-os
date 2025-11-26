import { apiClient } from './client';
import type { ContentFormData } from '@/components/content/ContentForm';
import type { GeneratedContent, ContentSection } from '@/components/content/ContentPreview';
import type { ExportFormat } from '@/components/content/ExportMenu';

// Backend request types
export interface ProductInfo {
  name: string;
  description: string;
  key_features?: string[];
  value_propositions?: string[];
}

export interface AudienceInfo {
  audience_type?: string;
  company_name?: string;
  industry?: string;
  pain_points?: string[];
  role?: string;
}

export interface CompetitorInfo {
  name: string;
  description?: string;
  weaknesses?: string[];
}

export interface GenerateContentRequest {
  content_type: string;
  goal: string;
  product_info: ProductInfo;
  audience?: AudienceInfo;
  brand_voice?: string;
  competitors?: CompetitorInfo[];
  include_speaker_notes?: boolean;
  include_visual_suggestions?: boolean;
}

// Backend response types
export interface BackendSlide {
  slide_number: number;
  title: string;
  subtitle?: string;
  content_type: string;
  main_content: string | string[];
  speaker_notes?: string;
  visual_suggestions?: string;
  transition_note?: string;
}

export interface BackendDeckContent {
  title: string;
  subtitle?: string;
  deck_type: string;
  slides: BackendSlide[];
  total_slides: number;
  estimated_duration_minutes: number;
  key_messages: string[];
  call_to_action: string;
}

export interface BackendProposalSection {
  section_number: number;
  title: string;
  content: string;
  subsections?: Array<{ title: string; content: string }>;
}

export interface BackendProposalContent {
  title: string;
  proposal_type: string;
  executive_summary: string;
  sections: BackendProposalSection[];
  next_steps?: string[];
}

export interface BackendOnePagerContent {
  title: string;
  one_pager_type: string;
  headline: string;
  subheadline?: string;
  overview: string;
  key_points: Array<{ title: string; description: string }>;
  benefits: string[];
  call_to_action: string;
}

export interface BackendBattlecardContent {
  title: string;
  battlecard_type: string;
  competitor_name?: string;
  competitor_overview?: string;
  their_strengths?: string[];
  their_weaknesses?: string[];
  our_advantages?: string[];
  head_to_head?: Array<{ feature: string; us: string; them: string }>;
  win_themes?: string[];
  objections?: Array<{ objection: string; response: string }>;
}

export interface BackendContentMetadata {
  content_id: string;
  content_type: string;
  status: string;
  created_at: string;
  generation_time_ms?: number;
  model_used?: string;
}

export interface BackendContentResponse {
  metadata: BackendContentMetadata;
  content: BackendDeckContent | BackendProposalContent | BackendOnePagerContent | BackendBattlecardContent;
  suggestions?: string[];
  wbd_alignment_score?: number;
}

export interface ExportContentResponse {
  download_url?: string;
  share_link?: string;
  content_text?: string;
}

// Map frontend content type to backend content type
function mapContentType(frontendType: string): string {
  const mapping: Record<string, string> = {
    'deck': 'deck_pitch',
    'proposal': 'proposal_custom',
    'one-pager': 'one_pager_product',
    'battlecard': 'battlecard_competitive',
  };
  return mapping[frontendType] || 'deck_pitch';
}

// Map frontend tone to backend brand voice
function mapBrandVoice(tone: string): string {
  const mapping: Record<string, string> = {
    'professional': 'professional',
    'conversational': 'conversational',
    'technical': 'technical',
    'persuasive': 'professional', // Map to professional as closest match
    'executive': 'executive',
  };
  return mapping[tone] || 'professional';
}

function mapFormToRequest(formData: ContentFormData): GenerateContentRequest {
  // Parse key features from newline-separated string
  const keyFeatures = formData.keyFeatures
    ? formData.keyFeatures.split('\n').filter((f) => f.trim())
    : [];

  // Parse pain points from string
  const painPoints = formData.painPoints
    ? formData.painPoints.split('\n').filter((p) => p.trim())
    : [];

  const request: GenerateContentRequest = {
    content_type: mapContentType(formData.contentType),
    goal: formData.goal,
    product_info: {
      name: formData.productName,
      description: formData.productDescription,
      key_features: keyFeatures.length > 0 ? keyFeatures : undefined,
    },
    audience: {
      company_name: formData.targetAudience,
      role: formData.audienceRole,
      industry: formData.industryFocus,
      pain_points: painPoints.length > 0 ? painPoints : undefined,
    },
    brand_voice: mapBrandVoice(formData.tone),
    include_speaker_notes: true,
    include_visual_suggestions: true,
  };

  // Add competitor info for battlecards
  if (formData.contentType === 'battlecard' && formData.competitorName) {
    request.competitors = [
      {
        name: formData.competitorName,
        weaknesses: formData.competitorWeaknesses
          ? formData.competitorWeaknesses.split('\n').filter((w) => w.trim())
          : undefined,
      },
    ];
  }

  return request;
}

// Convert backend deck slides to frontend sections
function convertDeckToSections(content: BackendDeckContent): ContentSection[] {
  return content.slides.map((slide, index) => {
    // Determine section type based on slide content
    const mainContent = Array.isArray(slide.main_content)
      ? slide.main_content.join('\n')
      : slide.main_content;

    let sectionType: ContentSection['type'] = 'text';
    if (slide.content_type === 'bullets' || Array.isArray(slide.main_content)) {
      sectionType = 'bullets';
    } else if (slide.content_type === 'quote') {
      sectionType = 'quote';
    }

    return {
      id: `slide-${slide.slide_number || index + 1}`,
      title: slide.title,
      content: mainContent,
      type: sectionType,
    };
  });
}

// Convert backend proposal sections to frontend sections
function convertProposalToSections(content: BackendProposalContent): ContentSection[] {
  const sections: ContentSection[] = [];

  // Add executive summary
  if (content.executive_summary) {
    sections.push({
      id: 'exec-summary',
      title: 'Executive Summary',
      content: content.executive_summary,
      type: 'text',
    });
  }

  // Add all proposal sections
  content.sections.forEach((section) => {
    sections.push({
      id: `section-${section.section_number}`,
      title: section.title,
      content: section.content,
      type: 'text',
    });
  });

  // Add next steps if present
  if (content.next_steps && content.next_steps.length > 0) {
    sections.push({
      id: 'next-steps',
      title: 'Next Steps',
      content: content.next_steps.join('\n'),
      type: 'bullets',
    });
  }

  return sections;
}

// Convert backend one-pager to frontend sections
function convertOnePagerToSections(content: BackendOnePagerContent): ContentSection[] {
  const sections: ContentSection[] = [];

  // Headline
  sections.push({
    id: 'headline',
    title: content.headline,
    content: content.subheadline || '',
    type: 'heading',
  });

  // Overview
  sections.push({
    id: 'overview',
    title: 'Overview',
    content: content.overview,
    type: 'text',
  });

  // Key Points
  if (content.key_points && content.key_points.length > 0) {
    sections.push({
      id: 'key-points',
      title: 'Key Points',
      content: content.key_points.map((p) => `${p.title}: ${p.description}`).join('\n'),
      type: 'bullets',
    });
  }

  // Benefits
  if (content.benefits && content.benefits.length > 0) {
    sections.push({
      id: 'benefits',
      title: 'Benefits',
      content: content.benefits.join('\n'),
      type: 'bullets',
    });
  }

  // Call to Action
  if (content.call_to_action) {
    sections.push({
      id: 'cta',
      title: 'Next Steps',
      content: content.call_to_action,
      type: 'callout',
    });
  }

  return sections;
}

// Convert backend battlecard to frontend sections
function convertBattlecardToSections(content: BackendBattlecardContent): ContentSection[] {
  const sections: ContentSection[] = [];

  // Competitor overview
  if (content.competitor_name && content.competitor_overview) {
    sections.push({
      id: 'competitor-overview',
      title: `About ${content.competitor_name}`,
      content: content.competitor_overview,
      type: 'text',
    });
  }

  // Their Strengths
  if (content.their_strengths && content.their_strengths.length > 0) {
    sections.push({
      id: 'their-strengths',
      title: 'Competitor Strengths',
      content: content.their_strengths.join('\n'),
      type: 'bullets',
    });
  }

  // Their Weaknesses
  if (content.their_weaknesses && content.their_weaknesses.length > 0) {
    sections.push({
      id: 'their-weaknesses',
      title: 'Competitor Weaknesses',
      content: content.their_weaknesses.join('\n'),
      type: 'bullets',
    });
  }

  // Our Advantages
  if (content.our_advantages && content.our_advantages.length > 0) {
    sections.push({
      id: 'our-advantages',
      title: 'Our Advantages',
      content: content.our_advantages.join('\n'),
      type: 'bullets',
    });
  }

  // Head to Head Comparison
  if (content.head_to_head && content.head_to_head.length > 0) {
    sections.push({
      id: 'head-to-head',
      title: 'Feature Comparison',
      content: content.head_to_head
        .map((h) => `${h.feature}: Us - ${h.us} | Them - ${h.them}`)
        .join('\n'),
      type: 'text',
    });
  }

  // Win Themes
  if (content.win_themes && content.win_themes.length > 0) {
    sections.push({
      id: 'win-themes',
      title: 'Key Win Themes',
      content: content.win_themes.join('\n'),
      type: 'bullets',
    });
  }

  // Objection Handling
  if (content.objections && content.objections.length > 0) {
    sections.push({
      id: 'objections',
      title: 'Objection Handling',
      content: content.objections
        .map((o) => `Q: ${o.objection}\nA: ${o.response}`)
        .join('\n\n'),
      type: 'text',
    });
  }

  return sections;
}

function mapResponseToContent(
  response: BackendContentResponse,
  contentType: string
): GeneratedContent {
  const content = response.content;
  let sections: ContentSection[] = [];
  let title = '';
  let subtitle = '';

  // Determine content type from metadata
  const backendContentType = response.metadata.content_type;

  if (backendContentType.startsWith('deck_')) {
    const deckContent = content as BackendDeckContent;
    title = deckContent.title;
    subtitle = deckContent.subtitle || `${deckContent.total_slides} slides`;
    sections = convertDeckToSections(deckContent);
  } else if (backendContentType.startsWith('proposal_')) {
    const proposalContent = content as BackendProposalContent;
    title = proposalContent.title;
    subtitle = 'Business Proposal';
    sections = convertProposalToSections(proposalContent);
  } else if (backendContentType.startsWith('one_pager_')) {
    const onePagerContent = content as BackendOnePagerContent;
    title = onePagerContent.title;
    subtitle = onePagerContent.subheadline || 'One-Pager';
    sections = convertOnePagerToSections(onePagerContent);
  } else if (backendContentType.startsWith('battlecard_')) {
    const battlecardContent = content as BackendBattlecardContent;
    title = battlecardContent.title;
    subtitle = battlecardContent.competitor_name
      ? `vs ${battlecardContent.competitor_name}`
      : 'Competitive Battlecard';
    sections = convertBattlecardToSections(battlecardContent);
  }

  return {
    id: response.metadata.content_id,
    contentType: contentType as GeneratedContent['contentType'],
    title,
    subtitle,
    sections,
    generatedAt: response.metadata.created_at,
  };
}

export const contentApi = {
  async generateContent(formData: ContentFormData): Promise<GeneratedContent> {
    const request = mapFormToRequest(formData);
    const response = await apiClient.post<BackendContentResponse>(
      '/content/generate',
      request
    );
    return mapResponseToContent(response, formData.contentType);
  },

  async getContent(id: string): Promise<GeneratedContent> {
    const response = await apiClient.get<BackendContentResponse>(`/content/${id}`);
    // Extract content type from the response
    const contentType = response.metadata.content_type;
    let frontendType = 'deck';
    if (contentType.startsWith('proposal_')) frontendType = 'proposal';
    else if (contentType.startsWith('one_pager_')) frontendType = 'one-pager';
    else if (contentType.startsWith('battlecard_')) frontendType = 'battlecard';

    return mapResponseToContent(response, frontendType);
  },

  async exportContent(
    id: string,
    format: ExportFormat
  ): Promise<ExportContentResponse> {
    return apiClient.post<ExportContentResponse>(`/content/${id}/export`, {
      format,
    });
  },

  async listContent(): Promise<GeneratedContent[]> {
    const response = await apiClient.get<BackendContentResponse[]>('/content');
    return response.map((item) => {
      const contentType = item.metadata.content_type;
      let frontendType = 'deck';
      if (contentType.startsWith('proposal_')) frontendType = 'proposal';
      else if (contentType.startsWith('one_pager_')) frontendType = 'one-pager';
      else if (contentType.startsWith('battlecard_')) frontendType = 'battlecard';
      return mapResponseToContent(item, frontendType);
    });
  },

  async deleteContent(id: string): Promise<void> {
    await apiClient.delete(`/content/${id}`);
  },
};
