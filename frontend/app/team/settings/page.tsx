'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api';
import type { Organization } from '@/types';

export default function SettingsPage() {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    primary_color: '',
  });

  useEffect(() => {
    api.loadTokenFromStorage();
    fetchOrganization();
  }, []);

  const fetchOrganization = async () => {
    try {
      setIsLoading(true);
      const org = await api.getCurrentOrganization();
      setOrganization(org);
      setFormData({
        name: org.name,
        description: org.description || '',
        primary_color: org.primary_color || '',
      });
    } catch (err) {
      setError('Failed to load organization settings');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!organization) return;

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await api.updateOrganization(organization.id, formData);
      setSuccess('Settings saved successfully');
      fetchOrganization();
    } catch (err) {
      setError('Failed to save settings');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error || 'Organization not found'}
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900">
          Organization Settings
        </h2>
        <p className="text-sm text-gray-500">
          Configure your organization's profile and preferences
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6">
        <div className="space-y-6">
          <Input
            id="name"
            label="Organization Name"
            value={formData.name}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, name: e.target.value }))
            }
            required
          />

          <div>
            <label htmlFor="description" className="label">
              Description
            </label>
            <textarea
              id="description"
              className="input min-h-[100px]"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              placeholder="Tell us about your organization..."
            />
          </div>

          <Input
            id="primary_color"
            label="Primary Brand Color"
            type="text"
            value={formData.primary_color}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, primary_color: e.target.value }))
            }
            placeholder="#0ea5e9"
            pattern="^#[0-9A-Fa-f]{6}$"
            title="Enter a valid hex color (e.g., #0ea5e9)"
          />

          {/* Organization Info (Read-only) */}
          <div className="pt-6 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-4">
              Organization Info
            </h3>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-gray-500">Slug</dt>
                <dd className="font-medium">{organization.slug}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Plan</dt>
                <dd className="font-medium capitalize">{organization.plan}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Max Users</dt>
                <dd className="font-medium">{organization.max_users}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Max Teams</dt>
                <dd className="font-medium">{organization.max_teams}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <Button type="submit" isLoading={isSaving}>
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
}
