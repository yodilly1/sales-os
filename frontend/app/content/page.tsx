'use client';

import { useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent, Button } from '@/components/ui';
import {
  ContentForm,
  ContentFormData,
  ContentPreview,
  GeneratedContent,
  ExportMenu,
  ExportFormat,
} from '@/components/content';
import { generateMockContent } from '@/lib/api/content';

const GENERATION_STEPS = [
  'Analyzing your inputs...',
  'Crafting content structure...',
  'Generating compelling copy...',
  'Applying brand styling...',
  'Finalizing content...',
];

export default function ContentPage() {
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [showForm, setShowForm] = useState(true);

  const simulateGeneration = useCallback(async (formData: ContentFormData) => {
    setIsGenerating(true);
    setProgress(0);
    setGeneratedContent(null);
    setShowForm(false);

    // Simulate progressive generation with steps
    for (let i = 0; i < GENERATION_STEPS.length; i++) {
      setCurrentStep(GENERATION_STEPS[i]);
      setProgress(((i + 1) / GENERATION_STEPS.length) * 100);
      await new Promise((resolve) => setTimeout(resolve, 800));
    }

    // Generate mock content (in production, this would call the API)
    const content = generateMockContent(formData);
    setGeneratedContent(content);
    setIsGenerating(false);
  }, []);

  const handleExport = async (format: ExportFormat) => {
    if (!generatedContent) return;

    // Simulate export delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    switch (format) {
      case 'pdf':
        // In production, this would trigger a PDF download
        console.log('Exporting as PDF:', generatedContent.id);
        alert('PDF export would download here');
        break;
      case 'pptx':
        // In production, this would trigger a PPTX download
        console.log('Exporting as PPTX:', generatedContent.id);
        alert('PPTX export would download here');
        break;
      case 'link':
        // In production, this would generate a shareable link
        await navigator.clipboard.writeText(
          `${window.location.origin}/deck/${generatedContent.id}`
        );
        break;
      case 'copy':
        // Copy content as plain text
        const textContent = generatedContent.sections
          .map((s) => `${s.title}\n${s.content}`)
          .join('\n\n');
        await navigator.clipboard.writeText(textContent);
        break;
    }
  };

  const handleReset = () => {
    setGeneratedContent(null);
    setShowForm(true);
    setProgress(0);
    setCurrentStep('');
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Content Generator</h1>
          <p className="mt-1 text-sm text-gray-500">
            Create professional sales content powered by AI
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Panel - Form */}
          <div>
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>
                    {showForm ? 'Create Content' : 'Content Details'}
                  </CardTitle>
                  {!showForm && !isGenerating && (
                    <Button variant="ghost" size="sm" onClick={handleReset}>
                      <svg
                        className="mr-1.5 h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                        />
                      </svg>
                      New Content
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {showForm ? (
                  <ContentForm
                    onSubmit={simulateGeneration}
                    isLoading={isGenerating}
                  />
                ) : (
                  <div className="space-y-6">
                    {generatedContent && (
                      <>
                        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                          <h3 className="font-medium text-gray-900">
                            {generatedContent.title}
                          </h3>
                          {generatedContent.subtitle && (
                            <p className="mt-1 text-sm text-gray-500">
                              {generatedContent.subtitle}
                            </p>
                          )}
                          <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                            <span>
                              {generatedContent.sections.length} sections
                            </span>
                            <span>
                              Generated{' '}
                              {new Date(
                                generatedContent.generatedAt
                              ).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <ExportMenu
                            content={generatedContent}
                            onExport={handleExport}
                          />
                          <Button variant="outline" onClick={handleReset}>
                            Edit Inputs
                          </Button>
                        </div>
                      </>
                    )}
                    {isGenerating && (
                      <div className="text-center text-sm text-gray-500">
                        Your content is being generated. This may take a moment...
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Preview */}
          <div className="lg:sticky lg:top-24 lg:self-start">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Preview</CardTitle>
                  {generatedContent && !isGenerating && (
                    <div className="flex items-center gap-2">
                      <span className="flex h-2 w-2 rounded-full bg-success-500" />
                      <span className="text-xs text-gray-500">Ready</span>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[600px] overflow-hidden">
                  <ContentPreview
                    content={generatedContent}
                    isGenerating={isGenerating}
                    progress={progress}
                    currentStep={currentStep}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
