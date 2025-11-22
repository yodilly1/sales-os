'use client';

import { useState, useEffect } from 'react';
import { SettingsSection, FormField, AvatarUpload, Toggle } from '@/components/settings';
import type { Organization, OrganizationDefaults } from '@/lib/types/settings';
import { getOrganization, updateOrganization, uploadOrganizationLogo } from '@/lib/api/settings';

const contentTones = [
  { value: 'formal', label: 'Formal', description: 'Professional and business-oriented language' },
  { value: 'casual', label: 'Casual', description: 'Friendly and conversational tone' },
  { value: 'professional', label: 'Professional', description: 'Balanced and polished communication' },
];

const spicedMethodologies = [
  { value: 'standard', label: 'Standard SPICED', description: 'Use the standard Winning by Design SPICED framework' },
  { value: 'custom', label: 'Custom SPICED', description: 'Customized SPICED criteria for your organization' },
];

export default function OrganizationSettingsPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#3B82F6');
  const [secondaryColor, setSecondaryColor] = useState('#1E40AF');
  const [defaults, setDefaults] = useState<OrganizationDefaults>({
    spicedMethodology: 'standard',
    contentTone: 'professional',
    enrichmentProvider: 'default',
    crmSyncEnabled: true,
    autoAnalyzeTranscripts: true,
  });

  useEffect(() => {
    loadOrganization();
  }, []);

  const loadOrganization = async () => {
    try {
      const orgData = await getOrganization();
      setOrg(orgData);
      setName(orgData.name);
      setPrimaryColor(orgData.primaryColor || '#3B82F6');
      setSecondaryColor(orgData.secondaryColor || '#1E40AF');
      setDefaults(orgData.defaults);
    } catch (err) {
      setError('Failed to load organization data');
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
      const updatedOrg = await updateOrganization({
        name,
        primaryColor,
        secondaryColor,
        defaults,
      });
      setOrg(updatedOrg);
      setSuccessMessage('Organization settings updated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save changes');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogoUpload = async (file: File) => {
    const result = await uploadOrganizationLogo(file);
    setOrg((prev) => (prev ? { ...prev, logo: result.url } : null));
  };

  const updateDefault = <K extends keyof OrganizationDefaults>(
    key: K,
    value: OrganizationDefaults[K]
  ) => {
    setDefaults((prev) => ({ ...prev, [key]: value }));
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

      {/* General Section */}
      <SettingsSection
        title="General"
        description="Manage your organization's basic information"
      >
        <div className="space-y-6">
          {/* Logo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Organization Logo
            </label>
            <AvatarUpload
              currentAvatar={org?.logo}
              name={name || 'Organization'}
              onUpload={handleLogoUpload}
              size="lg"
            />
          </div>

          {/* Name */}
          <FormField label="Organization Name" htmlFor="orgName" required>
            <input
              id="orgName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </FormField>

          {/* Slug (read-only) */}
          <FormField
            label="Organization Slug"
            htmlFor="slug"
            hint="Used in URLs and API calls"
          >
            <input
              id="slug"
              type="text"
              value={org?.slug || ''}
              disabled
              className="w-full max-w-md px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
          </FormField>
        </div>
      </SettingsSection>

      {/* Branding Section */}
      <SettingsSection
        title="Branding"
        description="Customize the look and feel of your generated content"
      >
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Primary Color */}
            <FormField label="Primary Color" htmlFor="primaryColor">
              <div className="flex items-center gap-3">
                <input
                  id="primaryColor"
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="h-10 w-16 rounded border border-gray-300 cursor-pointer"
                />
                <input
                  type="text"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  pattern="^#[0-9A-Fa-f]{6}$"
                  className="flex-1 max-w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
                />
              </div>
            </FormField>

            {/* Secondary Color */}
            <FormField label="Secondary Color" htmlFor="secondaryColor">
              <div className="flex items-center gap-3">
                <input
                  id="secondaryColor"
                  type="color"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  className="h-10 w-16 rounded border border-gray-300 cursor-pointer"
                />
                <input
                  type="text"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  pattern="^#[0-9A-Fa-f]{6}$"
                  className="flex-1 max-w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
                />
              </div>
            </FormField>
          </div>

          {/* Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Color Preview
            </label>
            <div className="flex gap-4">
              <div
                className="w-24 h-24 rounded-lg shadow-sm flex items-center justify-center text-white text-sm font-medium"
                style={{ backgroundColor: primaryColor }}
              >
                Primary
              </div>
              <div
                className="w-24 h-24 rounded-lg shadow-sm flex items-center justify-center text-white text-sm font-medium"
                style={{ backgroundColor: secondaryColor }}
              >
                Secondary
              </div>
            </div>
          </div>
        </div>
      </SettingsSection>

      {/* Defaults Section */}
      <SettingsSection
        title="Defaults"
        description="Configure default settings for your organization"
      >
        <div className="space-y-6">
          {/* SPICED Methodology */}
          <FormField label="SPICED Methodology">
            <div className="space-y-2 max-w-md">
              {spicedMethodologies.map((method) => (
                <label
                  key={method.value}
                  className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                    defaults.spicedMethodology === method.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="spicedMethodology"
                    value={method.value}
                    checked={defaults.spicedMethodology === method.value}
                    onChange={(e) =>
                      updateDefault(
                        'spicedMethodology',
                        e.target.value as OrganizationDefaults['spicedMethodology']
                      )
                    }
                    className="mt-1"
                  />
                  <div>
                    <span className="font-medium text-gray-900">{method.label}</span>
                    <p className="text-sm text-gray-500">{method.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </FormField>

          {/* Content Tone */}
          <FormField label="Default Content Tone" htmlFor="contentTone">
            <select
              id="contentTone"
              value={defaults.contentTone}
              onChange={(e) =>
                updateDefault(
                  'contentTone',
                  e.target.value as OrganizationDefaults['contentTone']
                )
              }
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {contentTones.map((tone) => (
                <option key={tone.value} value={tone.value}>
                  {tone.label} - {tone.description}
                </option>
              ))}
            </select>
          </FormField>

          {/* Toggles */}
          <div className="space-y-4 pt-4 border-t border-gray-200">
            <Toggle
              enabled={defaults.crmSyncEnabled}
              onChange={(value) => updateDefault('crmSyncEnabled', value)}
              label="Enable CRM Sync"
              description="Automatically sync data with connected CRM (HubSpot)"
            />

            <Toggle
              enabled={defaults.autoAnalyzeTranscripts}
              onChange={(value) => updateDefault('autoAnalyzeTranscripts', value)}
              label="Auto-analyze Transcripts"
              description="Automatically run SPICED analysis on new transcripts"
            />
          </div>
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
