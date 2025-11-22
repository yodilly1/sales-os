/**
 * NotificationToast component - Toast notifications for real-time alerts.
 *
 * Displays transient notifications that automatically dismiss after a delay.
 */

"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Notification, NotificationType } from "@/lib/api/notifications";

interface Toast {
  id: string;
  notification: Notification;
  exiting?: boolean;
}

interface NotificationToastProps {
  notifications: Toast[];
  onDismiss: (id: string) => void;
  onClick?: (notification: Notification) => void;
  duration?: number;
}

// Toast type colors
const toastColors: Record<NotificationType, { bg: string; border: string; icon: string }> = {
  transcript_processed: { bg: "bg-blue-50", border: "border-blue-200", icon: "text-blue-500" },
  content_generated: { bg: "bg-green-50", border: "border-green-200", icon: "text-green-500" },
  enrichment_complete: { bg: "bg-purple-50", border: "border-purple-200", icon: "text-purple-500" },
  coaching_feedback_ready: { bg: "bg-yellow-50", border: "border-yellow-200", icon: "text-yellow-500" },
  integration_sync_status: { bg: "bg-indigo-50", border: "border-indigo-200", icon: "text-indigo-500" },
  system_alert: { bg: "bg-red-50", border: "border-red-200", icon: "text-red-500" },
  team_update: { bg: "bg-teal-50", border: "border-teal-200", icon: "text-teal-500" },
};

function SingleToast({
  toast,
  onDismiss,
  onClick,
  duration = 5000,
}: {
  toast: Toast;
  onDismiss: (id: string) => void;
  onClick?: (notification: Notification) => void;
  duration?: number;
}) {
  const [progress, setProgress] = useState(100);
  const { notification, exiting } = toast;
  const colors = toastColors[notification.type] || {
    bg: "bg-gray-50",
    border: "border-gray-200",
    icon: "text-gray-500",
  };

  // Auto-dismiss timer
  useEffect(() => {
    if (exiting) return;

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
        onDismiss(toast.id);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [toast.id, duration, exiting, onDismiss]);

  const handleClick = () => {
    onClick?.(notification);
    onDismiss(toast.id);
  };

  return (
    <div
      className={`
        relative overflow-hidden rounded-lg shadow-lg border
        ${colors.bg} ${colors.border}
        transform transition-all duration-300 ease-out
        ${exiting ? "opacity-0 translate-x-full" : "opacity-100 translate-x-0"}
        cursor-pointer hover:shadow-xl
      `}
      onClick={handleClick}
      role="alert"
    >
      <div className="p-4 pr-10">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className={`flex-shrink-0 ${colors.icon}`}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">
              {notification.title}
            </p>
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {notification.body}
            </p>
          </div>
        </div>
      </div>

      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDismiss(toast.id);
        }}
        className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 rounded"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
        <div
          className="h-full bg-gray-400 transition-all duration-50 ease-linear"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

export function NotificationToast({
  notifications,
  onDismiss,
  onClick,
  duration = 5000,
}: NotificationToastProps) {
  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {notifications.map((toast) => (
        <SingleToast
          key={toast.id}
          toast={toast}
          onDismiss={onDismiss}
          onClick={onClick}
          duration={duration}
        />
      ))}
    </div>
  );
}

// =============================================================================
// useToastNotifications Hook
// =============================================================================

interface UseToastNotificationsReturn {
  toasts: Toast[];
  addToast: (notification: Notification) => void;
  dismissToast: (id: string) => void;
  clearAll: () => void;
}

/**
 * Hook for managing toast notifications.
 */
export function useToastNotifications(maxToasts: number = 5): UseToastNotificationsReturn {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback(
    (notification: Notification) => {
      const id = `toast-${notification.id}-${Date.now()}`;

      setToasts((prev) => {
        // Remove oldest if at max
        const updated = prev.length >= maxToasts ? prev.slice(1) : prev;
        return [...updated, { id, notification }];
      });
    },
    [maxToasts]
  );

  const dismissToast = useCallback((id: string) => {
    // First mark as exiting for animation
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
    );

    // Then remove after animation
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const clearAll = useCallback(() => {
    setToasts((prev) => prev.map((t) => ({ ...t, exiting: true })));
    setTimeout(() => setToasts([]), 300);
  }, []);

  return { toasts, addToast, dismissToast, clearAll };
}
