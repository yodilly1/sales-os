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
      </div>
    </div>
  );
}
