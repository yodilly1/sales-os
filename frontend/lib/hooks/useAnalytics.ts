/**
 * Deal Room Analytics Tracking Hook
 *
 * Provides utilities for tracking viewer engagement in deal rooms.
 * Tracks page views, content interactions, and time spent.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { publicRoomApi } from '@/lib/api/dealroom';

interface UseAnalyticsOptions {
  slug: string;
  viewerEmail?: string;
  viewerName?: string;
  enabled?: boolean;
}

interface AnalyticsState {
  sessionId: string | null;
  viewEventId: string | null;
  timeSpent: number;
}

/**
 * Hook for tracking deal room analytics
 */
export function useAnalytics({
  slug,
  viewerEmail,
  viewerName,
  enabled = true,
}: UseAnalyticsOptions) {
  const [state, setState] = useState<AnalyticsState>({
    sessionId: null,
    viewEventId: null,
    timeSpent: 0,
  });

  const startTime = useRef<number>(Date.now());
  const lastUpdateTime = useRef<number>(Date.now());
  const isActive = useRef<boolean>(true);

  // Initialize session and track initial view
  useEffect(() => {
    if (!enabled) return;

    const initSession = async () => {
      try {
        const result = await publicRoomApi.trackView(slug, {
          viewer_email: viewerEmail,
          viewer_name: viewerName,
        });
        setState((prev) => ({
          ...prev,
          sessionId: result.session_id,
          viewEventId: result.view_event_id,
        }));
      } catch (error) {
        console.error('Failed to initialize analytics session:', error);
      }
    };

    initSession();
  }, [slug, viewerEmail, viewerName, enabled]);

  // Track time spent on page
  useEffect(() => {
    if (!enabled || !state.sessionId) return;

    const updateTimeSpent = () => {
      if (!isActive.current) return;

      const now = Date.now();
      const timeSpent = Math.floor((now - startTime.current) / 1000);
      setState((prev) => ({ ...prev, timeSpent }));
    };

    // Update time every second
    const interval = setInterval(updateTimeSpent, 1000);

    // Send time to server every 30 seconds
    const serverInterval = setInterval(() => {
      if (!isActive.current) return;
      const timeSpent = Math.floor((Date.now() - startTime.current) / 1000);
      publicRoomApi.updateSessionTime(slug, state.sessionId!, timeSpent).catch(console.error);
    }, 30000);

    return () => {
      clearInterval(interval);
      clearInterval(serverInterval);
    };
  }, [slug, state.sessionId, enabled]);

  // Track visibility changes
  useEffect(() => {
    if (!enabled) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        isActive.current = false;
        // Send final time update when user leaves
        if (state.sessionId) {
          const timeSpent = Math.floor((Date.now() - startTime.current) / 1000);
          publicRoomApi.updateSessionTime(slug, state.sessionId, timeSpent).catch(console.error);
        }
      } else {
        isActive.current = true;
        lastUpdateTime.current = Date.now();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [slug, state.sessionId, enabled]);

  // Track before unload
  useEffect(() => {
    if (!enabled || !state.sessionId) return;

    const handleBeforeUnload = () => {
      const timeSpent = Math.floor((Date.now() - startTime.current) / 1000);
      // Use sendBeacon for reliable delivery on page close
      const data = JSON.stringify({
        session_id: state.sessionId,
        time_spent_seconds: timeSpent,
      });
      navigator.sendBeacon?.(`/room/${slug}/update-session-time`, data);
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [slug, state.sessionId, enabled]);

  // Track content view
  const trackContentView = useCallback(
    async (
      contentId: string,
      options?: {
        timeSpentSeconds?: number;
        scrollDepthPercent?: number;
        downloaded?: boolean;
      }
    ) => {
      if (!enabled || !state.viewEventId) return;

      try {
        await publicRoomApi.trackContentView(slug, {
          content_id: contentId,
          view_event_id: state.viewEventId,
          time_spent_seconds: options?.timeSpentSeconds || 0,
          scroll_depth_percent: options?.scrollDepthPercent || 0,
          downloaded: options?.downloaded || false,
        });
      } catch (error) {
        console.error('Failed to track content view:', error);
      }
    },
    [slug, state.viewEventId, enabled]
  );

  // Track download
  const trackDownload = useCallback(
    (contentId: string) => {
      trackContentView(contentId, { downloaded: true });
    },
    [trackContentView]
  );

  return {
    sessionId: state.sessionId,
    viewEventId: state.viewEventId,
    timeSpent: state.timeSpent,
    trackContentView,
    trackDownload,
  };
}

/**
 * Hook for tracking scroll depth on content
 */
export function useScrollTracking(onScrollDepthChange: (depth: number) => void) {
  const elementRef = useRef<HTMLDivElement | null>(null);
  const maxScrollDepth = useRef<number>(0);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const handleScroll = () => {
      const scrollHeight = element.scrollHeight - element.clientHeight;
      if (scrollHeight <= 0) return;

      const scrollDepth = Math.round((element.scrollTop / scrollHeight) * 100);
      if (scrollDepth > maxScrollDepth.current) {
        maxScrollDepth.current = scrollDepth;
        onScrollDepthChange(scrollDepth);
      }
    };

    element.addEventListener('scroll', handleScroll);
    return () => element.removeEventListener('scroll', handleScroll);
  }, [onScrollDepthChange]);

  return elementRef;
}

/**
 * Hook for tracking time spent on a specific piece of content
 */
export function useContentTimeTracking(
  onTimeUpdate: (timeSpent: number) => void,
  active = true
) {
  const startTime = useRef<number | null>(null);
  const totalTime = useRef<number>(0);

  useEffect(() => {
    if (active) {
      startTime.current = Date.now();
    } else if (startTime.current) {
      totalTime.current += Date.now() - startTime.current;
      onTimeUpdate(Math.floor(totalTime.current / 1000));
      startTime.current = null;
    }

    return () => {
      if (startTime.current) {
        totalTime.current += Date.now() - startTime.current;
        onTimeUpdate(Math.floor(totalTime.current / 1000));
      }
    };
  }, [active, onTimeUpdate]);

  return totalTime.current;
}

export default useAnalytics;
