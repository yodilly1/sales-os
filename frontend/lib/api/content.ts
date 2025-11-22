import { apiClient } from './client';
import type { ContentFormData } from '@/components/content/ContentForm';
import type { GeneratedContent, ContentSection } from '@/components/content/ContentPreview';
import type { ExportFormat } from '@/components/content/ExportMenu';

export interface GenerateContentRequest {
  content_type: string;
  goal: string;
  product_name: string;
  product_description: string;
  key_features?: string;
  target_audience: string;
  audience_role?: string;
  industry_focus?: string;
  pain_points?: string;
  competitor_name?: string;
  competitor_weaknesses?: string;
  tone: string;
}

export interface GenerateContentResponse {
  id: string;
  content_type: string;
  title: string;
  subtitle?: string;
  sections: Array<{
    id: string;
    title: string;
    content: string;
    type: 'heading' | 'text' | 'bullets' | 'quote' | 'callout';
  }>;
  generated_at: string;
}

export interface ExportContentResponse {
  download_url?: string;
  share_link?: string;
  content_text?: string;
}

function mapFormToRequest(formData: ContentFormData): GenerateContentRequest {
  return {
    content_type: formData.contentType,
    goal: formData.goal,
    product_name: formData.productName,
    product_description: formData.productDescription,
    key_features: formData.keyFeatures,
    target_audience: formData.targetAudience,
    audience_role: formData.audienceRole,
    industry_focus: formData.industryFocus,
    pain_points: formData.painPoints,
    competitor_name: formData.competitorName,
    competitor_weaknesses: formData.competitorWeaknesses,
    tone: formData.tone,
  };
}

function mapResponseToContent(response: GenerateContentResponse): GeneratedContent {
  return {
    id: response.id,
    contentType: response.content_type as GeneratedContent['contentType'],
    title: response.title,
    subtitle: response.subtitle,
    sections: response.sections as ContentSection[],
    generatedAt: response.generated_at,
  };
}

export const contentApi = {
  async generateContent(formData: ContentFormData): Promise<GeneratedContent> {
    const request = mapFormToRequest(formData);
    const response = await apiClient.post<GenerateContentResponse>(
      '/content/generate',
      request
    );
    return mapResponseToContent(response);
  },

  async getContent(id: string): Promise<GeneratedContent> {
    const response = await apiClient.get<GenerateContentResponse>(`/content/${id}`);
    return mapResponseToContent(response);
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
    const response = await apiClient.get<GenerateContentResponse[]>('/content');
    return response.map(mapResponseToContent);
  },

  async deleteContent(id: string): Promise<void> {
    await apiClient.delete(`/content/${id}`);
  },
};

// Mock data generator for development/demo purposes
export function generateMockContent(formData: ContentFormData): GeneratedContent {
  const contentTypeLabels: Record<string, string> = {
    deck: 'Sales Deck',
    proposal: 'Business Proposal',
    'one-pager': 'Executive Summary',
    battlecard: 'Competitive Battlecard',
  };

  const baseTitle = `${formData.productName} - ${contentTypeLabels[formData.contentType]}`;

  const sections: ContentSection[] = [];

  // Executive Summary
  sections.push({
    id: '1',
    title: 'Executive Summary',
    content: `${formData.productName} addresses the critical challenges faced by ${formData.targetAudience}. Our solution delivers measurable results through innovative technology and proven methodologies.`,
    type: 'text',
  });

  // Problem Statement
  sections.push({
    id: '2',
    title: 'The Challenge',
    content: formData.painPoints || `Organizations today face increasing pressure to optimize operations while maintaining quality and reducing costs.`,
    type: 'text',
  });

  // Solution Overview
  sections.push({
    id: '3',
    title: 'Our Solution',
    content: formData.productDescription,
    type: 'text',
  });

  // Key Features
  if (formData.keyFeatures) {
    sections.push({
      id: '4',
      title: 'Key Features & Benefits',
      content: formData.keyFeatures,
      type: 'bullets',
    });
  }

  // Value Proposition
  sections.push({
    id: '5',
    title: 'Why Choose Us',
    content: `Proven track record with industry-leading results\nDedicated support and implementation team\nFlexible deployment options\nContinuous innovation and updates`,
    type: 'bullets',
  });

  // For battlecards, add competitive section
  if (formData.contentType === 'battlecard' && formData.competitorName) {
    sections.push({
      id: '6',
      title: `${formData.productName} vs ${formData.competitorName}`,
      content: formData.competitorWeaknesses || 'Our solution offers superior performance, better support, and more flexible pricing compared to alternatives.',
      type: 'text',
    });
  }

  // Call to Action
  sections.push({
    id: '7',
    title: 'Next Steps',
    content: `Ready to transform your ${formData.industryFocus || 'business'} operations? Contact us today to schedule a personalized demo and see how ${formData.productName} can help you achieve your goals.`,
    type: 'callout',
  });

  return {
    id: `mock-${Date.now()}`,
    contentType: formData.contentType,
    title: baseTitle,
    subtitle: `Tailored for ${formData.targetAudience}`,
    sections,
    generatedAt: new Date().toISOString(),
  };
}
