'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  listCompetitors,
  createCompetitor,
  deleteCompetitor,
  type Competitor,
} from '@/lib/api/battlecards';

export default function CompetitorsPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Form state
  const [name, setName] = useState('');
  const [website, setWebsite] = useState('');
  const [description, setDescription] = useState('');
  const [targetMarket, setTargetMarket] = useState('');
  const [pricingModel, setPricingModel] = useState('');
  const [keyProducts, setKeyProducts] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCompetitors();
  }, [searchQuery]);

  async function loadCompetitors() {
    try {
      setLoading(true);
      const response = await listCompetitors({ search: searchQuery || undefined });
      if (response.success) {
        setCompetitors(response.competitors);
      }
    } catch (err) {
      console.error('Failed to load competitors:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !description || !targetMarket) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const competitor = await createCompetitor({
        name,
        website: website || undefined,
        description,
        target_market: targetMarket,
        pricing_model: pricingModel || undefined,
        key_products: keyProducts
          .split(',')
          .map((p) => p.trim())
          .filter(Boolean),
        strengths: [],
        weaknesses: [],
        common_objections: [],
      });

      setCompetitors((prev) => [...prev, competitor]);
      resetForm();
      setShowForm(false);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create competitor';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this competitor?')) {
      return;
    }

    try {
      await deleteCompetitor(id);
      setCompetitors((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Failed to delete competitor:', err);
    }
  }

  function resetForm() {
    setName('');
    setWebsite('');
    setDescription('');
    setTargetMarket('');
    setPricingModel('');
    setKeyProducts('');
    setError(null);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/battlecards"
                className="text-gray-500 hover:text-gray-700"
              >
                ← Back
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Competitors
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                  Manage your competitive intelligence database
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              + Add Competitor
            </button>
          </div>
        </div>
      </header>

      {/* Search */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <input
          type="text"
          placeholder="Search competitors..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Add Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  Add Competitor
                </h2>
                <button
                  onClick={() => {
                    setShowForm(false);
                    resetForm();
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Salesforce"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Website
                  </label>
                  <input
                    type="url"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description *
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the competitor..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Target Market *
                  </label>
                  <input
                    type="text"
                    value={targetMarket}
                    onChange={(e) => setTargetMarket(e.target.value)}
                    placeholder="e.g., Enterprise, SMB, Mid-market"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Pricing Model
                  </label>
                  <input
                    type="text"
                    value={pricingModel}
                    onChange={(e) => setPricingModel(e.target.value)}
                    placeholder="e.g., Per-user subscription"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Key Products (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={keyProducts}
                    onChange={(e) => setKeyProducts(e.target.value)}
                    placeholder="e.g., Sales Cloud, Service Cloud, Marketing Cloud"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      resetForm();
                    }}
                    className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {submitting ? 'Adding...' : 'Add Competitor'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : competitors.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🏢</div>
            <h3 className="text-lg font-medium text-gray-900">
              No competitors yet
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Add competitors to build your competitive intelligence database.
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Add First Competitor
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {competitors.map((competitor) => (
              <CompetitorCard
                key={competitor.id}
                competitor={competitor}
                onDelete={() => handleDelete(competitor.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function CompetitorCard({
  competitor,
  onDelete,
}: {
  competitor: Competitor;
  onDelete: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-gray-900">
                {competitor.name}
              </h3>
              {competitor.win_rate_against !== null && competitor.win_rate_against !== undefined && (
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded ${
                    competitor.win_rate_against >= 50
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {competitor.win_rate_against}% win rate
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-gray-500">{competitor.description}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {competitor.key_products.slice(0, 4).map((product, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                >
                  {product}
                </span>
              ))}
              {competitor.key_products.length > 4 && (
                <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                  +{competitor.key_products.length - 4} more
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <span className="text-gray-400">{expanded ? '▲' : '▼'}</span>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Details
              </h4>
              <dl className="space-y-1 text-sm">
                <div className="flex gap-2">
                  <dt className="text-gray-500">Target Market:</dt>
                  <dd className="text-gray-900">{competitor.target_market}</dd>
                </div>
                {competitor.pricing_model && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500">Pricing:</dt>
                    <dd className="text-gray-900">{competitor.pricing_model}</dd>
                  </div>
                )}
                {competitor.website && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500">Website:</dt>
                    <dd>
                      <a
                        href={competitor.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {competitor.website}
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            <div>
              {competitor.strengths.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Strengths
                  </h4>
                  <ul className="space-y-1">
                    {competitor.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-gray-600">
                        • <strong>{s.area}:</strong> {s.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {competitor.weaknesses.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Weaknesses
                  </h4>
                  <ul className="space-y-1">
                    {competitor.weaknesses.map((w, i) => (
                      <li key={i} className="text-sm text-gray-600">
                        • <strong>{w.area}:</strong> {w.description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {competitor.common_objections.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Common Objections
              </h4>
              <div className="flex flex-wrap gap-2">
                {competitor.common_objections.map((obj, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded"
                  >
                    "{obj}"
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
