'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  getBattlecard,
  deleteBattlecard,
  toggleFavorite,
  exportBattlecard,
  type Battlecard,
  type BattlecardType,
} from '@/lib/api/battlecards';

const BATTLECARD_TYPE_LABELS: Record<BattlecardType, string> = {
  competitive: 'Competitive',
  objection_handling: 'Objection Handling',
  feature_comparison: 'Feature Comparison',
  win_loss_analysis: 'Win/Loss Analysis',
};

export default function BattlecardDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [battlecard, setBattlecard] = useState<Battlecard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const userId = 'user-1'; // In production, get from auth context

  useEffect(() => {
    if (params.id) {
      loadBattlecard(params.id as string);
    }
  }, [params.id]);

  async function loadBattlecard(id: string) {
    try {
      setLoading(true);
      const response = await getBattlecard(id);
      if (response.success && response.battlecard) {
        setBattlecard(response.battlecard);
      } else {
        setError('Battlecard not found');
      }
    } catch (err) {
      setError('Failed to load battlecard');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!battlecard || !confirm('Are you sure you want to delete this battlecard?')) {
      return;
    }

    try {
      await deleteBattlecard(battlecard.id);
      router.push('/battlecards');
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  }

  async function handleToggleFavorite() {
    if (!battlecard) return;

    try {
      const response = await toggleFavorite(battlecard.id, userId);
      if (response.success && response.battlecard) {
        setBattlecard(response.battlecard);
      }
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  }

  async function handleExport(format: 'markdown' | 'html' | 'json') {
    if (!battlecard) return;

    try {
      setExporting(true);
      const response = await exportBattlecard(battlecard.id, format);
      if (response.success && response.data) {
        // Create download
        const blob = new Blob([typeof response.data === 'string' ? response.data : JSON.stringify(response.data, null, 2)], {
          type: format === 'json' ? 'application/json' : 'text/plain',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${battlecard.title}.${format === 'markdown' ? 'md' : format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to export:', err);
    } finally {
      setExporting(false);
    }
  }

  const isFavorited = battlecard?.favorited_by.includes(userId);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !battlecard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Battlecard not found'}</p>
          <Link href="/battlecards" className="text-blue-600 hover:underline">
            Back to Battlecards
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/battlecards"
                className="text-gray-500 hover:text-gray-700"
              >
                ← Back
              </Link>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-500 uppercase">
                    {BATTLECARD_TYPE_LABELS[battlecard.type]}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-xs font-medium rounded ${
                      battlecard.status === 'published'
                        ? 'bg-green-100 text-green-800'
                        : battlecard.status === 'draft'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {battlecard.status}
                  </span>
                </div>
                <h1 className="text-xl font-bold text-gray-900">
                  {battlecard.title}
                </h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleToggleFavorite}
                className={`p-2 rounded-lg ${
                  isFavorited
                    ? 'text-yellow-500 bg-yellow-50'
                    : 'text-gray-400 hover:bg-gray-100'
                }`}
              >
                {isFavorited ? '★' : '☆'}
              </button>
              <div className="relative group">
                <button
                  className="px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={exporting}
                >
                  {exporting ? 'Exporting...' : 'Export'}
                </button>
                <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                  <button
                    onClick={() => handleExport('markdown')}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Markdown
                  </button>
                  <button
                    onClick={() => handleExport('html')}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    HTML
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    JSON
                  </button>
                </div>
              </div>
              <button
                onClick={handleDelete}
                className="px-3 py-2 text-sm text-red-600 bg-white border border-gray-300 rounded-lg hover:bg-red-50"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Meta info */}
        <div className="mb-6 flex items-center gap-4 text-sm text-gray-500">
          <span>Version {battlecard.version}</span>
          <span>•</span>
          <span>{battlecard.view_count} views</span>
          {battlecard.last_updated && (
            <>
              <span>•</span>
              <span>
                Updated {new Date(battlecard.last_updated).toLocaleDateString()}
              </span>
            </>
          )}
        </div>

        {/* Render content based on type */}
        {battlecard.type === 'competitive' && battlecard.content.competitive && (
          <CompetitiveBattlecardView content={battlecard.content.competitive} />
        )}

        {battlecard.type === 'objection_handling' &&
          battlecard.content.objection_handling && (
            <ObjectionHandlingView content={battlecard.content.objection_handling} />
          )}

        {battlecard.type === 'feature_comparison' &&
          battlecard.content.feature_comparison && (
            <FeatureComparisonView content={battlecard.content.feature_comparison} />
          )}

        {battlecard.type === 'win_loss_analysis' &&
          battlecard.content.win_loss_analysis && (
            <WinLossAnalysisView content={battlecard.content.win_loss_analysis} />
          )}
      </main>
    </div>
  );
}

// Content Components

function CompetitiveBattlecardView({
  content,
}: {
  content: NonNullable<Battlecard['content']['competitive']>;
}) {
  return (
    <div className="space-y-6">
      {/* Overview */}
      <Section title={`vs. ${content.competitor_name}`}>
        <p className="text-gray-700">{content.competitor_overview}</p>
      </Section>

      {/* Positioning */}
      <Section title="Our Positioning">
        <p className="text-gray-700">{content.our_positioning}</p>
      </Section>

      {/* Key Differentiators */}
      <Section title="Key Differentiators">
        <ul className="list-disc list-inside space-y-1">
          {content.key_differentiators.map((d, i) => (
            <li key={i} className="text-gray-700">
              {d}
            </li>
          ))}
        </ul>
      </Section>

      {/* Strengths & Weaknesses Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <Section title="Competitor Strengths" className="bg-red-50">
          <div className="space-y-3">
            {content.competitor_strengths.map((s, i) => (
              <div key={i} className="border-l-4 border-red-400 pl-3">
                <div className="font-medium text-gray-900">{s.area}</div>
                <div className="text-sm text-gray-600">{s.description}</div>
                <div className="text-sm text-red-600 mt-1">
                  Impact: {s.impact}
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Competitor Weaknesses" className="bg-green-50">
          <div className="space-y-3">
            {content.competitor_weaknesses.map((w, i) => (
              <div key={i} className="border-l-4 border-green-400 pl-3">
                <div className="font-medium text-gray-900">{w.area}</div>
                <div className="text-sm text-gray-600">{w.description}</div>
                <div className="text-sm text-green-600 mt-1">
                  Talking point: {w.talking_point}
                </div>
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* Talking Points */}
      <Section title="Talking Points">
        <div className="space-y-3">
          {content.talking_points.map((tp, i) => (
            <div key={i} className="bg-blue-50 p-3 rounded-lg">
              <div className="text-xs font-medium text-blue-600 uppercase mb-1">
                {tp.category}
              </div>
              <div className="text-gray-900">{tp.point}</div>
              {tp.supporting_evidence && (
                <div className="text-sm text-gray-500 mt-1">
                  Evidence: {tp.supporting_evidence}
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* Landmines */}
      <Section title="Landmine Questions">
        <ul className="space-y-2">
          {content.landmines.map((l, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-orange-500">💣</span>
              <span className="text-gray-700">{l}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* When We Win/Lose */}
      <div className="grid md:grid-cols-2 gap-6">
        <Section title="When We Win" className="bg-green-50">
          <ul className="space-y-2">
            {content.when_we_win.map((w, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span className="text-gray-700">{w}</span>
              </li>
            ))}
          </ul>
        </Section>

        <Section title="When We Lose" className="bg-red-50">
          <ul className="space-y-2">
            {content.when_we_lose.map((l, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-red-500">✗</span>
                <span className="text-gray-700">{l}</span>
              </li>
            ))}
          </ul>
        </Section>
      </div>
    </div>
  );
}

function ObjectionHandlingView({
  content,
}: {
  content: NonNullable<Battlecard['content']['objection_handling']>;
}) {
  return (
    <div className="space-y-6">
      <Section title={`Context: ${content.context}`}>
        <p className="text-gray-500">
          Objection handling responses for {content.context}
        </p>
      </Section>

      {/* Objections */}
      <div className="space-y-6">
        {content.objections.map((obj, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">"{obj.objection}"</h3>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-700 rounded capitalize">
                    {obj.category}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-xs rounded ${
                      obj.severity === 'high'
                        ? 'bg-red-100 text-red-700'
                        : obj.severity === 'medium'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-green-100 text-green-700'
                    }`}
                  >
                    {obj.severity}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Root cause: {obj.root_cause}
              </p>
            </div>
            <div className="p-4 space-y-4">
              <ResponseStep label="Acknowledge" color="blue">
                {obj.response.acknowledge}
              </ResponseStep>
              <ResponseStep label="Clarify" color="purple">
                {obj.response.clarify}
              </ResponseStep>
              <ResponseStep label="Respond" color="green">
                {obj.response.respond}
              </ResponseStep>
              {obj.response.proof && (
                <ResponseStep label="Proof" color="orange">
                  {obj.response.proof}
                </ResponseStep>
              )}
              <ResponseStep label="Redirect" color="indigo">
                {obj.response.redirect}
              </ResponseStep>

              {obj.success_rate && (
                <div className="mt-4 text-sm text-gray-500">
                  Success rate: {obj.success_rate}%
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* General Tips */}
      <Section title="General Tips">
        <ul className="space-y-2">
          {content.general_tips.map((tip, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-blue-500">💡</span>
              <span className="text-gray-700">{tip}</span>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

function FeatureComparisonView({
  content,
}: {
  content: NonNullable<Battlecard['content']['feature_comparison']>;
}) {
  return (
    <div className="space-y-6">
      <Section title={content.title}>
        <p className="text-gray-700">{content.summary}</p>
      </Section>

      {/* Key Advantages */}
      <Section title="Key Advantages" className="bg-green-50">
        <ul className="space-y-1">
          {content.key_advantages.map((adv, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-green-500">✓</span>
              <span className="text-gray-700">{adv}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Comparison Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Feature
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {content.our_product}
                </th>
                {content.competitors.map((comp) => (
                  <th
                    key={comp}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
                  >
                    {comp}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {content.comparisons.map((comp, i) => (
                <tr key={i}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">
                      {comp.feature_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {comp.feature_category}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <RatingBadge rating={comp.our_rating} />
                    <div className="text-sm text-gray-600 mt-1">
                      {comp.our_capability}
                    </div>
                  </td>
                  {content.competitors.map((competitor) => (
                    <td key={competitor} className="px-4 py-3">
                      <RatingBadge
                        rating={comp.competitor_ratings[competitor]}
                      />
                      <div className="text-sm text-gray-600 mt-1">
                        {comp.competitor_capabilities[competitor]}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Areas for Improvement */}
      {content.areas_for_improvement.length > 0 && (
        <Section title="Areas for Improvement" className="bg-yellow-50">
          <ul className="space-y-1">
            {content.areas_for_improvement.map((area, i) => (
              <li key={i} className="text-gray-700">
                • {area}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function WinLossAnalysisView({
  content,
}: {
  content: NonNullable<Battlecard['content']['win_loss_analysis']>;
}) {
  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Win Rate" value={`${content.win_rate.toFixed(1)}%`} />
        <StatCard label="Deals Analyzed" value={content.total_deals_analyzed.toString()} />
        <StatCard
          label="Avg Won Deal"
          value={content.avg_deal_size_won ? `$${(content.avg_deal_size_won / 1000).toFixed(0)}k` : '-'}
        />
        <StatCard
          label="Avg Sales Cycle (Won)"
          value={content.avg_sales_cycle_won ? `${content.avg_sales_cycle_won} days` : '-'}
        />
      </div>

      {/* Win/Loss Factors */}
      <div className="grid md:grid-cols-2 gap-6">
        <Section title="Top Win Factors" className="bg-green-50">
          <div className="space-y-3">
            {content.top_win_factors.map((f, i) => (
              <div key={i} className="border-l-4 border-green-400 pl-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-gray-900">{f.factor}</div>
                  <span
                    className={`px-2 py-0.5 text-xs rounded ${
                      f.impact === 'high'
                        ? 'bg-green-200 text-green-800'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {f.impact}
                  </span>
                </div>
                <div className="text-sm text-gray-600">{f.description}</div>
                {f.frequency && (
                  <div className="text-xs text-gray-500 mt-1">
                    Appeared in {f.frequency} deals
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>

        <Section title="Top Loss Factors" className="bg-red-50">
          <div className="space-y-3">
            {content.top_loss_factors.map((f, i) => (
              <div key={i} className="border-l-4 border-red-400 pl-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-gray-900">{f.factor}</div>
                  <span
                    className={`px-2 py-0.5 text-xs rounded ${
                      f.impact === 'high'
                        ? 'bg-red-200 text-red-800'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {f.impact}
                  </span>
                </div>
                <div className="text-sm text-gray-600">{f.description}</div>
                {f.frequency && (
                  <div className="text-xs text-gray-500 mt-1">
                    Appeared in {f.frequency} deals
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* Competitor Breakdown */}
      {Object.keys(content.competitor_breakdown).length > 0 && (
        <Section title="Win Rate by Competitor">
          <div className="space-y-2">
            {Object.entries(content.competitor_breakdown).map(([comp, rate]) => (
              <div key={comp} className="flex items-center gap-3">
                <div className="w-32 font-medium text-gray-700">{comp}</div>
                <div className="flex-1 bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-full ${rate >= 50 ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${rate}%` }}
                  />
                </div>
                <div className="w-12 text-right text-sm text-gray-600">
                  {rate}%
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Recommendations */}
      <Section title="Recommendations">
        <ul className="space-y-2">
          {content.recommendations.map((rec, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-blue-500">→</span>
              <span className="text-gray-700">{rec}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Notable Deals */}
      {content.notable_deals.length > 0 && (
        <Section title="Notable Deals">
          <div className="space-y-4">
            {content.notable_deals.map((deal, i) => (
              <div
                key={i}
                className={`p-4 rounded-lg border ${
                  deal.outcome === 'won'
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium text-gray-900">{deal.deal_name}</div>
                  <span
                    className={`px-2 py-0.5 text-xs font-medium rounded ${
                      deal.outcome === 'won'
                        ? 'bg-green-200 text-green-800'
                        : 'bg-red-200 text-red-800'
                    }`}
                  >
                    {deal.outcome}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {deal.competitor && <span>vs. {deal.competitor} • </span>}
                  {deal.deal_size && <span>${(deal.deal_size / 1000).toFixed(0)}k • </span>}
                  {deal.sales_cycle_days && <span>{deal.sales_cycle_days} days</span>}
                </div>
                <div className="mt-2 text-sm text-gray-700">
                  {deal.lessons_learned}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// Helper Components

function Section({
  title,
  children,
  className = '',
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-white rounded-lg shadow-sm p-6 ${className}`}>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
      {children}
    </div>
  );
}

function ResponseStep({
  label,
  color,
  children,
}: {
  label: string;
  color: string;
  children: React.ReactNode;
}) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    indigo: 'bg-indigo-100 text-indigo-800',
  };

  return (
    <div>
      <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded ${colors[color]}`}>
        {label}
      </span>
      <p className="mt-1 text-gray-700">{children}</p>
    </div>
  );
}

function RatingBadge({ rating }: { rating: string }) {
  const colors: Record<string, string> = {
    superior: 'bg-green-100 text-green-800',
    comparable: 'bg-yellow-100 text-yellow-800',
    inferior: 'bg-red-100 text-red-800',
    not_available: 'bg-gray-100 text-gray-800',
  };

  const labels: Record<string, string> = {
    superior: 'Superior',
    comparable: 'Comparable',
    inferior: 'Inferior',
    not_available: 'N/A',
  };

  return (
    <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded ${colors[rating] || colors.not_available}`}>
      {labels[rating] || rating}
    </span>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  );
}
