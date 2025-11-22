'use client';

/**
 * Public Deal Room Viewer
 *
 * Mobile-friendly viewer for prospects to access deal room content.
 * Features:
 * - Branded experience (colors, logo)
 * - Content browsing
 * - Action plan view
 * - Analytics tracking
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import {
  publicRoomApi,
  PublicDealRoom,
  PublicSection,
  PublicContent,
  PublicActionPlanItem,
} from '@/lib/api/dealroom';

export default function PublicDealRoomPage() {
  const params = useParams();
  const slug = params.room_slug as string;

  const [dealRoom, setDealRoom] = useState<PublicDealRoom | null>(null);
  const [requiresAuth, setRequiresAuth] = useState(false);
  const [authRequirements, setAuthRequirements] = useState<Record<string, boolean>>({});
  const [roomPreview, setRoomPreview] = useState<{ title: string; prospect_company?: string; branding: any } | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Auth state
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);

  // Tracking
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [viewEventId, setViewEventId] = useState<string | null>(null);
  const sessionStartTime = useRef<number>(Date.now());

  // Selected content
  const [selectedContent, setSelectedContent] = useState<PublicContent | null>(null);

  // Fetch deal room
  useEffect(() => {
    async function fetchRoom() {
      try {
        setLoading(true);
        const response = await publicRoomApi.get(slug);

        if ('requires_auth' in response && response.requires_auth) {
          setRequiresAuth(true);
          setAuthRequirements(response.auth_requirements);
          setRoomPreview({
            title: (response as any).title,
            prospect_company: (response as any).prospect_company,
            branding: (response as any).branding,
          });
        } else {
          setDealRoom(response as PublicDealRoom);
          // Track view
          trackView();
        }
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load deal room');
      } finally {
        setLoading(false);
      }
    }

    fetchRoom();
  }, [slug]);

  // Track view
  const trackView = useCallback(async (viewerEmail?: string) => {
    try {
      const result = await publicRoomApi.trackView(slug, {
        viewer_email: viewerEmail,
      });
      setSessionId(result.session_id);
      setViewEventId(result.view_event_id);
    } catch (err) {
      console.error('Failed to track view:', err);
    }
  }, [slug]);

  // Update session time periodically
  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(() => {
      const timeSpent = Math.floor((Date.now() - sessionStartTime.current) / 1000);
      publicRoomApi.updateSessionTime(slug, sessionId, timeSpent).catch(console.error);
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [sessionId, slug]);

  // Track content view
  const handleContentClick = async (content: PublicContent) => {
    setSelectedContent(content);

    if (viewEventId) {
      publicRoomApi.trackContentView(slug, {
        content_id: content.id,
        view_event_id: viewEventId,
        time_spent_seconds: 0,
      }).catch(console.error);
    }
  };

  // Handle auth
  const handleVerifyAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);

    try {
      const response = await publicRoomApi.verifyAccess(slug, {
        password: password || undefined,
        email: email || undefined,
      });

      if (response.granted) {
        // Refetch the room
        const room = await publicRoomApi.get(slug) as PublicDealRoom;
        setDealRoom(room);
        setRequiresAuth(false);
        trackView(email);
      } else {
        setAuthError(response.message || 'Access denied');
      }
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Verification failed');
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
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
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className="mt-2 text-lg font-semibold text-gray-900">Unable to load</h2>
          <p className="mt-1 text-sm text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  // Auth required
  if (requiresAuth) {
    return (
      <AuthGate
        title={roomPreview?.title || 'Deal Room'}
        branding={roomPreview?.branding}
        requirements={authRequirements}
        email={email}
        password={password}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSubmit={handleVerifyAccess}
        error={authError}
      />
    );
  }

  // Main viewer
  if (!dealRoom) return null;

  const primaryColor = dealRoom.branding.primary_color || '#0066FF';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Custom styles */}
      <style jsx global>{`
        .deal-room-accent {
          color: ${primaryColor};
        }
        .deal-room-accent-bg {
          background-color: ${primaryColor};
        }
        .deal-room-accent-border {
          border-color: ${primaryColor};
        }
      `}</style>

      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {dealRoom.branding.logo_url && (
                <img
                  src={dealRoom.branding.logo_url}
                  alt="Logo"
                  className="h-8 w-auto"
                />
              )}
              <div>
                <h1 className="text-lg font-bold text-gray-900">{dealRoom.title}</h1>
                {dealRoom.prospect_company && (
                  <p className="text-sm text-gray-500">For {dealRoom.prospect_company}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* Description */}
        {dealRoom.description && (
          <div className="mb-6">
            <p className="text-gray-600">{dealRoom.description}</p>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Content Sections */}
          <div className="lg:col-span-2 space-y-6">
            {dealRoom.sections.map((section) => (
              <SectionCard
                key={section.id}
                section={section}
                onContentClick={handleContentClick}
                primaryColor={primaryColor}
              />
            ))}

            {dealRoom.sections.length === 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
                <p className="text-gray-500">No content available</p>
              </div>
            )}
          </div>

          {/* Sidebar - Action Plan */}
          {dealRoom.show_action_plan && dealRoom.action_plan.length > 0 && (
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-20">
                <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                    />
                  </svg>
                  Mutual Action Plan
                </h3>

                <div className="space-y-3">
                  {dealRoom.action_plan.map((item) => (
                    <ActionPlanItemCard key={item.id} item={item} />
                  ))}
                </div>

                {/* Progress */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Progress</span>
                    <span>
                      {dealRoom.action_plan.filter((i) => i.status === 'completed').length} of{' '}
                      {dealRoom.action_plan.length}
                    </span>
                  </div>
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className="deal-room-accent-bg rounded-full h-2 transition-all"
                      style={{
                        width: `${
                          (dealRoom.action_plan.filter((i) => i.status === 'completed').length /
                            dealRoom.action_plan.length) *
                          100
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Content Viewer Modal */}
      {selectedContent && (
        <ContentViewerModal
          content={selectedContent}
          onClose={() => setSelectedContent(null)}
          primaryColor={primaryColor}
        />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-5xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          Powered by Sales OS
        </div>
      </footer>
    </div>
  );
}

// =============================================================================
// Auth Gate Component
// =============================================================================

function AuthGate({
  title,
  branding,
  requirements,
  email,
  password,
  onEmailChange,
  onPasswordChange,
  onSubmit,
  error,
}: {
  title: string;
  branding?: any;
  requirements: Record<string, boolean>;
  email: string;
  password: string;
  onEmailChange: (v: string) => void;
  onPasswordChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  error: string | null;
}) {
  const primaryColor = branding?.primary_color || '#0066FF';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Logo */}
          {branding?.logo_url && (
            <div className="flex justify-center mb-6">
              <img src={branding.logo_url} alt="Logo" className="h-10 w-auto" />
            </div>
          )}

          <h1 className="text-xl font-bold text-gray-900 text-center mb-2">{title}</h1>
          <p className="text-sm text-gray-500 text-center mb-6">
            {requirements.requires_password
              ? 'Enter the password to access this deal room'
              : requirements.requires_email
              ? 'Enter your email to access this deal room'
              : 'You need an invitation to access this deal room'}
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            {requirements.requires_email && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => onEmailChange(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="you@company.com"
                />
              </div>
            )}

            {requirements.requires_password && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => onPasswordChange(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter password"
                />
              </div>
            )}

            {error && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</div>
            )}

            <button
              type="submit"
              style={{ backgroundColor: primaryColor }}
              className="w-full py-2 px-4 text-white font-medium rounded-lg hover:opacity-90 transition-opacity"
            >
              Access Deal Room
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Section Card Component
// =============================================================================

function SectionCard({
  section,
  onContentClick,
  primaryColor,
}: {
  section: PublicSection;
  onContentClick: (content: PublicContent) => void;
  primaryColor: string;
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Section Header */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          {section.icon && (
            <span className="text-gray-400">{section.icon}</span>
          )}
          <h3 className="font-semibold text-gray-900">{section.name}</h3>
          <span className="text-xs text-gray-400">({section.contents.length})</span>
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${isCollapsed ? '' : 'rotate-180'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Section Content */}
      {!isCollapsed && (
        <div className="px-4 pb-4">
          {section.description && (
            <p className="text-sm text-gray-500 mb-3">{section.description}</p>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            {section.contents.map((content) => (
              <ContentCard
                key={content.id}
                content={content}
                onClick={() => onContentClick(content)}
                primaryColor={primaryColor}
              />
            ))}
          </div>

          {/* Nested sections */}
          {section.children.length > 0 && (
            <div className="mt-4 ml-4 space-y-4">
              {section.children.map((child) => (
                <SectionCard
                  key={child.id}
                  section={child}
                  onContentClick={onContentClick}
                  primaryColor={primaryColor}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Content Card Component
// =============================================================================

function ContentCard({
  content,
  onClick,
  primaryColor,
}: {
  content: PublicContent;
  onClick: () => void;
  primaryColor: string;
}) {
  const typeLabels: Record<string, string> = {
    proposal: 'Proposal',
    deck: 'Deck',
    case_study: 'Case Study',
    pricing: 'Pricing',
    contract: 'Contract',
    video: 'Video',
    document: 'Document',
    link: 'Link',
  };

  const typeIcons: Record<string, string> = {
    proposal: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    deck: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    case_study: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    pricing: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    contract: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    video: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z',
    document: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    link: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1',
  };

  return (
    <button
      onClick={onClick}
      className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left w-full group"
    >
      {/* Thumbnail or Icon */}
      <div
        className="w-12 h-12 rounded flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: `${primaryColor}15` }}
      >
        {content.thumbnail_url ? (
          <img
            src={content.thumbnail_url}
            alt=""
            className="w-full h-full object-cover rounded"
          />
        ) : (
          <svg
            className="w-6 h-6"
            style={{ color: primaryColor }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d={typeIcons[content.content_type] || typeIcons.document}
            />
          </svg>
        )}
      </div>

      {/* Content Info */}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600">
          {content.title}
        </h4>
        <p className="text-xs text-gray-500 mt-0.5">
          {typeLabels[content.content_type] || 'Document'}
        </p>
        {content.description && (
          <p className="text-xs text-gray-400 mt-1 line-clamp-2">{content.description}</p>
        )}
      </div>

      {/* Featured badge */}
      {content.is_featured && (
        <span
          className="text-xs px-2 py-0.5 rounded-full"
          style={{ backgroundColor: `${primaryColor}15`, color: primaryColor }}
        >
          Featured
        </span>
      )}
    </button>
  );
}

// =============================================================================
// Action Plan Item Component
// =============================================================================

function ActionPlanItemCard({ item }: { item: PublicActionPlanItem }) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-600',
    in_progress: 'bg-blue-100 text-blue-600',
    completed: 'bg-green-100 text-green-600',
    blocked: 'bg-red-100 text-red-600',
  };

  return (
    <div
      className={`flex items-start gap-3 p-2 rounded ${
        item.status === 'completed' ? 'opacity-60' : ''
      }`}
    >
      <div
        className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
          statusColors[item.status]
        }`}
      >
        {item.status === 'completed' ? (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        ) : item.is_milestone ? (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M3 6a3 3 0 013-3h10a1 1 0 01.8 1.6L14.25 8l2.55 3.4A1 1 0 0116 13H6a1 1 0 00-1 1v3a1 1 0 11-2 0V6z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <div className="w-2 h-2 rounded-full bg-current"></div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p
          className={`text-sm ${
            item.status === 'completed' ? 'line-through text-gray-400' : 'text-gray-900'
          }`}
        >
          {item.title}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <span
            className={`text-xs px-1.5 py-0.5 rounded ${
              item.owner === 'seller'
                ? 'bg-blue-50 text-blue-600'
                : item.owner === 'buyer'
                ? 'bg-purple-50 text-purple-600'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {item.owner}
          </span>
          {item.due_date && (
            <span className="text-xs text-gray-400">
              {new Date(item.due_date).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Content Viewer Modal
// =============================================================================

function ContentViewerModal({
  content,
  onClose,
  primaryColor,
}: {
  content: PublicContent;
  onClose: () => void;
  primaryColor: string;
}) {
  const isExternal = content.content_type === 'link' || content.external_link;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose}></div>

      {/* Modal */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{content.title}</h3>
              {content.description && (
                <p className="text-sm text-gray-500 mt-1">{content.description}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-4 overflow-auto max-h-[calc(90vh-120px)]">
            {content.file_url ? (
              <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                {content.content_type === 'video' ? (
                  <video src={content.file_url} controls className="w-full h-full" />
                ) : content.file_url.endsWith('.pdf') ? (
                  <iframe
                    src={content.file_url}
                    className="w-full h-full min-h-[600px]"
                    title={content.title}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full py-12">
                    <svg
                      className="w-16 h-16 text-gray-400 mb-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                      />
                    </svg>
                    <a
                      href={content.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ backgroundColor: primaryColor }}
                      className="inline-flex items-center px-4 py-2 text-white rounded-lg hover:opacity-90"
                    >
                      <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Download
                    </a>
                  </div>
                )}
              </div>
            ) : content.external_link ? (
              <div className="text-center py-12">
                <svg
                  className="w-16 h-16 text-gray-400 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                <a
                  href={content.external_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ backgroundColor: primaryColor }}
                  className="inline-flex items-center px-4 py-2 text-white rounded-lg hover:opacity-90"
                >
                  Open Link
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">No preview available</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
