<<<<<<< HEAD
'use client';

import { useState, useEffect } from 'react';
import { SettingsSection, Toggle, FormField } from '@/components/settings';
import type { NotificationPreferences } from '@/lib/types/settings';
import {
  getNotificationPreferences,
  updateNotificationPreferences,
} from '@/lib/api/settings';

const daysOfWeek = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

export default function NotificationsSettingsPage() {
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const data = await getNotificationPreferences();
      setPreferences(data);
    } catch (err) {
      setError('Failed to load notification preferences');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!preferences) return;

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updated = await updateNotificationPreferences(preferences);
      setPreferences(updated);
      setSuccessMessage('Notification preferences saved');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save changes');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const updateEmailPref = (key: keyof NotificationPreferences['email'], value: boolean) => {
    setPreferences((prev) =>
      prev
        ? {
            ...prev,
            email: { ...prev.email, [key]: value },
          }
        : null
    );
  };

  const updateInAppPref = (key: keyof NotificationPreferences['inApp'], value: boolean) => {
    setPreferences((prev) =>
      prev
        ? {
            ...prev,
            inApp: { ...prev.inApp, [key]: value },
          }
        : null
    );
  };

  const updateDigestPref = <K extends keyof NotificationPreferences['digest']>(
    key: K,
    value: NotificationPreferences['digest'][K]
  ) => {
    setPreferences((prev) =>
      prev
        ? {
            ...prev,
            digest: { ...prev.digest, [key]: value },
          }
        : null
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Failed to load preferences</p>
        <button
          onClick={loadPreferences}
          className="mt-4 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success/Error Messages */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Email Notifications */}
      <SettingsSection
        title="Email Notifications"
        description="Control which notifications you receive via email"
      >
        <div className="space-y-4">
          <Toggle
            enabled={preferences.email.transcriptAnalyzed}
            onChange={(value) => updateEmailPref('transcriptAnalyzed', value)}
            label="Transcript Analyzed"
            description="Receive an email when a transcript has been analyzed"
          />
          <Toggle
            enabled={preferences.email.contentGenerated}
            onChange={(value) => updateEmailPref('contentGenerated', value)}
            label="Content Generated"
            description="Receive an email when content generation is complete"
          />
          <Toggle
            enabled={preferences.email.prospectEnriched}
            onChange={(value) => updateEmailPref('prospectEnriched', value)}
            label="Prospect Enriched"
            description="Receive an email when prospect enrichment completes"
          />
          <Toggle
            enabled={preferences.email.weeklyReport}
            onChange={(value) => updateEmailPref('weeklyReport', value)}
            label="Weekly Report"
            description="Receive a weekly summary of your activity"
          />
          <Toggle
            enabled={preferences.email.teamUpdates}
            onChange={(value) => updateEmailPref('teamUpdates', value)}
            label="Team Updates"
            description="Receive updates about team activity and changes"
          />
          <Toggle
            enabled={preferences.email.securityAlerts}
            onChange={(value) => updateEmailPref('securityAlerts', value)}
            label="Security Alerts"
            description="Important security-related notifications (recommended)"
          />
        </div>
      </SettingsSection>

      {/* In-App Notifications */}
      <SettingsSection
        title="In-App Notifications"
        description="Control which notifications appear in the app"
      >
        <div className="space-y-4">
          <Toggle
            enabled={preferences.inApp.transcriptAnalyzed}
            onChange={(value) => updateInAppPref('transcriptAnalyzed', value)}
            label="Transcript Analyzed"
            description="Show notification when a transcript has been analyzed"
          />
          <Toggle
            enabled={preferences.inApp.contentGenerated}
            onChange={(value) => updateInAppPref('contentGenerated', value)}
            label="Content Generated"
            description="Show notification when content generation is complete"
          />
          <Toggle
            enabled={preferences.inApp.prospectEnriched}
            onChange={(value) => updateInAppPref('prospectEnriched', value)}
            label="Prospect Enriched"
            description="Show notification when prospect enrichment completes"
          />
          <Toggle
            enabled={preferences.inApp.coachingFeedback}
            onChange={(value) => updateInAppPref('coachingFeedback', value)}
            label="Coaching Feedback"
            description="Show notification when new coaching feedback is available"
          />
          <Toggle
            enabled={preferences.inApp.mentions}
            onChange={(value) => updateInAppPref('mentions', value)}
            label="Mentions"
            description="Show notification when someone mentions you"
          />
        </div>
      </SettingsSection>

      {/* Email Digest */}
      <SettingsSection
        title="Email Digest"
        description="Receive a summary of your notifications"
      >
        <div className="space-y-4">
          <Toggle
            enabled={preferences.digest.enabled}
            onChange={(value) => updateDigestPref('enabled', value)}
            label="Enable Email Digest"
            description="Receive a periodic digest of your notifications instead of individual emails"
          />

          {preferences.digest.enabled && (
            <div className="pl-0 md:pl-4 space-y-4 pt-4 border-t border-gray-200">
              {/* Frequency */}
              <FormField label="Digest Frequency" htmlFor="digestFrequency">
                <select
                  id="digestFrequency"
                  value={preferences.digest.frequency}
                  onChange={(e) =>
                    updateDigestPref(
                      'frequency',
                      e.target.value as NotificationPreferences['digest']['frequency']
                    )
                  }
                  className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </FormField>

              {/* Day of Week (for weekly) */}
              {preferences.digest.frequency === 'weekly' && (
                <FormField label="Day of Week" htmlFor="dayOfWeek">
                  <select
                    id="dayOfWeek"
                    value={preferences.digest.dayOfWeek ?? 1}
                    onChange={(e) =>
                      updateDigestPref('dayOfWeek', parseInt(e.target.value, 10))
                    }
                    className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {daysOfWeek.map((day) => (
                      <option key={day.value} value={day.value}>
                        {day.label}
                      </option>
                    ))}
                  </select>
                </FormField>
              )}

              {/* Time of Day */}
              <FormField
                label="Time of Day"
                htmlFor="timeOfDay"
                hint="Digest will be sent at this time in your local timezone"
              >
                <input
                  id="timeOfDay"
                  type="time"
                  value={preferences.digest.timeOfDay}
                  onChange={(e) => updateDigestPref('timeOfDay', e.target.value)}
                  className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </FormField>
            </div>
          )}
        </div>
      </SettingsSection>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
=======
/**
 * Notification Settings Page.
 *
 * Allows users to configure their notification preferences.
 */

import { NotificationPreferences } from "@/components/notifications";

export const metadata = {
  title: "Notification Settings - Sales OS",
  description: "Configure your notification preferences",
};

export default function NotificationSettingsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <nav className="flex items-center gap-2 text-sm text-gray-500 mb-4">
            <a href="/settings" className="hover:text-gray-700">
              Settings
            </a>
            <span>/</span>
            <span className="text-gray-900">Notifications</span>
          </nav>
          <h1 className="text-2xl font-bold text-gray-900">Notification Settings</h1>
          <p className="mt-2 text-gray-600">
            Manage how and when you receive notifications from Sales OS.
          </p>
        </div>

        {/* Preferences Component */}
        <div className="bg-white rounded-lg shadow p-6">
          <NotificationPreferences />
        </div>
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
      </div>
    </div>
  );
}
