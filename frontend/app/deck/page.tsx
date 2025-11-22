'use client';

import { useState } from 'react';
import { DeckViewer, SlideData } from '@/components/deck';

// Sample deck for demo purposes
const sampleSlides: SlideData[] = [
  {
    id: '1',
    content: {
      layout: 'title',
      title: 'Sales OS Platform',
      subtitle: 'VP-of-Sales Operating System',
    },
  },
  {
    id: '2',
    content: {
      layout: 'title_content',
      title: 'The Challenge',
      body: [
        {
          content:
            'Sales teams spend 65% of their time on non-selling activities.',
        },
        {
          content:
            'Lack of standardized methodology leads to inconsistent results.',
        },
      ],
      bullets: {
        items: [
          'Manual CRM data entry',
          'Inconsistent follow-up processes',
          'No visibility into conversation quality',
        ],
        style: 'bullet',
      },
    },
  },
  {
    id: '3',
    content: {
      layout: 'metrics',
      title: 'The Impact',
      metrics: [
        { value: '40%', label: 'Increase in Win Rate', trend: 'up' },
        { value: '3x', label: 'Faster Deal Velocity', trend: 'up' },
        { value: '65%', label: 'Less Admin Time', trend: 'down' },
      ],
    },
  },
  {
    id: '4',
    content: {
      layout: 'quote',
      quote:
        'Sales OS transformed how our team operates. We closed 40% more deals in Q1.',
      quote_author: 'Sarah Chen, VP of Sales at TechCorp',
    },
  },
  {
    id: '5',
    content: {
      layout: 'cta',
      title: 'Ready to Transform Your Sales?',
      cta_text: 'Schedule a Demo',
      cta_url: '/demo',
    },
  },
];

export default function DeckPage() {
  const [viewerMode, setViewerMode] = useState<'demo' | 'upload'>('demo');

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Demo viewer */}
      {viewerMode === 'demo' && (
        <>
          <div className="absolute top-4 left-4 z-10">
            <button
              onClick={() => setViewerMode('upload')}
              className="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition"
            >
              ← Back
            </button>
          </div>
          <DeckViewer
            slides={sampleSlides}
            title="Sales OS Demo"
            config={{
              enableNavigation: true,
              enableFullscreen: true,
              enablePresenterMode: true,
              enableDownload: false,
              theme: 'dark',
            }}
          />
        </>
      )}

      {/* Upload/create mode */}
      {viewerMode === 'upload' && (
        <div className="max-w-4xl mx-auto py-16 px-4">
          <h1 className="text-3xl font-bold text-white mb-8">
            Web Deck Viewer
          </h1>

          <div className="grid gap-6">
            <div className="bg-gray-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">
                View Demo Deck
              </h2>
              <p className="text-gray-400 mb-4">
                See a sample presentation with the deck viewer features.
              </p>
              <button
                onClick={() => setViewerMode('demo')}
                className="px-6 py-3 bg-brand-primary text-white rounded-lg hover:bg-brand-secondary transition"
              >
                Launch Demo
              </button>
            </div>

            <div className="bg-gray-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">
                Open Shared Deck
              </h2>
              <p className="text-gray-400 mb-4">
                Enter a share ID to view a presentation.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = e.target as HTMLFormElement;
                  const shareId = (
                    form.elements.namedItem('shareId') as HTMLInputElement
                  ).value;
                  if (shareId) {
                    window.location.href = `/deck/${shareId}`;
                  }
                }}
                className="flex gap-4"
              >
                <input
                  type="text"
                  name="shareId"
                  placeholder="Enter share ID..."
                  className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-brand-primary focus:outline-none"
                />
                <button
                  type="submit"
                  className="px-6 py-3 bg-brand-primary text-white rounded-lg hover:bg-brand-secondary transition"
                >
                  Open
                </button>
              </form>
            </div>

            <div className="bg-gray-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">
                Features
              </h2>
              <ul className="space-y-3 text-gray-400">
                <li className="flex items-center gap-3">
                  <span className="text-brand-accent">✓</span>
                  Keyboard navigation (arrow keys, space)
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-brand-accent">✓</span>
                  Touch/swipe support for mobile
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-brand-accent">✓</span>
                  Fullscreen presentation mode
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-brand-accent">✓</span>
                  Presenter view with speaker notes
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-brand-accent">✓</span>
                  Progress indicator
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-brand-accent">✓</span>
                  Export to PDF/PPTX
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
