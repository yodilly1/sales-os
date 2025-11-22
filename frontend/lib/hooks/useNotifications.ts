/**
 * React hooks for notification management.
 *
 * Provides hooks for fetching notifications, managing WebSocket connections,
 * and handling real-time notification updates.
 */

"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Notification,
  NotificationListResponse,
  UnreadCountResponse,
  ListNotificationsParams,
  listNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
} from "../api/notifications";

// =============================================================================
// WebSocket Types
// =============================================================================

interface WebSocketMessage {
  event_type: string;
  notification?: Notification;
  status?: string;
  timestamp?: string;
}

type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

// =============================================================================
// useNotificationWebSocket Hook
// =============================================================================

interface UseNotificationWebSocketOptions {
  onNotification?: (notification: Notification) => void;
  onConnectionChange?: (status: WebSocketStatus) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseNotificationWebSocketReturn {
  status: WebSocketStatus;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for managing WebSocket connection for real-time notifications.
 */
export function useNotificationWebSocket(
  options: UseNotificationWebSocketOptions = {}
): UseNotificationWebSocketReturn {
  const {
    onNotification,
    onConnectionChange,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const updateStatus = useCallback(
    (newStatus: WebSocketStatus) => {
      setStatus(newStatus);
      onConnectionChange?.(newStatus);
    },
    [onConnectionChange]
  );

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (!token) {
      console.warn("No auth token available for WebSocket connection");
      return;
    }

    const wsUrl =
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/notifications";
    const url = `${wsUrl}?token=${encodeURIComponent(token)}`;

    updateStatus("connecting");

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        updateStatus("connected");
        reconnectAttemptsRef.current = 0;

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "heartbeat" }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.event_type === "notification" && message.notification) {
            onNotification?.(message.notification);
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onclose = () => {
        clearTimers();
        updateStatus("disconnected");

        // Attempt reconnection
        if (
          autoReconnect &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current += 1;
          const delay =
            reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        updateStatus("error");
      };
    } catch (error) {
      console.error("WebSocket connection error:", error);
      updateStatus("error");
    }
  }, [
    autoReconnect,
    maxReconnectAttempts,
    reconnectInterval,
    onNotification,
    updateStatus,
    clearTimers,
  ]);

