'use client';

import { useState, useEffect } from 'react';
import { SettingsSection, FormField, AvatarUpload } from '@/components/settings';
import type { User, UserPreferences } from '@/lib/types/settings';
import { getUser, updateUser, uploadAvatar } from '@/lib/api/settings';

const timezones = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
];

const dateFormats = [
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
];

const defaultViews = [
  { value: 'dashboard', label: 'Dashboard' },
  { value: 'transcripts', label: 'Transcripts' },
  { value: 'prospects', label: 'Prospects' },
];

export default function ProfileSettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'system',
    language: 'en',
    timezone: 'America/New_York',
    dateFormat: 'MM/DD/YYYY',
    defaultView: 'dashboard',
  });

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await getUser();
      setUser(userData);
      setName(userData.name);
      setPreferences(userData.preferences);
    } catch (err) {
      setError('Failed to load user data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updatedUser = await updateUser({ name, preferences });
      setUser(updatedUser);
      setSuccessMessage('Profile updated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save changes');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarUpload = async (file: File) => {
    const result = await uploadAvatar(file);
    setUser((prev) => (prev ? { ...prev, avatar: result.url } : null));
  };

  const updatePreference = <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
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

      {/* Profile Section */}
      <SettingsSection
        title="Profile"
        description="Manage your personal information"
      >
        <div className="space-y-6">
          {/* Avatar */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Profile Photo
            </label>
            <AvatarUpload
              currentAvatar={user?.avatar}
              name={name || 'User'}
              onUpload={handleAvatarUpload}
              size="lg"
            />
          </div>

          {/* Name */}
          <FormField label="Full Name" htmlFor="name" required>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </FormField>

          {/* Email (read-only) */}
          <FormField
            label="Email Address"
            htmlFor="email"
            hint="Contact support to change your email address"
          >
            <input
              id="email"
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full max-w-md px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </FormField>

          {/* Role (read-only) */}
          <FormField label="Role" htmlFor="role">
            <input
              id="role"
              type="text"
              value={user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : ''}
              disabled
              className="w-full max-w-md px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </FormField>
        </div>
      </SettingsSection>

      {/* Preferences Section */}
      <SettingsSection
        title="Preferences"
        description="Customize your Sales OS experience"
      >
        <div className="space-y-6">
          {/* Theme */}
          <FormField label="Theme" htmlFor="theme">
            <select
              id="theme"
              value={preferences.theme}
              onChange={(e) =>
                updatePreference('theme', e.target.value as UserPreferences['theme'])
              }
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="system">System</option>
            </select>
          </FormField>

          {/* Timezone */}
          <FormField label="Timezone" htmlFor="timezone">
            <select
              id="timezone"
              value={preferences.timezone}
              onChange={(e) => updatePreference('timezone', e.target.value)}
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {timezones.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
          </FormField>

          {/* Date Format */}
          <FormField label="Date Format" htmlFor="dateFormat">
            <select
              id="dateFormat"
              value={preferences.dateFormat}
              onChange={(e) => updatePreference('dateFormat', e.target.value)}
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {dateFormats.map((fmt) => (
                <option key={fmt.value} value={fmt.value}>
                  {fmt.label}
                </option>
              ))}
            </select>
          </FormField>

          {/* Default View */}
          <FormField
            label="Default View"
            htmlFor="defaultView"
            hint="The page to show when you first log in"
          >
            <select
              id="defaultView"
              value={preferences.defaultView}
              onChange={(e) =>
                updatePreference(
                  'defaultView',
                  e.target.value as UserPreferences['defaultView']
                )
              }
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {defaultViews.map((view) => (
                <option key={view.value} value={view.value}>
                  {view.label}
                </option>
              ))}
            </select>
          </FormField>
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
      </div>
    </div>
  );
}
