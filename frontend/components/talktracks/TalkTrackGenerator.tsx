'use client';

import { useState } from 'react';
import { generateTalkTrack } from '@/lib/api/talktracks';
import type { TalkTrack, TalkTrackRequest } from '@/lib/api/talktracks';

interface TalkTrackGeneratorProps {
  onGenerated: (talkTrack: TalkTrack) => void;
}

const SCRIPT_TYPES = [
  { value: 'discovery_call', label: 'Discovery Call', description: 'SPICED-aligned discovery with probing questions' },
  { value: 'demo_script', label: 'Demo Script', description: 'Value-focused demo connecting features to pain' },
  { value: 'objection_response', label: 'Objection Response', description: 'Playbook for handling common objections' },
  { value: 'closing_conversation', label: 'Closing Conversation', description: 'Framework for closing deals effectively' },
  { value: 'follow_up_guide', label: 'Follow-Up Guide', description: 'Multi-touch follow-up framework' },
];

const PERSONAS = [
  { value: 'executive', label: 'Executive' },
  { value: 'technical', label: 'Technical' },
  { value: 'financial', label: 'Financial' },
  { value: 'operations', label: 'Operations' },
  { value: 'end_user', label: 'End User' },
  { value: 'champion', label: 'Champion' },
  { value: 'economic_buyer', label: 'Economic Buyer' },
];

const INDUSTRIES = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'financial_services', label: 'Financial Services' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail' },
  { value: 'professional_services', label: 'Professional Services' },
  { value: 'education', label: 'Education' },
  { value: 'government', label: 'Government' },
  { value: 'media_entertainment', label: 'Media & Entertainment' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'other', label: 'Other' },
];

const DEAL_STAGES = [
  { value: 'prospecting', label: 'Prospecting' },
  { value: 'qualification', label: 'Qualification' },
  { value: 'discovery', label: 'Discovery' },
  { value: 'demo', label: 'Demo' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'negotiation', label: 'Negotiation' },
];

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'consultative', label: 'Consultative' },
  { value: 'casual', label: 'Casual' },
  { value: 'urgent', label: 'Urgent' },
];

export function TalkTrackGenerator({ onGenerated }: TalkTrackGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [formData, setFormData] = useState<TalkTrackRequest>({
    script_type: 'discovery_call',
    persona: 'champion',
    industry: 'technology',
    deal_stage: 'discovery',
    tone: 'consultative',
    generate_variants: false,
    include_coaching_notes: true,
    prospect: {
      name: '',
      title: '',
      company: '',
      company_size: '',
      industry: 'technology',
      known_pain_points: [],
    },
    product: {
      name: '',
      key_features: [],
      value_propositions: [],
      differentiators: [],
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setError(null);

    try {
      const response = await generateTalkTrack(formData);
      onGenerated(response.primary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate talk track');
    } finally {
      setIsGenerating(false);
    }
  };

  const updateFormData = (field: string, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const updateProspect = (field: string, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      prospect: {
        ...prev.prospect,
        [field]: value,
      },
    }));
  };

  const updateProduct = (field: string, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      product: {
        ...prev.product,
        [field]: value,
      },
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <form onSubmit={handleSubmit}>
        {/* Script Type Selection */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Script Type</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {SCRIPT_TYPES.map((type) => (
              <label
                key={type.value}
                className={`
                  relative flex cursor-pointer rounded-lg border p-4 focus:outline-none
                  ${formData.script_type === type.value
                    ? 'border-blue-500 ring-2 ring-blue-500'
                    : 'border-gray-300 hover:border-gray-400'
                  }
                `}
              >
                <input
                  type="radio"
                  name="script_type"
                  value={type.value}
                  checked={formData.script_type === type.value}
                  onChange={(e) => updateFormData('script_type', e.target.value)}
                  className="sr-only"
                />
                <div className="flex flex-col">
                  <span className="block text-sm font-medium text-gray-900">
                    {type.label}
                  </span>
                  <span className="mt-1 text-xs text-gray-500">
                    {type.description}
                  </span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Basic Configuration */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Persona
              </label>
              <select
                value={formData.persona}
                onChange={(e) => updateFormData('persona', e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {PERSONAS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Industry
              </label>
              <select
                value={formData.industry}
                onChange={(e) => updateFormData('industry', e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {INDUSTRIES.map((i) => (
                  <option key={i.value} value={i.value}>{i.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Deal Stage
              </label>
              <select
                value={formData.deal_stage}
                onChange={(e) => updateFormData('deal_stage', e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {DEAL_STAGES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tone
              </label>
              <select
                value={formData.tone}
                onChange={(e) => updateFormData('tone', e.target.value)}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {TONES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Options */}
          <div className="mt-4 flex items-center gap-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.generate_variants}
                onChange={(e) => updateFormData('generate_variants', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Generate A/B variants</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.include_coaching_notes}
                onChange={(e) => updateFormData('include_coaching_notes', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Include coaching notes</span>
            </label>
          </div>
        </div>

        {/* Advanced Options */}
        <div className="p-6 border-b border-gray-200">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <span>{showAdvanced ? '▼' : '▶'}</span>
            Advanced Options (Optional)
          </button>

          {showAdvanced && (
            <div className="mt-4 space-y-6">
              {/* Prospect Context */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Prospect Context</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <input
                    type="text"
                    placeholder="Prospect Name"
                    value={formData.prospect?.name || ''}
                    onChange={(e) => updateProspect('name', e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Title"
                    value={formData.prospect?.title || ''}
                    onChange={(e) => updateProspect('title', e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Company"
                    value={formData.prospect?.company || ''}
                    onChange={(e) => updateProspect('company', e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Company Size"
                    value={formData.prospect?.company_size || ''}
                    onChange={(e) => updateProspect('company_size', e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div className="mt-2">
                  <input
                    type="text"
                    placeholder="Known Pain Points (comma-separated)"
                    value={formData.prospect?.known_pain_points?.join(', ') || ''}
                    onChange={(e) => updateProspect('known_pain_points', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Product Context */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Product Context</h3>
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Product Name"
                    value={formData.product?.name || ''}
                    onChange={(e) => updateProduct('name', e.target.value)}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Key Features (comma-separated)"
                    value={formData.product?.key_features?.join(', ') || ''}
                    onChange={(e) => updateProduct('key_features', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Value Propositions (comma-separated)"
                    value={formData.product?.value_propositions?.join(', ') || ''}
                    onChange={(e) => updateProduct('value_propositions', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 mx-6 mt-6 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Submit Button */}
        <div className="p-6">
          <button
            type="submit"
            disabled={isGenerating}
            className={`
              w-full py-3 px-4 rounded-md font-medium text-white
              ${isGenerating
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
              }
            `}
          >
            {isGenerating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Generating Talk Track...
              </span>
            ) : (
              'Generate Talk Track'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