  const disconnect = useCallback(() => {
    clearTimers();
    reconnectAttemptsRef.current = maxReconnectAttempts; // Prevent auto-reconnect

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    updateStatus("disconnected");
  }, [clearTimers, maxReconnectAttempts, updateStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [clearTimers]);

  return { status, connect, disconnect };
}

// =============================================================================
// useNotifications Hook
// =============================================================================

interface UseNotificationsOptions {
  autoFetch?: boolean;
  autoConnect?: boolean;
  pageSize?: number;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  loading: boolean;
  error: Error | null;
  unreadCount: number;
  unreadByType: Record<string, number>;
  hasMore: boolean;
  page: number;
  total: number;
  wsStatus: WebSocketStatus;
  fetchNotifications: (params?: ListNotificationsParams) => Promise<void>;
  fetchMore: () => Promise<void>;
  refresh: () => Promise<void>;
  markRead: (notificationIds: string[]) => Promise<void>;
  markAllRead: () => Promise<void>;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

/**
 * Comprehensive hook for managing notifications state.
 *
 * Combines notification fetching, pagination, WebSocket connection,
 * and read status management.
 */
export function useNotifications(
  options: UseNotificationsOptions = {}
): UseNotificationsReturn {
  const { autoFetch = true, autoConnect = true, pageSize = 20 } = options;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [unreadByType, setUnreadByType] = useState<Record<string, number>>({});
  const [hasMore, setHasMore] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const currentParamsRef = useRef<ListNotificationsParams>({ page_size: pageSize });

  // Handle new notification from WebSocket
  const handleNewNotification = useCallback((notification: Notification) => {
    setNotifications((prev) => {
      // Check for duplicates
      if (prev.some((n) => n.id === notification.id)) {
        return prev;
      }
      return [notification, ...prev];
    });

    // Update unread count
    if (!notification.is_read) {
      setUnreadCount((prev) => prev + 1);
      setUnreadByType((prev) => ({
        ...prev,
        [notification.type]: (prev[notification.type] || 0) + 1,
      }));
    }
  }, []);

  const { status: wsStatus, connect, disconnect } = useNotificationWebSocket({
    onNotification: handleNewNotification,
    autoReconnect: true,
  });

  // Fetch notifications
  const fetchNotifications = useCallback(
    async (params: ListNotificationsParams = {}) => {
      setLoading(true);
      setError(null);

      try {
        const mergedParams = { ...currentParamsRef.current, ...params };
        currentParamsRef.current = mergedParams;

        const response = await listNotifications(mergedParams);

        if (mergedParams.page === 1 || !mergedParams.page) {
          setNotifications(response.notifications);
        } else {
          setNotifications((prev) => [...prev, ...response.notifications]);
        }

        setPage(response.page);
        setTotal(response.total);
        setHasMore(response.has_more);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Failed to fetch notifications"));
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Fetch next page
  const fetchMore = useCallback(async () => {
    if (!hasMore || loading) return;
    await fetchNotifications({ ...currentParamsRef.current, page: page + 1 });
  }, [hasMore, loading, page, fetchNotifications]);

  // Refresh notifications
  const refresh = useCallback(async () => {
    await fetchNotifications({ ...currentParamsRef.current, page: 1 });
    await fetchUnreadCount();
  }, [fetchNotifications]);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await getUnreadCount();
      setUnreadCount(response.count);
      setUnreadByType(response.by_type);
    } catch (err) {
      console.error("Failed to fetch unread count:", err);
    }
  }, []);

  // Mark notifications as read
  const markRead = useCallback(
    async (notificationIds: string[]) => {
      try {
        await markAsRead(notificationIds);

        // Update local state
        setNotifications((prev) =>
          prev.map((n) =>
            notificationIds.includes(n.id)
              ? { ...n, is_read: true, read_at: new Date().toISOString() }
              : n
          )
        );

        // Recalculate unread count
        const markedCount = notificationIds.length;
        setUnreadCount((prev) => Math.max(0, prev - markedCount));

        // Update by-type counts
        const markedNotifications = notifications.filter(
          (n) => notificationIds.includes(n.id) && !n.is_read
        );
        setUnreadByType((prev) => {
          const updated = { ...prev };
          markedNotifications.forEach((n) => {
            if (updated[n.type]) {
              updated[n.type] = Math.max(0, updated[n.type] - 1);
            }
          });
          return updated;
        });
      } catch (err) {
        console.error("Failed to mark notifications as read:", err);
        throw err;
      }
    },
    [notifications]
  );

  // Mark all as read
  const markAllRead = useCallback(async () => {
    try {
      await markAllAsRead();

      // Update local state
      setNotifications((prev) =>
        prev.map((n) => ({
          ...n,
          is_read: true,
          read_at: n.read_at || new Date().toISOString(),
        }))
      );
      setUnreadCount(0);
      setUnreadByType({});
    } catch (err) {
      console.error("Failed to mark all notifications as read:", err);
      throw err;
    }
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchNotifications();
      fetchUnreadCount();
    }
  }, [autoFetch, fetchNotifications, fetchUnreadCount]);

  // Auto-connect WebSocket on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    notifications,
    loading,
    error,
    unreadCount,
    unreadByType,
    hasMore,
    page,
    total,
    wsStatus,
    fetchNotifications,
    fetchMore,
    refresh,
    markRead,
    markAllRead,
    connectWebSocket: connect,
    disconnectWebSocket: disconnect,
  };
}

// =============================================================================
// useUnreadCount Hook
// =============================================================================

/**
 * Lightweight hook for just the unread count.
 *
 * Useful for showing notification badges without loading full notifications.
 */
export function useUnreadCount(): {
  count: number;
  byType: Record<string, number>;
  loading: boolean;
  refresh: () => Promise<void>;
} {
  const [count, setCount] = useState(0);
  const [byType, setByType] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getUnreadCount();
      setCount(response.count);
      setByType(response.by_type);
    } catch (err) {
      console.error("Failed to fetch unread count:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { count, byType, loading, refresh };
}
