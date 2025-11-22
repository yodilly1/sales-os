'use client';

import { useState } from 'react';
import { Button, Input, Textarea, Select } from '@/components/ui';
import { ContentTypeSelector, ContentType } from './ContentTypeSelector';

export interface ContentFormData {
  contentType: ContentType;
  goal: string;
  productName: string;
  productDescription: string;
  keyFeatures: string;
  targetAudience: string;
  audienceRole: string;
  industryFocus: string;
  painPoints: string;
  competitorName?: string;
  competitorWeaknesses?: string;
  tone: string;
}

interface ContentFormProps {
  onSubmit: (data: ContentFormData) => void;
  isLoading?: boolean;
}

const STEPS = ['Content Type', 'Product Info', 'Audience', 'Review'];

const toneOptions = [
  { value: 'professional', label: 'Professional' },
  { value: 'conversational', label: 'Conversational' },
  { value: 'technical', label: 'Technical' },
  { value: 'persuasive', label: 'Persuasive' },
  { value: 'executive', label: 'Executive' },
];

const industryOptions = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'finance', label: 'Finance & Banking' },
  { value: 'retail', label: 'Retail & E-commerce' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'saas', label: 'SaaS' },
  { value: 'consulting', label: 'Consulting' },
  { value: 'other', label: 'Other' },
];

