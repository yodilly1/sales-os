'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  listBattlecards,
  listCompetitors,
  type Battlecard,
  type BattlecardType,
  type Competitor,
} from '@/lib/api/battlecards';

const BATTLECARD_TYPE_LABELS: Record<BattlecardType, string> = {
  competitive: 'Competitive',
  objection_handling: 'Objection Handling',
  feature_comparison: 'Feature Comparison',
  win_loss_analysis: 'Win/Loss Analysis',
};

const BATTLECARD_TYPE_ICONS: Record<BattlecardType, string> = {
  competitive: '⚔️',
  objection_handling: '💬',
  feature_comparison: '📊',
  win_loss_analysis: '📈',
};

export default function BattlecardsPage() {
  const [battlecards, setBattlecards] = useState<Battlecard[]>([]);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<BattlecardType | ''>('');
  const [view, setView] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    fetchData();
  }, [searchQuery, selectedType]);

  async function fetchData() {
    try {
      setLoading(true);
      const [battlecardsRes, competitorsRes] = await Promise.all([
        listBattlecards({
          query: searchQuery || undefined,
          type: selectedType || undefined,
        }),
        listCompetitors(),
      ]);

      if (battlecardsRes.success) {
        setBattlecards(battlecardsRes.battlecards);
      }
      if (competitorsRes.success) {
        setCompetitors(competitorsRes.competitors);
      }
    } catch (err) {
      setError('Failed to load battlecards');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const getCompetitorName = (id: string) => {
    const competitor = competitors.find((c) => c.id === id);
    return competitor?.name || 'Unknown';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Battlecards</h1>
              <p className="mt-1 text-sm text-gray-500">
                Competitive intelligence and sales enablement
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/battlecards/competitors"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Manage Competitors
              </Link>
              <Link
                href="/battlecards/new"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                + Create Battlecard
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search battlecards..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as BattlecardType | '')}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            {Object.entries(BATTLECARD_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
            <button
              onClick={() => setView('grid')}
              className={`px-3 py-2 ${view === 'grid' ? 'bg-gray-100' : 'bg-white'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setView('list')}
              className={`px-3 py-2 ${view === 'list' ? 'bg-gray-100' : 'bg-white'}`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchData}
              className="mt-4 text-blue-600 hover:underline"
            >
              Try again
            </button>
          </div>
        ) : battlecards.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-lg font-medium text-gray-900">No battlecards yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Create your first battlecard to help your sales team win more deals.
            </p>
            <Link
              href="/battlecards/new"
              className="mt-4 inline-block px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Create Battlecard
            </Link>
          </div>
        ) : view === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {battlecards.map((card) => (
              <BattlecardCard
                key={card.id}
                battlecard={card}
                getCompetitorName={getCompetitorName}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Views
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Updated
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {battlecards.map((card) => (
                  <tr key={card.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <Link
                        href={`/battlecards/${card.id}`}
                        className="text-blue-600 hover:underline font-medium"
                      >
                        {card.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1">
                        {BATTLECARD_TYPE_ICONS[card.type]}
                        {BATTLECARD_TYPE_LABELS[card.type]}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={card.status} />
                    </td>
                    <td className="px-6 py-4 text-gray-500">{card.view_count}</td>
                    <td className="px-6 py-4 text-gray-500">
                      {card.last_updated
                        ? new Date(card.last_updated).toLocaleDateString()
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

function BattlecardCard({
  battlecard,
  getCompetitorName,
}: {
  battlecard: Battlecard;
  getCompetitorName: (id: string) => string;
}) {
  return (
    <Link
      href={`/battlecards/${battlecard.id}`}
      className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow"
    >
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">
              {BATTLECARD_TYPE_ICONS[battlecard.type]}
            </span>
            <span className="text-xs font-medium text-gray-500 uppercase">
              {BATTLECARD_TYPE_LABELS[battlecard.type]}
            </span>
          </div>
          <StatusBadge status={battlecard.status} />
        </div>

        <h3 className="mt-3 text-lg font-semibold text-gray-900">
          {battlecard.title}
        </h3>

        {battlecard.description && (
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
            {battlecard.description}
          </p>
        )}

        {battlecard.competitor_ids.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {battlecard.competitor_ids.slice(0, 3).map((id) => (
              <span
                key={id}
                className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
              >
                {getCompetitorName(id)}
              </span>
            ))}
            {battlecard.competitor_ids.length > 3 && (
              <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                +{battlecard.competitor_ids.length - 3} more
              </span>
            )}
          </div>
        )}

        <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
          <span>v{battlecard.version}</span>
          <span>{battlecard.view_count} views</span>
        </div>
      </div>
    </Link>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-yellow-100 text-yellow-800',
    published: 'bg-green-100 text-green-800',
    archived: 'bg-gray-100 text-gray-800',
  };

  return (
    <span
      className={`inline-block px-2 py-1 text-xs font-medium rounded ${colors[status] || colors.draft}`}
    >
      {status}
    </span>
  );
}
