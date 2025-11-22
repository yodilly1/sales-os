/**
 * NotificationItem component - Individual notification display.
 *
 * Displays a single notification with icon, title, body, and actions.
 */

"use client";

import React from "react";
import { Notification, NotificationType } from "@/lib/api/notifications";

interface NotificationItemProps {
  notification: Notification;
  onClick?: () => void;
  onMarkRead?: () => void;
  onDelete?: () => void;
}

// Notification type icons and colors
const notificationConfig: Record<
  NotificationType,
  { icon: React.ReactNode; bgColor: string; iconColor: string }
> = {
  transcript_processed: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    bgColor: "bg-blue-100",
    iconColor: "text-blue-600",
  },
  content_generated: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    bgColor: "bg-green-100",
    iconColor: "text-green-600",
  },
  enrichment_complete: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    bgColor: "bg-purple-100",
    iconColor: "text-purple-600",
  },
  coaching_feedback_ready: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    bgColor: "bg-yellow-100",
    iconColor: "text-yellow-600",
  },
  integration_sync_status: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    bgColor: "bg-indigo-100",
    iconColor: "text-indigo-600",
  },
  system_alert: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    bgColor: "bg-red-100",
    iconColor: "text-red-600",
  },
  team_update: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    bgColor: "bg-teal-100",
    iconColor: "text-teal-600",
  },
};

/**
 * Format relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "Just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  }
}

export function NotificationItem({
  notification,
  onClick,
  onMarkRead,
  onDelete,
}: NotificationItemProps) {
  const config = notificationConfig[notification.type] || {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    bgColor: "bg-gray-100",
    iconColor: "text-gray-600",
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onClick?.();
  };

  const handleMarkRead = (e: React.MouseEvent) => {
    e.stopPropagation();
    onMarkRead?.();
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.();
  };

  return (
    <div
      className={`group relative p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
        !notification.is_read ? "bg-indigo-50/50" : ""
      }`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick?.()}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full ${config.bgColor} ${config.iconColor} flex items-center justify-center`}
        >
          {config.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p
              className={`text-sm ${
                !notification.is_read ? "font-semibold text-gray-900" : "text-gray-700"
              }`}
            >
              {notification.title}
            </p>

            {/* Unread indicator */}
            {!notification.is_read && (
              <span className="flex-shrink-0 w-2 h-2 bg-indigo-600 rounded-full mt-1.5" />
            )}
          </div>

          <p className="mt-0.5 text-sm text-gray-600 line-clamp-2">
            {notification.body}
          </p>

          <p className="mt-1 text-xs text-gray-400">
            {formatRelativeTime(notification.created_at)}
          </p>
        </div>

        {/* Actions (visible on hover) */}
        <div className="hidden group-hover:flex items-center gap-1">
          {!notification.is_read && onMarkRead && (
            <button
              onClick={handleMarkRead}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
              title="Mark as read"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
          )}

          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-1 text-gray-400 hover:text-red-600 rounded"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Priority indicator for high/urgent */}
      {(notification.priority === "high" || notification.priority === "urgent") && (
        <div
          className={`absolute left-0 top-0 bottom-0 w-1 ${
            notification.priority === "urgent" ? "bg-red-500" : "bg-orange-400"
          }`}
        />
      )}
    </div>
  );
}
