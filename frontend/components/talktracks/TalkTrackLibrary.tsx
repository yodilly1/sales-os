'use client';

import { useState, useEffect } from 'react';
import { getTalkTrackLibrary } from '@/lib/api/talktracks';
import type { TalkTrackLibraryItem } from '@/lib/api/talktracks';

interface TalkTrackLibraryProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const SCRIPT_TYPE_LABELS: Record<string, string> = {
  discovery_call: 'Discovery',
  demo_script: 'Demo',
  objection_response: 'Objection',
  closing_conversation: 'Closing',
  follow_up_guide: 'Follow-Up',
};

const SCRIPT_TYPE_COLORS: Record<string, string> = {
  discovery_call: 'bg-blue-100 text-blue-800',
  demo_script: 'bg-purple-100 text-purple-800',
  objection_response: 'bg-orange-100 text-orange-800',
  closing_conversation: 'bg-green-100 text-green-800',
  follow_up_guide: 'bg-gray-100 text-gray-800',
};

export function TalkTrackLibrary({ selectedId, onSelect }: TalkTrackLibraryProps) {
  const [items, setItems] = useState<TalkTrackLibraryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    script_type: '',
    persona: '',
    industry: '',
  });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadLibrary();
  }, [filters]);

  const loadLibrary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getTalkTrackLibrary({
        script_type: filters.script_type || undefined,
        persona: filters.persona || undefined,
        industry: filters.industry || undefined,
      });
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load library');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredItems = items.filter((item) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(query) ||
      item.script_type.toLowerCase().includes(query) ||
      item.persona.toLowerCase().includes(query) ||
      item.industry.toLowerCase().includes(query)
    );
  });

  const renderStars = (rating: number | null) => {
    if (rating === null) return <span className="text-gray-400">No ratings</span>;
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} className={i <= rating ? 'text-yellow-400' : 'text-gray-300'}>
          ★
        </span>
      );
    }
    return <span className="text-sm">{stars}</span>;
  };

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Talk Track Library</h2>

        {/* Search */}
        <div className="mt-3">
          <input
            type="text"
            placeholder="Search talk tracks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          />
        </div>

        {/* Filters */}
        <div className="mt-3 grid grid-cols-3 gap-2">
          <select
            value={filters.script_type}
            onChange={(e) => setFilters((f) => ({ ...f, script_type: e.target.value }))}
            className="text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="discovery_call">Discovery</option>
            <option value="demo_script">Demo</option>
            <option value="objection_response">Objection</option>
            <option value="closing_conversation">Closing</option>
            <option value="follow_up_guide">Follow-Up</option>
          </select>

          <select
            value={filters.persona}
            onChange={(e) => setFilters((f) => ({ ...f, persona: e.target.value }))}
            className="text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Personas</option>
            <option value="executive">Executive</option>
            <option value="technical">Technical</option>
            <option value="financial">Financial</option>
            <option value="operations">Operations</option>
            <option value="champion">Champion</option>
          </select>

          <select
            value={filters.industry}
            onChange={(e) => setFilters((f) => ({ ...f, industry: e.target.value }))}
            className="text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Industries</option>
            <option value="technology">Technology</option>
            <option value="healthcare">Healthcare</option>
            <option value="financial_services">Financial</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="retail">Retail</option>
          </select>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
            Loading...
          </div>
        ) : error ? (
          <div className="p-4 text-center text-red-500">{error}</div>
        ) : filteredItems.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No talk tracks found</p>
            <p className="text-sm mt-1">Generate your first talk track to get started</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {filteredItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => onSelect(item.id)}
                  className={`
                    w-full text-left p-4 hover:bg-gray-50 transition-colors
                    ${selectedId === item.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
                  `}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.title}
                      </p>
                      <div className="mt-1 flex items-center gap-2">
                        <span className={`
                          inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                          ${SCRIPT_TYPE_COLORS[item.script_type] || 'bg-gray-100 text-gray-800'}
                        `}>
                          {SCRIPT_TYPE_LABELS[item.script_type] || item.script_type}
                        </span>
                        <span className="text-xs text-gray-500">
                          {item.persona.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4 flex flex-col items-end">
                      {renderStars(item.average_rating)}
                      <span className="text-xs text-gray-400 mt-1">
                        {item.total_uses} uses
                      </span>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-500 text-center">
          {filteredItems.length} talk track{filteredItems.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
}
