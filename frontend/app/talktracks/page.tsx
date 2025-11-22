'use client';

import { useState } from 'react';
import { TalkTrackGenerator } from '@/components/talktracks/TalkTrackGenerator';
import { TalkTrackLibrary } from '@/components/talktracks/TalkTrackLibrary';
import { TalkTrackViewer } from '@/components/talktracks/TalkTrackViewer';
import { TalkTrackPerformance } from '@/components/talktracks/TalkTrackPerformance';

type TabType = 'generate' | 'library' | 'performance';

export default function TalkTracksPage() {
  const [activeTab, setActiveTab] = useState<TabType>('generate');
  const [selectedTalkTrack, setSelectedTalkTrack] = useState<string | null>(null);

  const tabs = [
    { id: 'generate' as TabType, label: 'Generate', icon: '✨' },
    { id: 'library' as TabType, label: 'Library', icon: '📚' },
    { id: 'performance' as TabType, label: 'Performance', icon: '📊' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-2xl font-semibold text-gray-900">
              Talk Track Generator
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Generate WbD-aligned scripts for discovery calls, demos, objections, and more
            </p>
          </div>

          {/* Tabs */}
          <div className="flex space-x-8 border-b border-gray-200 -mb-px">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'generate' && (
          <TalkTrackGenerator
            onGenerated={(talkTrack) => {
              setSelectedTalkTrack(talkTrack.id);
              setActiveTab('library');
            }}
          />
        )}

        {activeTab === 'library' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <TalkTrackLibrary
                selectedId={selectedTalkTrack}
                onSelect={setSelectedTalkTrack}
              />
            </div>
            <div className="lg:col-span-2">
              {selectedTalkTrack ? (
                <TalkTrackViewer talkTrackId={selectedTalkTrack} />
              ) : (
                <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                  Select a talk track from the library to view it
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <TalkTrackPerformance />
        )}
      </main>
    </div>
  );
}
