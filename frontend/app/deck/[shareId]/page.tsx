'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function SharedDeckPage() {
  const params = useParams();
  const shareId = params.shareId as string;
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDeck() {
      try {
        const response = await fetch(`/api/render/deck/${shareId}`);
        if (!response.ok) {
          throw new Error('Deck not found');
        }
        const content = await response.text();
        setHtml(content);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load deck');
      } finally {
        setLoading(false);
      }
    }

    loadDeck();
  }, [shareId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary mx-auto mb-4"></div>
          <p className="text-gray-400">Loading presentation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">📊</div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Presentation Not Found
          </h1>
          <p className="text-gray-400 mb-6">{error}</p>
          <a
            href="/deck"
            className="px-6 py-3 bg-brand-primary text-white rounded-lg hover:bg-brand-secondary transition inline-block"
          >
            Go to Deck Viewer
          </a>
        </div>
      </div>
    );
  }

  // Render the deck HTML in an iframe
  return (
    <iframe
      srcDoc={html || ''}
      style={{
        width: '100vw',
        height: '100vh',
        border: 'none',
      }}
      title="Presentation"
    />
  );
}
