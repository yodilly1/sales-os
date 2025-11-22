'use client';

import { clsx } from 'clsx';

export type ContentType = 'deck' | 'proposal' | 'one-pager' | 'battlecard';

interface ContentTypeOption {
  type: ContentType;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const contentTypes: ContentTypeOption[] = [
  {
    type: 'deck',
    title: 'Sales Deck',
    description: 'Presentation slides for pitching your product',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    type: 'proposal',
    title: 'Proposal',
    description: 'Detailed proposal document for prospects',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    type: 'one-pager',
    title: 'One-Pager',
    description: 'Concise overview for quick sharing',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    type: 'battlecard',
    title: 'Battlecard',
    description: 'Competitive analysis and positioning',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
      </svg>
    ),
  },
];

interface ContentTypeSelectorProps {
  selectedType: ContentType | null;
  onSelect: (type: ContentType) => void;
}

export function ContentTypeSelector({
  selectedType,
  onSelect,
}: ContentTypeSelectorProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Choose Content Type</h2>
        <p className="mt-1 text-sm text-gray-500">
          Select the type of content you want to generate
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {contentTypes.map((option) => (
          <button
            key={option.type}
            type="button"
            onClick={() => onSelect(option.type)}
            className={clsx(
              'content-type-option',
              selectedType === option.type && 'selected'
            )}
          >
            <div
              className={clsx(
                'text-gray-400 transition-colors',
                selectedType === option.type && 'text-brand-600'
              )}
            >
              {option.icon}
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-900">{option.title}</div>
              <div className="mt-1 text-xs text-gray-500">{option.description}</div>
            </div>
            {selectedType === option.type && (
              <div className="absolute right-2 top-2">
                <svg
                  className="h-5 w-5 text-brand-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
