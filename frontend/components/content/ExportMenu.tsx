'use client';

import { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { Button } from '@/components/ui';
import type { GeneratedContent } from './ContentPreview';

export type ExportFormat = 'pdf' | 'pptx' | 'link' | 'copy';

interface ExportOption {
  format: ExportFormat;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const exportOptions: ExportOption[] = [
  {
    format: 'pdf',
    label: 'Download PDF',
    description: 'High-quality PDF document',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
    ),
  },
  {
    format: 'pptx',
    label: 'Download PPTX',
    description: 'PowerPoint presentation',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    ),
  },
  {
    format: 'link',
    label: 'Share Link',
    description: 'Create a shareable web link',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
        />
      </svg>
    ),
  },
  {
    format: 'copy',
    label: 'Copy to Clipboard',
    description: 'Copy content as plain text',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
        />
      </svg>
    ),
  },
];

interface ExportMenuProps {
  content: GeneratedContent | null;
  onExport: (format: ExportFormat) => Promise<void>;
  disabled?: boolean;
}

export function ExportMenu({ content, onExport, disabled = false }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format: ExportFormat) => {
    setExportingFormat(format);
    try {
      await onExport(format);
      if (format === 'link' || format === 'copy') {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2000);
      }
    } finally {
      setExportingFormat(null);
      setIsOpen(false);
    }
  };

  return (
    <div ref={menuRef} className="relative">
      <Button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || !content}
        rightIcon={
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        }
      >
        Export
      </Button>

      {isOpen && (
        <div className="absolute right-0 z-10 mt-2 w-64 origin-top-right rounded-xl border border-gray-200 bg-white p-2 shadow-lg">
          <div className="space-y-1">
            {exportOptions.map((option) => {
              const isExporting = exportingFormat === option.format;
              const showCopied =
                copiedLink && (option.format === 'link' || option.format === 'copy');

              return (
                <button
                  key={option.format}
                  onClick={() => handleExport(option.format)}
                  disabled={isExporting}
                  className={clsx(
                    'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors',
                    isExporting
                      ? 'cursor-not-allowed bg-gray-50'
                      : 'hover:bg-gray-50'
                  )}
                >
                  <div
                    className={clsx(
                      'flex h-9 w-9 items-center justify-center rounded-lg',
                      isExporting ? 'bg-gray-100' : 'bg-brand-50 text-brand-600'
                    )}
                  >
                    {isExporting ? (
                      <svg
                        className="h-4 w-4 animate-spin text-gray-400"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                    ) : (
                      option.icon
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      {showCopied ? 'Copied!' : option.label}
                    </div>
                    <div className="text-xs text-gray-500">{option.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
