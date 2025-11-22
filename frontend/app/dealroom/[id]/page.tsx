'use client';

/**
 * Deal Room Editor Page
 *
 * Full editor for managing a single deal room with tabs for:
 * - Content management
 * - Action plan
 * - Settings & branding
 * - Analytics
 */

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  dealRoomApi,
  DealRoom,
  Section,
  Content,
  ActionPlanItem,
  AnalyticsSummary,
  EngagementScore,
} from '@/lib/api/dealroom';

type TabType = 'content' | 'action-plan' | 'settings' | 'analytics';

export default function DealRoomEditorPage() {
  const params = useParams();
  const router = useRouter();
  const dealRoomId = params.id as string;

  const [dealRoom, setDealRoom] = useState<DealRoom | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [contents, setContents] = useState<Content[]>([]);
  const [actionPlanItems, setActionPlanItems] = useState<ActionPlanItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [engagementScore, setEngagementScore] = useState<EngagementScore | null>(null);

  const [activeTab, setActiveTab] = useState<TabType>('content');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch deal room data
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [room, sectionList, contentList, actionPlan] = await Promise.all([
          dealRoomApi.get(dealRoomId),
          dealRoomApi.listSections(dealRoomId),
          dealRoomApi.listContents(dealRoomId),
          dealRoomApi.listActionPlanItems(dealRoomId),
        ]);
        setDealRoom(room);
        setSections(sectionList);
        setContents(contentList);
        setActionPlanItems(actionPlan);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load deal room');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [dealRoomId]);

  // Fetch analytics when tab changes
  useEffect(() => {
    if (activeTab === 'analytics' && !analytics) {
      Promise.all([
        dealRoomApi.getAnalytics(dealRoomId),
        dealRoomApi.getEngagementScore(dealRoomId),
      ]).then(([analyticsData, scoreData]) => {
        setAnalytics(analyticsData);
        setEngagementScore(scoreData);
      }).catch(console.error);
    }
  }, [activeTab, dealRoomId, analytics]);

  // Handle publish/archive
  const handlePublish = async () => {
    if (!dealRoom) return;
    try {
      setSaving(true);
      const updated = await dealRoomApi.publish(dealRoomId);
      setDealRoom(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish');
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!dealRoom) return;
    try {
      setSaving(true);
      const updated = await dealRoomApi.archive(dealRoomId);
      setDealRoom(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive');
    } finally {
      setSaving(false);
    }
  };

  // Handle settings update
  const handleUpdateSettings = async (updates: Partial<DealRoom>) => {
    try {
      setSaving(true);
      const updated = await dealRoomApi.update(dealRoomId, updates);
      setDealRoom(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  // Copy share link
  const copyShareLink = () => {
    if (dealRoom?.share_url) {
      navigator.clipboard.writeText(dealRoom.share_url);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!dealRoom) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-gray-900">Deal room not found</h2>
          <Link href="/dealroom" className="text-blue-600 hover:underline mt-2 block">
            Back to deal rooms
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            {/* Breadcrumb */}
            <div className="flex items-center text-sm text-gray-500 mb-2">
              <Link href="/dealroom" className="hover:text-gray-700">
                Deal Rooms
              </Link>
              <svg className="w-4 h-4 mx-2" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-gray-900">{dealRoom.title}</span>
            </div>

            {/* Title and Actions */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{dealRoom.title}</h1>
                <div className="flex items-center gap-3 mt-1">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      dealRoom.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : dealRoom.status === 'draft'
                        ? 'bg-gray-100 text-gray-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {dealRoom.status}
                  </span>
                  {dealRoom.prospect_company && (
                    <span className="text-sm text-gray-500">{dealRoom.prospect_company}</span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                {dealRoom.share_url && (
                  <button
                    onClick={copyShareLink}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                    Copy Link
                  </button>
                )}
                {dealRoom.share_url && (
                  <a
                    href={dealRoom.share_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                    Preview
                  </a>
                )}
                {dealRoom.status === 'draft' ? (
                  <button
                    onClick={handlePublish}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    Publish
                  </button>
                ) : dealRoom.status === 'active' ? (
                  <button
                    onClick={handleArchive}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Archive
                  </button>
                ) : null}
              </div>
            </div>

            {/* Tabs */}
            <div className="mt-4 border-b border-gray-200 -mb-px">
              <nav className="flex gap-8">
                {[
                  { id: 'content', label: 'Content', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
                  { id: 'action-plan', label: 'Action Plan', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
                  { id: 'settings', label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
                  { id: 'analytics', label: 'Analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as TabType)}
                    className={`flex items-center py-3 px-1 border-b-2 text-sm font-medium ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
                    </svg>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Tab Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'content' && (
          <ContentTab
            dealRoomId={dealRoomId}
            sections={sections}
            contents={contents}
            onSectionsChange={setSections}
            onContentsChange={setContents}
          />
        )}
        {activeTab === 'action-plan' && (
          <ActionPlanTab
            dealRoomId={dealRoomId}
            items={actionPlanItems}
            onItemsChange={setActionPlanItems}
          />
        )}
        {activeTab === 'settings' && (
          <SettingsTab
            dealRoom={dealRoom}
            onUpdate={handleUpdateSettings}
            saving={saving}
          />
        )}
        {activeTab === 'analytics' && (
          <AnalyticsTab
            dealRoomId={dealRoomId}
            analytics={analytics}
            engagementScore={engagementScore}
          />
        )}
      </main>
    </div>
  );
}

// =============================================================================
// Content Tab
// =============================================================================

function ContentTab({
  dealRoomId,
  sections,
  contents,
  onSectionsChange,
  onContentsChange,
}: {
  dealRoomId: string;
  sections: Section[];
  contents: Content[];
  onSectionsChange: (sections: Section[]) => void;
  onContentsChange: (contents: Content[]) => void;
}) {
  const [showAddContent, setShowAddContent] = useState(false);
  const [showAddSection, setShowAddSection] = useState(false);

  const handleAddContent = async (data: Partial<Content>) => {
    try {
      const newContent = await dealRoomApi.addContent(dealRoomId, data as any);
      onContentsChange([...contents, newContent]);
      setShowAddContent(false);
    } catch (error) {
      console.error('Failed to add content:', error);
    }
  };

  const handleDeleteContent = async (contentId: string) => {
    if (!confirm('Delete this content?')) return;
    try {
      await dealRoomApi.deleteContent(dealRoomId, contentId);
      onContentsChange(contents.filter((c) => c.id !== contentId));
    } catch (error) {
      console.error('Failed to delete content:', error);
    }
  };

  const handleAddSection = async (name: string) => {
    try {
      const newSection = await dealRoomApi.createSection(dealRoomId, { name });
      onSectionsChange([...sections, newSection]);
      setShowAddSection(false);
    } catch (error) {
      console.error('Failed to add section:', error);
    }
  };

  const contentTypeLabels: Record<string, string> = {
    proposal: 'Proposal',
    deck: 'Deck',
    case_study: 'Case Study',
    pricing: 'Pricing',
    contract: 'Contract',
    video: 'Video',
    document: 'Document',
    link: 'Link',
  };

  return (
    <div className="space-y-6">
      {/* Actions */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Content</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddSection(true)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
          >
            Add Section
          </button>
          <button
            onClick={() => setShowAddContent(true)}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700"
          >
            Add Content
          </button>
        </div>
      </div>

      {/* Sections and Content */}
      <div className="space-y-4">
        {/* Unsectioned content */}
        {contents.filter((c) => !c.section_id).length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Documents</h3>
            <div className="space-y-2">
              {contents
                .filter((c) => !c.section_id)
                .map((content) => (
                  <ContentItem
                    key={content.id}
                    content={content}
                    onDelete={() => handleDeleteContent(content.id)}
                  />
                ))}
            </div>
          </div>
        )}

        {/* Sectioned content */}
        {sections.map((section) => (
          <div key={section.id} className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">{section.name}</h3>
            <div className="space-y-2">
              {contents
                .filter((c) => c.section_id === section.id)
                .map((content) => (
                  <ContentItem
                    key={content.id}
                    content={content}
                    onDelete={() => handleDeleteContent(content.id)}
                  />
                ))}
              {contents.filter((c) => c.section_id === section.id).length === 0 && (
                <p className="text-sm text-gray-400 italic">No content in this section</p>
              )}
            </div>
          </div>
        ))}

        {/* Empty state */}
        {contents.length === 0 && sections.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No content yet</h3>
            <p className="mt-1 text-sm text-gray-500">Add proposals, decks, or other content.</p>
          </div>
        )}
      </div>

      {/* Add Content Modal */}
      {showAddContent && (
        <AddContentModal
          sections={sections}
          onClose={() => setShowAddContent(false)}
          onAdd={handleAddContent}
        />
      )}

      {/* Add Section Modal */}
      {showAddSection && (
        <AddSectionModal
          onClose={() => setShowAddSection(false)}
          onAdd={handleAddSection}
        />
      )}
    </div>
  );
}

function ContentItem({ content, onDelete }: { content: Content; onDelete: () => void }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
          <span className="text-blue-600 text-xs font-medium uppercase">
            {content.content_type.slice(0, 3)}
          </span>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-900">{content.title}</p>
          <p className="text-xs text-gray-500">
            {content.view_count} views | {content.download_count} downloads
          </p>
        </div>
      </div>
      <button onClick={onDelete} className="p-1 text-gray-400 hover:text-red-600">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

function AddContentModal({
  sections,
  onClose,
  onAdd,
}: {
  sections: Section[];
  onClose: () => void;
  onAdd: (data: Partial<Content>) => void;
}) {
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState<Content['content_type']>('document');
  const [sectionId, setSectionId] = useState('');
  const [externalLink, setExternalLink] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd({
      title,
      content_type: contentType,
      section_id: sectionId || undefined,
      external_link: externalLink || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Content</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={contentType}
                onChange={(e) => setContentType(e.target.value as Content['content_type'])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="proposal">Proposal</option>
                <option value="deck">Deck</option>
                <option value="case_study">Case Study</option>
                <option value="pricing">Pricing</option>
                <option value="contract">Contract</option>
                <option value="video">Video</option>
                <option value="document">Document</option>
                <option value="link">Link</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Section</label>
              <select
                value={sectionId}
                onChange={(e) => setSectionId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No section</option>
                {sections.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Link (optional)</label>
              <input
                type="url"
                value={externalLink}
                onChange={(e) => setExternalLink(e.target.value)}
                placeholder="https://..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700">
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                Add
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function AddSectionModal({
  onClose,
  onAdd,
}: {
  onClose: () => void;
  onAdd: (name: string) => void;
}) {
  const [name, setName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd(name);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Section</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Section name"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-end gap-3 mt-4">
              <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700">
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                Add
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Action Plan Tab
// =============================================================================

function ActionPlanTab({
  dealRoomId,
  items,
  onItemsChange,
}: {
  dealRoomId: string;
  items: ActionPlanItem[];
  onItemsChange: (items: ActionPlanItem[]) => void;
}) {
  const [newItemTitle, setNewItemTitle] = useState('');

  const handleAddItem = async () => {
    if (!newItemTitle.trim()) return;
    try {
      const newItem = await dealRoomApi.addActionPlanItem(dealRoomId, { title: newItemTitle });
      onItemsChange([...items, newItem]);
      setNewItemTitle('');
    } catch (error) {
      console.error('Failed to add item:', error);
    }
  };

  const handleUpdateStatus = async (itemId: string, status: ActionPlanItem['status']) => {
    try {
      const updated = await dealRoomApi.updateActionPlanItem(dealRoomId, itemId, { status });
      onItemsChange(items.map((i) => (i.id === itemId ? updated : i)));
    } catch (error) {
      console.error('Failed to update item:', error);
    }
  };

  const handleDelete = async (itemId: string) => {
    try {
      await dealRoomApi.deleteActionPlanItem(dealRoomId, itemId);
      onItemsChange(items.filter((i) => i.id !== itemId));
    } catch (error) {
      console.error('Failed to delete item:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Mutual Action Plan</h2>
      </div>

      {/* Add new item */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newItemTitle}
          onChange={(e) => setNewItemTitle(e.target.value)}
          placeholder="Add a new action item..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          onKeyDown={(e) => e.key === 'Enter' && handleAddItem()}
        />
        <button
          onClick={handleAddItem}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add
        </button>
      </div>

      {/* Items list */}
      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={item.id}
            className={`flex items-center gap-3 p-4 bg-white rounded-lg border ${
              item.status === 'completed' ? 'border-green-200 bg-green-50' : 'border-gray-200'
            }`}
          >
            <input
              type="checkbox"
              checked={item.status === 'completed'}
              onChange={() =>
                handleUpdateStatus(item.id, item.status === 'completed' ? 'pending' : 'completed')
              }
              className="w-5 h-5 text-blue-600 rounded"
            />
            <div className="flex-1">
              <p
                className={`font-medium ${
                  item.status === 'completed' ? 'line-through text-gray-400' : 'text-gray-900'
                }`}
              >
                {item.title}
              </p>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                <span
                  className={`px-2 py-0.5 rounded ${
                    item.owner === 'seller'
                      ? 'bg-blue-100 text-blue-700'
                      : item.owner === 'buyer'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {item.owner}
                </span>
                {item.due_date && <span>Due: {new Date(item.due_date).toLocaleDateString()}</span>}
              </div>
            </div>
            <button onClick={() => handleDelete(item.id)} className="p-1 text-gray-400 hover:text-red-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No action items yet. Add items to track deal progress.
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Settings Tab
// =============================================================================

function SettingsTab({
  dealRoom,
  onUpdate,
  saving,
}: {
  dealRoom: DealRoom;
  onUpdate: (updates: Partial<DealRoom>) => void;
  saving: boolean;
}) {
  const [formData, setFormData] = useState({
    title: dealRoom.title,
    description: dealRoom.description || '',
    prospect_company: dealRoom.prospect_company || '',
    prospect_name: dealRoom.prospect_name || '',
    prospect_email: dealRoom.prospect_email || '',
    primary_color: dealRoom.branding.primary_color,
    access_level: dealRoom.access_level,
    show_action_plan: dealRoom.settings.show_action_plan,
    notify_on_view: dealRoom.settings.notify_on_view,
  });

  const handleSave = () => {
    onUpdate({
      title: formData.title,
      description: formData.description || undefined,
      prospect_company: formData.prospect_company || undefined,
      prospect_name: formData.prospect_name || undefined,
      prospect_email: formData.prospect_email || undefined,
      branding: {
        ...dealRoom.branding,
        primary_color: formData.primary_color,
      },
      access_control: {
        access_level: formData.access_level,
      },
      settings: {
        ...dealRoom.settings,
        show_action_plan: formData.show_action_plan,
        notify_on_view: formData.notify_on_view,
      },
    });
  };

  return (
    <div className="space-y-8">
      {/* Basic Info */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Prospect Company</label>
            <input
              type="text"
              value={formData.prospect_company}
              onChange={(e) => setFormData({ ...formData, prospect_company: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
      </section>

      {/* Branding */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Branding</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="w-10 h-10 border border-gray-300 rounded cursor-pointer"
              />
              <input
                type="text"
                value={formData.primary_color}
                onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Access Control */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Access Control</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Access Level</label>
          <select
            value={formData.access_level}
            onChange={(e) => setFormData({ ...formData, access_level: e.target.value as any })}
            className="w-full sm:w-64 px-3 py-2 border border-gray-300 rounded-lg"
          >
            <option value="public">Public (anyone with link)</option>
            <option value="password">Password Protected</option>
            <option value="email_gate">Email Gated</option>
            <option value="invite_only">Invite Only</option>
          </select>
        </div>
      </section>

      {/* Settings */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Settings</h3>
        <div className="space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={formData.show_action_plan}
              onChange={(e) => setFormData({ ...formData, show_action_plan: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <span className="text-sm text-gray-700">Show action plan to viewers</span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={formData.notify_on_view}
              onChange={(e) => setFormData({ ...formData, notify_on_view: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <span className="text-sm text-gray-700">Notify me when someone views</span>
          </label>
        </div>
      </section>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// Analytics Tab
// =============================================================================

function AnalyticsTab({
  dealRoomId,
  analytics,
  engagementScore,
}: {
  dealRoomId: string;
  analytics: AnalyticsSummary | null;
  engagementScore: EngagementScore | null;
}) {
  if (!analytics) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Views</p>
          <p className="text-2xl font-bold text-gray-900">{analytics.total_views}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Unique Viewers</p>
          <p className="text-2xl font-bold text-gray-900">{analytics.unique_viewers}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Avg. Time</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatTime(Math.round(analytics.avg_time_per_visit_seconds))}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Engagement Score</p>
          <p className="text-2xl font-bold text-gray-900">
            {engagementScore?.overall_score || 0}
            <span className="text-sm font-normal text-gray-500">/100</span>
          </p>
        </div>
      </div>

      {/* Engagement Score Breakdown */}
      {engagementScore && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement Analysis</h3>
          <p className="text-sm text-gray-600 mb-4">{engagementScore.interpretation}</p>
          <div className="grid gap-4 sm:grid-cols-5">
            {Object.entries(engagementScore.breakdown).map(([key, value]) => (
              <div key={key}>
                <p className="text-xs text-gray-500 capitalize">{key.replace('_', ' ')}</p>
                <div className="mt-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 rounded-full h-2"
                    style={{ width: `${value}%` }}
                  ></div>
                </div>
                <p className="text-sm font-medium text-gray-900 mt-1">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Views */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Views</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2">Viewer</th>
                <th className="pb-2">Device</th>
                <th className="pb-2">Time Spent</th>
                <th className="pb-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {analytics.recent_views.map((view) => (
                <tr key={view.id} className="border-b last:border-0">
                  <td className="py-3">
                    {view.viewer_email || view.viewer_name || 'Anonymous'}
                  </td>
                  <td className="py-3">{view.device_type || 'Unknown'}</td>
                  <td className="py-3">{formatTime(view.time_spent_seconds)}</td>
                  <td className="py-3">{new Date(view.viewed_at).toLocaleString()}</td>
                </tr>
              ))}
              {analytics.recent_views.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-4 text-center text-gray-500">
                    No views yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Content */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Content</h3>
        <div className="space-y-3">
          {analytics.most_viewed_content.map((content, index) => (
            <div key={content.content_id} className="flex items-center gap-3">
              <span className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
                {index + 1}
              </span>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{content.content_title}</p>
                <p className="text-xs text-gray-500">
                  {content.view_count} views | {formatTime(content.total_time_spent)} total time
                </p>
              </div>
            </div>
          ))}
          {analytics.most_viewed_content.length === 0 && (
            <p className="text-center text-gray-500">No content viewed yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
