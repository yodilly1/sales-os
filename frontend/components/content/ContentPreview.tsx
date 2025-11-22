'use client';

import { useState } from 'react';
import { clsx } from 'clsx';
import { Badge, ProgressBar, Spinner } from '@/components/ui';
import type { ContentType } from './ContentTypeSelector';

export interface ContentSection {
  id: string;
  title: string;
  content: string;
  type: 'heading' | 'text' | 'bullets' | 'quote' | 'callout';
}

export interface GeneratedContent {
  id: string;
  contentType: ContentType;
  title: string;
  subtitle?: string;
  sections: ContentSection[];
  generatedAt: string;
}

interface ContentPreviewProps {
  content: GeneratedContent | null;
  isGenerating: boolean;
  progress: number;
  currentStep?: string;
}

const contentTypeLabels: Record<ContentType, string> = {
  deck: 'Sales Deck',
  proposal: 'Proposal',
  'one-pager': 'One-Pager',
  battlecard: 'Battlecard',
};

function EmptyState() {
  return (
    <div className="flex h-full min-h-[500px] flex-col items-center justify-center text-center">
      <div className="rounded-full bg-gray-100 p-4">
        <svg
          className="h-8 w-8 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>
      <h3 className="mt-4 text-sm font-medium text-gray-900">No content yet</h3>
      <p className="mt-1 text-sm text-gray-500">
        Fill out the form to generate your content
      </p>
    </div>
  );
}

function GeneratingState({ progress, currentStep }: { progress: number; currentStep?: string }) {
  return (
    <div className="flex h-full min-h-[500px] flex-col items-center justify-center text-center">
      <Spinner size="lg" />
      <h3 className="mt-4 text-sm font-medium text-gray-900">Generating your content...</h3>
      {currentStep && (
        <p className="mt-1 text-sm text-gray-500">{currentStep}</p>
      )}
      <div className="mt-6 w-full max-w-xs">
        <ProgressBar
          value={progress}
          showPercentage
          animated
        />
      </div>
    </div>
  );
}

function SectionRenderer({ section }: { section: ContentSection }) {
  switch (section.type) {
    case 'heading':
      return (
        <div className="mb-4">
          <h3 className="text-xl font-semibold text-gray-900">{section.title}</h3>
          {section.content && (
            <p className="mt-1 text-gray-600">{section.content}</p>
          )}
        </div>
      );

    case 'text':
      return (
        <div className="mb-4">
          {section.title && (
            <h4 className="mb-2 font-medium text-gray-800">{section.title}</h4>
          )}
          <p className="text-gray-600 leading-relaxed">{section.content}</p>
        </div>
      );

    case 'bullets':
      return (
        <div className="mb-4">
          {section.title && (
            <h4 className="mb-2 font-medium text-gray-800">{section.title}</h4>
          )}
          <ul className="space-y-2">
            {section.content.split('\n').filter(Boolean).map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-gray-600">
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      );

    case 'quote':
      return (
        <blockquote className="mb-4 border-l-4 border-brand-500 bg-brand-50 py-3 pl-4 pr-6 italic text-gray-700">
          {section.content}
        </blockquote>
      );

    case 'callout':
      return (
        <div className="mb-4 rounded-lg border border-brand-200 bg-brand-50 p-4">
          {section.title && (
            <h4 className="mb-1 font-medium text-brand-800">{section.title}</h4>
          )}
          <p className="text-sm text-brand-700">{section.content}</p>
        </div>
      );

    default:
      return null;
  }
}

export function ContentPreview({
  content,
  isGenerating,
  progress,
  currentStep,
}: ContentPreviewProps) {
  const [viewMode, setViewMode] = useState<'preview' | 'slides'>('preview');

  if (isGenerating) {
    return (
      <div className="preview-panel">
        <GeneratingState progress={progress} currentStep={currentStep} />
      </div>
    );
  }

  if (!content) {
    return (
      <div className="preview-panel">
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="preview-panel scrollbar-thin">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Badge variant="info">{contentTypeLabels[content.contentType]}</Badge>
          <span className="text-xs text-gray-500">
            Generated {new Date(content.generatedAt).toLocaleString()}
          </span>
        </div>
        {content.contentType === 'deck' && (
          <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
            <button
              onClick={() => setViewMode('preview')}
              className={clsx(
                'rounded-md px-3 py-1 text-xs font-medium transition-colors',
                viewMode === 'preview'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              Document
            </button>
            <button
              onClick={() => setViewMode('slides')}
              className={clsx(
                'rounded-md px-3 py-1 text-xs font-medium transition-colors',
                viewMode === 'slides'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              Slides
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-gray-900">{content.title}</h1>
        {content.subtitle && (
          <p className="text-lg text-gray-600">{content.subtitle}</p>
        )}
      </div>

      <hr className="my-6 border-gray-200" />

      {viewMode === 'preview' ? (
        <div className="space-y-6">
          {content.sections.map((section) => (
            <SectionRenderer key={section.id} section={section} />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {content.sections.map((section, index) => (
            <div
              key={section.id}
              className="aspect-video rounded-lg border border-gray-200 bg-gradient-to-br from-gray-50 to-white p-6 shadow-sm"
            >
              <div className="flex h-full flex-col">
                <div className="mb-2 text-xs text-gray-400">Slide {index + 1}</div>
                <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                <p className="mt-2 flex-1 text-sm text-gray-600 line-clamp-4">
                  {section.content}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
