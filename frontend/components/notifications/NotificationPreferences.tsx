/**
 * NotificationPreferences component - User notification settings.
 *
 * Allows users to configure their notification preferences for each
 * notification type and delivery channel.
 */

"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  NotificationType,
  NotificationChannel,
  NotificationPreference,
  getPreferences,
  updatePreference,
} from "@/lib/api/notifications";

// =============================================================================
// Types & Constants
// =============================================================================

interface PreferenceMatrix {
  [notificationType: string]: {
    [channel: string]: {
      enabled: boolean;
      digest_frequency?: string;
      digest_time?: string;
      digest_timezone?: string;
    };
  };
}

const NOTIFICATION_TYPES: { type: NotificationType; label: string; description: string }[] = [
  {
    type: "transcript_processed",
    label: "Transcript Processed",
    description: "When a call transcript has been processed and analyzed",
  },
  {
    type: "content_generated",
    label: "Content Generated",
    description: "When sales content (decks, proposals) has been created",
  },
  {
    type: "enrichment_complete",
    label: "Enrichment Complete",
    description: "When prospect data enrichment is finished",
  },
  {
    type: "coaching_feedback_ready",
    label: "Coaching Feedback Ready",
    description: "When coaching feedback for a call is available",
  },
  {
    type: "integration_sync_status",
    label: "Integration Sync Status",
    description: "Updates about CRM and integration syncs",
  },
  {
    type: "system_alert",
    label: "System Alerts",
    description: "Important system notifications and alerts",
  },
  {
    type: "team_update",
    label: "Team Updates",
    description: "Updates about team activity and changes",
  },
];

const CHANNELS: { channel: NotificationChannel; label: string; icon: React.ReactNode }[] = [
  {
    channel: "in_app",
    label: "In-App",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
  },
  {
    channel: "email_instant",
    label: "Email (Instant)",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    channel: "email_digest",
    label: "Email (Digest)",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
];

const DIGEST_FREQUENCIES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern Time (ET)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "UTC", label: "UTC" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Paris", label: "Paris (CET/CEST)" },
];

// =============================================================================
// Component
// =============================================================================

interface NotificationPreferencesProps {
  className?: string;
}

