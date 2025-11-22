'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  generateBattlecard,
  listCompetitors,
  type BattlecardType,
  type BattlecardGenerateRequest,
  type Competitor,
} from '@/lib/api/battlecards';

const BATTLECARD_TYPES: { value: BattlecardType; label: string; description: string; icon: string }[] = [
  {
    value: 'competitive',
    label: 'Competitive Battlecard',
    description: 'Intelligence against a specific competitor',
    icon: '⚔️',
  },
  {
    value: 'objection_handling',
    label: 'Objection Handling',
    description: 'Responses to common sales objections',
    icon: '💬',
  },
  {
    value: 'feature_comparison',
    label: 'Feature Comparison',
    description: 'Side-by-side feature matrix',
    icon: '📊',
  },
  {
    value: 'win_loss_analysis',
    label: 'Win/Loss Analysis',
    description: 'Insights from deal outcomes',
    icon: '📈',
  },
];

const OBJECTION_CATEGORIES = [
  'price',
  'timing',
  'competition',
  'need',
  'authority',
];

const FEATURE_CATEGORIES = [
  'Core Functionality',
  'Integration & API',
  'Security & Compliance',
  'Support & Success',
  'Performance & Scalability',
];

export default function NewBattlecardPage() {
  const router = useRouter();
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [selectedType, setSelectedType] = useState<BattlecardType | null>(null);
  const [title, setTitle] = useState('');
  const [competitorId, setCompetitorId] = useState('');
  const [competitorName, setCompetitorName] = useState('');
  const [objectionContext, setObjectionContext] = useState('');
  const [selectedObjectionCategories, setSelectedObjectionCategories] = useState<string[]>([]);
  const [selectedCompetitors, setSelectedCompetitors] = useState<string[]>([]);
  const [selectedFeatureCategories, setSelectedFeatureCategories] = useState<string[]>([]);
  const [analysisPeriod, setAnalysisPeriod] = useState(90);
  const [productContext, setProductContext] = useState('');
  const [additionalContext, setAdditionalContext] = useState('');
  const [autoPublish, setAutoPublish] = useState(false);

  useEffect(() => {
    loadCompetitors();
  }, []);

  async function loadCompetitors() {
    try {
      setLoading(true);
      const response = await listCompetitors();
      if (response.success) {
        setCompetitors(response.competitors);
      }
    } catch (err) {
      console.error('Failed to load competitors:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    if (!selectedType || !title) {
      setError('Please select a type and enter a title');
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      const request: BattlecardGenerateRequest = {
        type: selectedType,
        title,
        auto_publish: autoPublish,
      };

      // Add type-specific fields
      if (selectedType === 'competitive') {
        if (competitorId) {
          request.competitor_id = competitorId;
        } else if (competitorName) {
          request.competitor_name = competitorName;
        }
      }

      if (selectedType === 'objection_handling') {
        if (objectionContext) request.objection_context = objectionContext;
        if (selectedObjectionCategories.length > 0) {
          request.objection_categories = selectedObjectionCategories;
        }
      }

      if (selectedType === 'feature_comparison') {
        if (selectedCompetitors.length > 0) {
          request.competitors_to_compare = selectedCompetitors;
        }
        if (selectedFeatureCategories.length > 0) {
          request.feature_categories = selectedFeatureCategories;
        }
      }

      if (selectedType === 'win_loss_analysis') {
        request.analysis_period_days = analysisPeriod;
      }

      if (productContext) request.product_context = productContext;
      if (additionalContext) request.additional_context = additionalContext;

      const response = await generateBattlecard(request);

      if (response.success && response.battlecard) {
        router.push(`/battlecards/${response.battlecard.id}`);
      } else {
        setError(response.message || 'Failed to generate battlecard');
      }
    } catch (err) {
      setError('An error occurred while generating the battlecard');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  }

  function toggleObjectionCategory(category: string) {
    setSelectedObjectionCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  }

  function toggleCompetitor(name: string) {
    setSelectedCompetitors((prev) =>
      prev.includes(name) ? prev.filter((c) => c !== name) : [...prev, name]
    );
  }

  function toggleFeatureCategory(category: string) {
    setSelectedFeatureCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <Link
              href="/battlecards"
              className="text-gray-500 hover:text-gray-700"
            >
              ← Back
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Create Battlecard
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Generate AI-powered competitive intelligence
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Step 1: Select Type */}
        <section className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            1. Select Battlecard Type
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {BATTLECARD_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => setSelectedType(type.value)}
                className={`p-4 border-2 rounded-lg text-left transition-colors ${
                  selectedType === type.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{type.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900">{type.label}</div>
                    <div className="text-sm text-gray-500">{type.description}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* Step 2: Basic Info */}
        {selectedType && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              2. Basic Information
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Salesforce Competitive Battlecard"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product Context
                </label>
                <input
                  type="text"
                  value={productContext}
                  onChange={(e) => setProductContext(e.target.value)}
                  placeholder="e.g., Enterprise Sales Platform"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </section>
        )}

        {/* Step 3: Type-specific options */}
        {selectedType === 'competitive' && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              3. Select Competitor
            </h2>
            {competitors.length > 0 ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Choose from database
                  </label>
                  <select
                    value={competitorId}
                    onChange={(e) => {
                      setCompetitorId(e.target.value);
                      setCompetitorName('');
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a competitor...</option>
                    {competitors.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="text-center text-gray-500">or</div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Enter competitor name
                  </label>
                  <input
                    type="text"
                    value={competitorName}
                    onChange={(e) => {
                      setCompetitorName(e.target.value);
                      setCompetitorId('');
                    }}
                    placeholder="e.g., Competitor Inc."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Competitor Name
                </label>
                <input
                  type="text"
                  value={competitorName}
                  onChange={(e) => setCompetitorName(e.target.value)}
                  placeholder="e.g., Salesforce"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
          </section>
        )}

        {selectedType === 'objection_handling' && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              3. Objection Settings
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Context
                </label>
                <input
                  type="text"
                  value={objectionContext}
                  onChange={(e) => setObjectionContext(e.target.value)}
                  placeholder="e.g., Enterprise software sales"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Categories to Include
                </label>
                <div className="flex flex-wrap gap-2">
                  {OBJECTION_CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => toggleObjectionCategory(cat)}
                      className={`px-3 py-1 rounded-full text-sm capitalize ${
                        selectedObjectionCategories.includes(cat)
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {selectedType === 'feature_comparison' && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              3. Comparison Settings
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Competitors to Compare
                </label>
                {competitors.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {competitors.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => toggleCompetitor(c.name)}
                        className={`px-3 py-1 rounded-full text-sm ${
                          selectedCompetitors.includes(c.name)
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {c.name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    No competitors in database. Default competitors will be used.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Feature Categories
                </label>
                <div className="flex flex-wrap gap-2">
                  {FEATURE_CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => toggleFeatureCategory(cat)}
                      className={`px-3 py-1 rounded-full text-sm ${
                        selectedFeatureCategories.includes(cat)
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {selectedType === 'win_loss_analysis' && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              3. Analysis Settings
            </h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Analysis Period (days)
              </label>
              <select
                value={analysisPeriod}
                onChange={(e) => setAnalysisPeriod(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value={30}>Last 30 days</option>
                <option value={60}>Last 60 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last year</option>
              </select>
            </div>
          </section>
        )}

        {/* Step 4: Additional Context */}
        {selectedType && (
          <section className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              4. Additional Context (Optional)
            </h2>
            <textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Any additional context or instructions for generating the battlecard..."
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />

            <div className="mt-4 flex items-center">
              <input
                type="checkbox"
                id="autoPublish"
                checked={autoPublish}
                onChange={(e) => setAutoPublish(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="autoPublish" className="ml-2 text-sm text-gray-700">
                Publish immediately (otherwise saved as draft)
              </label>
            </div>
          </section>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Generate button */}
        {selectedType && (
          <div className="flex justify-end gap-4">
            <Link
              href="/battlecards"
              className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </Link>
            <button
              onClick={handleGenerate}
              disabled={generating || !title}
              className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generating ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  Generating...
                </span>
              ) : (
                'Generate Battlecard'
              )}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