export function ContentForm({ onSubmit, isLoading = false }: ContentFormProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Partial<ContentFormData>>({
    tone: 'professional',
    industryFocus: 'technology',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof ContentFormData, string>>>({});

  const updateField = <K extends keyof ContentFormData>(
    field: K,
    value: ContentFormData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Partial<Record<keyof ContentFormData, string>> = {};

    switch (step) {
      case 0:
        if (!formData.contentType) {
          newErrors.contentType = 'Please select a content type';
        }
        break;
      case 1:
        if (!formData.goal?.trim()) {
          newErrors.goal = 'Goal is required';
        }
        if (!formData.productName?.trim()) {
          newErrors.productName = 'Product name is required';
        }
        if (!formData.productDescription?.trim()) {
          newErrors.productDescription = 'Product description is required';
        }
        break;
      case 2:
        if (!formData.targetAudience?.trim()) {
          newErrors.targetAudience = 'Target audience is required';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
    }
  };

  const handlePrevious = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const handleSubmit = () => {
    if (validateStep(currentStep)) {
      onSubmit(formData as ContentFormData);
    }
  };

  const renderStepIndicator = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => (
          <div key={step} className="flex items-center">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors ${
                index < currentStep
                  ? 'bg-brand-600 text-white'
                  : index === currentStep
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {index < currentStep ? (
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`ml-2 text-sm font-medium ${
                index === currentStep ? 'text-gray-900' : 'text-gray-500'
              }`}
            >
              {step}
            </span>
            {index < STEPS.length - 1 && (
              <div
                className={`mx-4 h-0.5 w-12 sm:w-24 ${
                  index < currentStep ? 'bg-brand-600' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="form-step">
            <ContentTypeSelector
              selectedType={formData.contentType || null}
              onSelect={(type) => updateField('contentType', type)}
            />
            {errors.contentType && (
              <p className="mt-2 text-sm text-error-600">{errors.contentType}</p>
            )}
          </div>
        );

      case 1:
        return (
          <div className="form-step">
            <h2 className="text-lg font-semibold text-gray-900">Product Information</h2>
            <p className="mt-1 text-sm text-gray-500">
              Tell us about your product and what you want to achieve
            </p>
            <div className="mt-6 space-y-4">
              <Textarea
                label="What's your goal for this content?"
                placeholder="e.g., Close a deal with a Fortune 500 company, introduce our new feature..."
                value={formData.goal || ''}
                onChange={(e) => updateField('goal', e.target.value)}
                error={errors.goal}
                rows={3}
              />
              <Input
                label="Product Name"
                placeholder="e.g., Sales OS"
                value={formData.productName || ''}
                onChange={(e) => updateField('productName', e.target.value)}
                error={errors.productName}
              />
              <Textarea
                label="Product Description"
                placeholder="Describe what your product does and its main value proposition..."
                value={formData.productDescription || ''}
                onChange={(e) => updateField('productDescription', e.target.value)}
                error={errors.productDescription}
                rows={4}
              />
              <Textarea
                label="Key Features & Benefits"
                placeholder="List the key features and benefits (one per line)..."
                value={formData.keyFeatures || ''}
                onChange={(e) => updateField('keyFeatures', e.target.value)}
                hint="Separate each feature with a new line"
                rows={4}
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="form-step">
            <h2 className="text-lg font-semibold text-gray-900">Target Audience</h2>
            <p className="mt-1 text-sm text-gray-500">
              Define who will be reading this content
            </p>
            <div className="mt-6 space-y-4">
              <Input
                label="Target Company / Audience"
                placeholder="e.g., Enterprise SaaS companies, Mid-market retailers..."
                value={formData.targetAudience || ''}
                onChange={(e) => updateField('targetAudience', e.target.value)}
                error={errors.targetAudience}
              />
              <Input
                label="Primary Role / Title"
                placeholder="e.g., VP of Sales, CTO, Product Manager..."
                value={formData.audienceRole || ''}
                onChange={(e) => updateField('audienceRole', e.target.value)}
              />
              <Select
                label="Industry Focus"
                options={industryOptions}
                value={formData.industryFocus || 'technology'}
                onChange={(e) => updateField('industryFocus', e.target.value)}
              />
              <Textarea
                label="Pain Points to Address"
                placeholder="What problems does your audience face that your product solves?"
                value={formData.painPoints || ''}
                onChange={(e) => updateField('painPoints', e.target.value)}
                rows={3}
              />
              <Select
                label="Tone"
                options={toneOptions}
                value={formData.tone || 'professional'}
                onChange={(e) => updateField('tone', e.target.value)}
              />
              {formData.contentType === 'battlecard' && (
                <>
                  <Input
                    label="Competitor Name"
                    placeholder="e.g., Competitor XYZ"
                    value={formData.competitorName || ''}
                    onChange={(e) => updateField('competitorName', e.target.value)}
                  />
                  <Textarea
                    label="Competitor Weaknesses"
                    placeholder="What are the key weaknesses of this competitor?"
                    value={formData.competitorWeaknesses || ''}
                    onChange={(e) => updateField('competitorWeaknesses', e.target.value)}
                    rows={3}
                  />
                </>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="form-step">
            <h2 className="text-lg font-semibold text-gray-900">Review & Generate</h2>
            <p className="mt-1 text-sm text-gray-500">
              Review your inputs before generating content
            </p>
            <div className="mt-6 space-y-4">
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Content Type</dt>
                    <dd className="mt-1 text-sm text-gray-900 capitalize">
                      {formData.contentType?.replace('-', ' ')}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Goal</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formData.goal}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Product</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formData.productName}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Target Audience</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {formData.targetAudience}
                      {formData.audienceRole && ` (${formData.audienceRole})`}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Tone</dt>
                    <dd className="mt-1 text-sm text-gray-900 capitalize">{formData.tone}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      {renderStepIndicator()}
      <div className="min-h-[400px]">{renderStep()}</div>
      <div className="mt-8 flex items-center justify-between border-t border-gray-200 pt-6">
        <Button
          variant="ghost"
          onClick={handlePrevious}
          disabled={currentStep === 0}
        >
          Previous
        </Button>
        {currentStep < STEPS.length - 1 ? (
          <Button onClick={handleNext}>Continue</Button>
        ) : (
          <Button onClick={handleSubmit} loading={isLoading}>
            Generate Content
          </Button>
        )}
      </div>
    </div>
  );
}
