/**
 * Outreach Tracker Component
 *
 * Track and manage LinkedIn outreach activities.
 */

'use client';

import React, { useState } from 'react';
import type {
  OutreachActivity,
  OutreachType,
  OutreachStatus,
} from '@/lib/api/linkedin';

interface OutreachTrackerProps {
  activities: OutreachActivity[];
  onTrackNew?: (data: {
    prospectLinkedinUrl: string;
    outreachType: OutreachType;
    messageContent?: string;
    subject?: string;
  }) => Promise<void>;
  onUpdateStatus?: (
    activityId: string,
    status: OutreachStatus
  ) => Promise<void>;
  isLoading?: boolean;
}

const outreachTypeConfig: Record<
  OutreachType,
  { label: string; icon: React.ReactNode; color: string }
> = {
  connection_request: {
    label: 'Connection Request',
    icon: <UserPlusIcon className="w-4 h-4" />,
    color: 'bg-blue-100 text-blue-800',
  },
  inmail: {
    label: 'InMail',
    icon: <MailIcon className="w-4 h-4" />,
    color: 'bg-purple-100 text-purple-800',
  },
  message: {
    label: 'Message',
    icon: <ChatIcon className="w-4 h-4" />,
    color: 'bg-green-100 text-green-800',
  },
  comment: {
    label: 'Comment',
    icon: <CommentIcon className="w-4 h-4" />,
    color: 'bg-yellow-100 text-yellow-800',
  },
  like: {
    label: 'Like',
    icon: <HeartIcon className="w-4 h-4" />,
    color: 'bg-red-100 text-red-800',
  },
  share: {
    label: 'Share',
    icon: <ShareIcon className="w-4 h-4" />,
    color: 'bg-indigo-100 text-indigo-800',
  },
  profile_view: {
    label: 'Profile View',
    icon: <EyeIcon className="w-4 h-4" />,
    color: 'bg-gray-100 text-gray-800',
  },
};

const statusConfig: Record<OutreachStatus, { label: string; color: string }> = {
  pending: { label: 'Pending', color: 'bg-gray-200 text-gray-700' },
  sent: { label: 'Sent', color: 'bg-blue-100 text-blue-800' },
  delivered: { label: 'Delivered', color: 'bg-cyan-100 text-cyan-800' },
  read: { label: 'Read', color: 'bg-purple-100 text-purple-800' },
  replied: { label: 'Replied', color: 'bg-green-100 text-green-800' },
  accepted: { label: 'Accepted', color: 'bg-green-200 text-green-900' },
  declined: { label: 'Declined', color: 'bg-red-100 text-red-800' },
  expired: { label: 'Expired', color: 'bg-gray-300 text-gray-600' },
};

export function OutreachTracker({
  activities,
  onTrackNew,
  onUpdateStatus,
  isLoading,
}: OutreachTrackerProps) {
  const [showNewForm, setShowNewForm] = useState(false);
  const [formData, setFormData] = useState({
    prospectLinkedinUrl: '',
    outreachType: 'connection_request' as OutreachType,
    messageContent: '',
    subject: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (onTrackNew) {
      await onTrackNew(formData);
      setFormData({
        prospectLinkedinUrl: '',
        outreachType: 'connection_request',
        messageContent: '',
        subject: '',
      });
      setShowNewForm(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Outreach Activities</h3>
        {onTrackNew && (
          <button
            onClick={() => setShowNewForm(!showNewForm)}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showNewForm ? 'Cancel' : '+ Track Outreach'}
          </button>
        )}
      </div>

      {/* New Outreach Form */}
      {showNewForm && (
        <form onSubmit={handleSubmit} className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                LinkedIn URL
              </label>
              <input
                type="url"
                value={formData.prospectLinkedinUrl}
                onChange={(e) =>
                  setFormData({ ...formData, prospectLinkedinUrl: e.target.value })
                }
                placeholder="https://linkedin.com/in/username"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={formData.outreachType}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    outreachType: e.target.value as OutreachType,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {Object.entries(outreachTypeConfig).map(([value, { label }]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {formData.outreachType === 'inmail' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) =>
                    setFormData({ ...formData, subject: e.target.value })
                  }
                  placeholder="Subject line..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            {['connection_request', 'inmail', 'message', 'comment'].includes(
              formData.outreachType
            ) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message
                </label>
                <textarea
                  value={formData.messageContent}
                  onChange={(e) =>
                    setFormData({ ...formData, messageContent: e.target.value })
                  }
                  placeholder="Your message..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Tracking...' : 'Track Activity'}
            </button>
          </div>
        </form>
      )}

      {/* Activities List */}
      <div className="divide-y divide-gray-100">
        {activities.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <MailIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No outreach activities tracked yet</p>
          </div>
        ) : (
          activities.map((activity) => (
            <OutreachActivityItem
              key={activity.id}
              activity={activity}
              onUpdateStatus={onUpdateStatus}
              isLoading={isLoading}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ==================== Activity Item Component ====================

interface OutreachActivityItemProps {
  activity: OutreachActivity;
  onUpdateStatus?: (activityId: string, status: OutreachStatus) => Promise<void>;
  isLoading?: boolean;
}

function OutreachActivityItem({
  activity,
  onUpdateStatus,
  isLoading,
}: OutreachActivityItemProps) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const typeConfig = outreachTypeConfig[activity.outreach_type];
  const statusCfg = statusConfig[activity.status];

  const handleStatusUpdate = async (status: OutreachStatus) => {
    if (onUpdateStatus) {
      await onUpdateStatus(activity.id, status);
    }
    setShowStatusMenu(false);
  };

  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start gap-3">
        {/* Type Icon */}
        <div className={`p-2 rounded-lg ${typeConfig.color}`}>
          {typeConfig.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-gray-900">{typeConfig.label}</span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${statusCfg.color}`}>
              {statusCfg.label}
            </span>
            {activity.is_sales_navigator && (
              <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded-full">
                Sales Nav
              </span>
            )}
          </div>

          <a
            href={activity.prospect_linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:underline truncate block mt-1"
          >
            {activity.prospect_name ||
              activity.prospect_linkedin_url.split('/in/')[1]}
          </a>

          {activity.message_content && (
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
              {activity.message_content}
            </p>
          )}

          {activity.response_content && (
            <div className="mt-2 p-2 bg-green-50 rounded text-sm text-green-800">
              <span className="font-medium">Response:</span>{' '}
              {activity.response_content}
            </div>
          )}

          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>Created: {formatDateTime(activity.created_at)}</span>
            {activity.sent_at && <span>Sent: {formatDateTime(activity.sent_at)}</span>}
            {activity.read_at && <span>Read: {formatDateTime(activity.read_at)}</span>}
            {activity.replied_at && (
              <span>Replied: {formatDateTime(activity.replied_at)}</span>
            )}
          </div>
        </div>

        {/* Status Update */}
        {onUpdateStatus && (
          <div className="relative">
            <button
              onClick={() => setShowStatusMenu(!showStatusMenu)}
              disabled={isLoading}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <DotsIcon className="w-5 h-5" />
            </button>

            {showStatusMenu && (
              <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                {Object.entries(statusConfig).map(([status, { label }]) => (
                  <button
                    key={status}
                    onClick={() => handleStatusUpdate(status as OutreachStatus)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors"
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== Helper Functions ====================

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

// ==================== Icons ====================

function UserPlusIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
    </svg>
  );
}

function MailIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function ChatIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );
}

function CommentIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
    </svg>
  );
}

function HeartIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  );
}

function ShareIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
    </svg>
  );
}

function EyeIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function DotsIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
    </svg>
  );
}

export default OutreachTracker;
