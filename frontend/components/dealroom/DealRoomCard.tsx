'use client';

/**
 * Deal Room Card Component
 *
 * Displays a deal room summary card for the list view.
 */

import Link from 'next/link';
import { DealRoom } from '@/lib/api/dealroom';

interface DealRoomCardProps {
  dealRoom: DealRoom;
  onDuplicate?: () => void;
  onDelete?: () => void;
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  archived: 'bg-yellow-100 text-yellow-800',
  expired: 'bg-red-100 text-red-800',
};

export default function DealRoomCard({
  dealRoom,
  onDuplicate,
  onDelete,
}: DealRoomCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const copyShareLink = () => {
    if (dealRoom.share_url) {
      navigator.clipboard.writeText(dealRoom.share_url);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      {/* Card Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <Link
              href={`/dealroom/${dealRoom.id}`}
              className="text-lg font-semibold text-gray-900 hover:text-blue-600 truncate block"
            >
              {dealRoom.title}
            </Link>
            {dealRoom.prospect_company && (
              <p className="text-sm text-gray-500 mt-1">{dealRoom.prospect_company}</p>
            )}
          </div>
          <span
            className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              statusColors[dealRoom.status]
            }`}
          >
            {dealRoom.status}
          </span>
        </div>
      </div>

      {/* Card Body */}
      <div className="p-4">
        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center">
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
            {dealRoom.total_views} views
          </div>
          <div className="flex items-center">
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            {dealRoom.unique_viewers} viewers
          </div>
        </div>

        {/* Last Activity */}
        <div className="mt-3 text-xs text-gray-400">
          {dealRoom.last_viewed_at
            ? `Last viewed ${formatDate(dealRoom.last_viewed_at)}`
            : `Created ${formatDate(dealRoom.created_at)}`}
        </div>
      </div>

      {/* Card Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 rounded-b-lg flex items-center justify-between">
        <Link
          href={`/dealroom/${dealRoom.id}`}
          className="text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          Edit
        </Link>
        <div className="flex items-center gap-2">
          {dealRoom.share_url && (
            <button
              onClick={copyShareLink}
              className="p-1 text-gray-400 hover:text-gray-600"
              title="Copy share link"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
            </button>
          )}
          {onDuplicate && (
            <button
              onClick={onDuplicate}
              className="p-1 text-gray-400 hover:text-gray-600"
              title="Duplicate"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1 text-gray-400 hover:text-red-600"
              title="Delete"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