export function NotificationPreferences({ className = "" }: NotificationPreferencesProps) {
  const [preferences, setPreferences] = useState<PreferenceMatrix>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Digest settings state
  const [digestFrequency, setDigestFrequency] = useState("daily");
  const [digestTime, setDigestTime] = useState("09:00");
  const [digestTimezone, setDigestTimezone] = useState("America/New_York");

  // Load preferences
  useEffect(() => {
    async function loadPreferences() {
      try {
        setLoading(true);
        const prefs = await getPreferences();

        // Convert to matrix format
        const matrix: PreferenceMatrix = {};
        prefs.forEach((pref) => {
          if (!matrix[pref.notification_type]) {
            matrix[pref.notification_type] = {};
          }
          matrix[pref.notification_type][pref.channel] = {
            enabled: pref.enabled,
            digest_frequency: pref.digest_frequency,
            digest_time: pref.digest_time,
            digest_timezone: pref.digest_timezone,
          };

          // Extract digest settings from first email_digest preference
          if (pref.channel === "email_digest" && pref.digest_frequency) {
            setDigestFrequency(pref.digest_frequency);
            if (pref.digest_time) setDigestTime(pref.digest_time);
            if (pref.digest_timezone) setDigestTimezone(pref.digest_timezone);
          }
        });

        setPreferences(matrix);
      } catch (err) {
        setError("Failed to load notification preferences");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadPreferences();
  }, []);

  // Check if a preference is enabled
  const isEnabled = useCallback(
    (type: NotificationType, channel: NotificationChannel): boolean => {
      // Default: in_app enabled, others disabled
      const defaults: Record<NotificationChannel, boolean> = {
        in_app: true,
        email_instant: false,
        email_digest: false,
        websocket: true,
      };

      return preferences[type]?.[channel]?.enabled ?? defaults[channel];
    },
    [preferences]
  );

  // Toggle a preference
  const togglePreference = async (type: NotificationType, channel: NotificationChannel) => {
    const currentValue = isEnabled(type, channel);
    const newValue = !currentValue;
    const key = `${type}-${channel}`;

    setSaving(key);
    setError(null);

    try {
      await updatePreference(type, channel, {
        enabled: newValue,
        ...(channel === "email_digest" && {
          digest_frequency: digestFrequency,
          digest_time: digestTime,
          digest_timezone: digestTimezone,
        }),
      });

      // Update local state
      setPreferences((prev) => ({
        ...prev,
        [type]: {
          ...prev[type],
          [channel]: {
            ...prev[type]?.[channel],
            enabled: newValue,
          },
        },
      }));
    } catch (err) {
      setError("Failed to update preference");
      console.error(err);
    } finally {
      setSaving(null);
    }
  };

  // Update digest settings for all email_digest preferences
  const updateDigestSettings = async () => {
    setSaving("digest");
    setError(null);

    try {
      for (const { type } of NOTIFICATION_TYPES) {
        if (isEnabled(type, "email_digest")) {
          await updatePreference(type, "email_digest", {
            enabled: true,
            digest_frequency: digestFrequency,
            digest_time: digestTime,
            digest_timezone: digestTimezone,
          });
        }
      }
    } catch (err) {
      setError("Failed to update digest settings");
      console.error(err);
    } finally {
      setSaving(null);
    }
  };

  if (loading) {
    return (
      <div className={`${className} animate-pulse`}>
        <div className="h-8 bg-gray-200 rounded w-48 mb-6" />
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900">Notification Preferences</h2>
        <p className="mt-1 text-sm text-gray-500">
          Choose how you want to receive notifications for different events.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Preference Matrix */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Notification Type
              </th>
              {CHANNELS.map(({ channel, label, icon }) => (
                <th
                  key={channel}
                  className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  <div className="flex flex-col items-center gap-1">
                    {icon}
                    <span>{label}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {NOTIFICATION_TYPES.map(({ type, label, description }) => (
              <tr key={type} className="hover:bg-gray-50">
                <td className="px-4 py-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{label}</p>
                    <p className="text-xs text-gray-500">{description}</p>
                  </div>
                </td>
                {CHANNELS.map(({ channel }) => (
                  <td key={channel} className="px-4 py-4 text-center">
                    <button
                      onClick={() => togglePreference(type, channel)}
                      disabled={saving === `${type}-${channel}`}
                      className={`
                        relative inline-flex h-6 w-11 items-center rounded-full
                        transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                        ${isEnabled(type, channel) ? "bg-indigo-600" : "bg-gray-200"}
                        ${saving === `${type}-${channel}` ? "opacity-50 cursor-wait" : ""}
                      `}
                      role="switch"
                      aria-checked={isEnabled(type, channel)}
                    >
                      <span
                        className={`
                          inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                          ${isEnabled(type, channel) ? "translate-x-6" : "translate-x-1"}
                        `}
                      />
                    </button>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Digest Settings */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Email Digest Settings</h3>
        <p className="text-sm text-gray-500 mb-4">
          Configure when you receive digest emails for notification types with &quot;Email (Digest)&quot; enabled.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Frequency */}
          <div>
            <label htmlFor="digest-frequency" className="block text-sm font-medium text-gray-700 mb-1">
              Frequency
            </label>
            <select
              id="digest-frequency"
              value={digestFrequency}
              onChange={(e) => setDigestFrequency(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              {DIGEST_FREQUENCIES.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Time */}
          <div>
            <label htmlFor="digest-time" className="block text-sm font-medium text-gray-700 mb-1">
              Time
            </label>
            <input
              type="time"
              id="digest-time"
              value={digestTime}
              onChange={(e) => setDigestTime(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            />
          </div>

          {/* Timezone */}
          <div>
            <label htmlFor="digest-timezone" className="block text-sm font-medium text-gray-700 mb-1">
              Timezone
            </label>
            <select
              id="digest-timezone"
              value={digestTimezone}
              onChange={(e) => setDigestTimezone(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              {TIMEZONES.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={updateDigestSettings}
            disabled={saving === "digest"}
            className={`
              px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
              hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              ${saving === "digest" ? "opacity-50 cursor-wait" : ""}
            `}
          >
            {saving === "digest" ? "Saving..." : "Save Digest Settings"}
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 flex gap-4">
        <button
          onClick={async () => {
            for (const { type } of NOTIFICATION_TYPES) {
              for (const { channel } of CHANNELS) {
                if (!isEnabled(type, channel)) {
                  await togglePreference(type, channel);
                }
              }
            }
          }}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Enable all
        </button>
        <button
          onClick={async () => {
            for (const { type } of NOTIFICATION_TYPES) {
              for (const { channel } of CHANNELS) {
                if (channel !== "in_app" && isEnabled(type, channel)) {
                  await togglePreference(type, channel);
                }
              }
            }
          }}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Disable all emails
        </button>
      </div>
    </div>
  );
}
