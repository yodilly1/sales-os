/**
 * NotificationList component - List of notification items.
 *
 * Displays a list of notifications with loading states and empty states.
 */

"use client";

import React from "react";
import { Notification } from "@/lib/api/notifications";
import { NotificationItem } from "./NotificationItem";

interface NotificationListProps {
  notifications: Notification[];
  loading?: boolean;
  onNotificationClick?: (notificationId: string) => void;
  onMarkRead?: (notificationId: string) => void;
  onDelete?: (notificationId: string) => void;
}

export function NotificationList({
  notifications,
  loading = false,
  onNotificationClick,
  onMarkRead,
  onDelete,
}: NotificationListProps) {
  // Loading skeleton
  if (loading && notifications.length === 0) {
    return (
      <div className="divide-y divide-gray-100">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 animate-pulse">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-full" />
                <div className="h-3 bg-gray-200 rounded w-1/4" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <svg
          className="w-12 h-12 text-gray-300 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        <p className="text-sm text-gray-500">No notifications yet</p>
        <p className="text-xs text-gray-400 mt-1">
          We&apos;ll notify you when something important happens
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClick={() => onNotificationClick?.(notification.id)}
          onMarkRead={() => onMarkRead?.(notification.id)}
          onDelete={() => onDelete?.(notification.id)}
        />
      ))}
    </div>
  );
}
