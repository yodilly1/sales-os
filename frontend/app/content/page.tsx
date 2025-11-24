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
import { contentApi } from '@/lib/api/content';

const GENERATION_STEPS = [
  'Connecting to AI service...',
  'Analyzing your inputs...',
  'Generating content with Claude AI...',
  'Processing response...',
  'Finalizing content...',
];

export default function ContentPage() {
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [showForm, setShowForm] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = useCallback(async (formData: ContentFormData) => {
    setIsGenerating(true);
    setProgress(0);
    setGeneratedContent(null);
    setShowForm(false);
    setError(null);

    // Start progress animation - updates every 3 seconds during real API call
    let stepIndex = 0;
    const progressInterval = setInterval(() => {
      if (stepIndex < GENERATION_STEPS.length - 1) {
        stepIndex++;
        setCurrentStep(GENERATION_STEPS[stepIndex]);
        setProgress(((stepIndex + 1) / GENERATION_STEPS.length) * 80); // Max 80% during generation
      }
    }, 3000);

    // Set initial step
    setCurrentStep(GENERATION_STEPS[0]);
    setProgress(10);

    try {
      // Call the real backend API
      const content = await contentApi.generateContent(formData);

      // Clear progress interval and set to complete
      clearInterval(progressInterval);
      setCurrentStep(GENERATION_STEPS[GENERATION_STEPS.length - 1]);
      setProgress(100);

      // Short delay to show completion
      await new Promise((resolve) => setTimeout(resolve, 500));

      setGeneratedContent(content);
    } catch (err) {
      clearInterval(progressInterval);
      console.error('Content generation failed:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to generate content. Please check your connection and try again.'
      );
      setShowForm(true);
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const handleExport = async (format: ExportFormat) => {
    if (!generatedContent) return;

    try {
      switch (format) {
        case 'pdf':
          // For now, create a simple text file download
          const pdfContent = generatedContent.sections
            .map((s) => `# ${s.title}\n\n${s.content}`)
            .join('\n\n---\n\n');
          const pdfBlob = new Blob([`# ${generatedContent.title}\n\n${pdfContent}`], { type: 'text/plain' });
          const pdfUrl = URL.createObjectURL(pdfBlob);
          const pdfLink = document.createElement('a');
          pdfLink.href = pdfUrl;
          pdfLink.download = `${generatedContent.title.replace(/\s+/g, '-')}.txt`;
          pdfLink.click();
          URL.revokeObjectURL(pdfUrl);
          break;

        case 'pptx':
          // For now, create a markdown file that can be converted to slides
          const slideContent = generatedContent.sections
            .map((s, i) => `---\n\n# Slide ${i + 1}: ${s.title}\n\n${s.content}`)
            .join('\n\n');
          const pptxBlob = new Blob([`# ${generatedContent.title}\n${slideContent}`], { type: 'text/markdown' });
          const pptxUrl = URL.createObjectURL(pptxBlob);
          const pptxLink = document.createElement('a');
          pptxLink.href = pptxUrl;
          pptxLink.download = `${generatedContent.title.replace(/\s+/g, '-')}-slides.md`;
          pptxLink.click();
          URL.revokeObjectURL(pptxUrl);
          break;

        case 'link':
          // Copy a shareable link
          await navigator.clipboard.writeText(
            `${window.location.origin}/content/${generatedContent.id}`
          );
          break;

        case 'copy':
          // Copy content as plain text
          const textContent = `${generatedContent.title}\n\n` + generatedContent.sections
            .map((s) => `${s.title}\n${s.content}`)
            .join('\n\n');
          await navigator.clipboard.writeText(textContent);
          break;
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleReset = () => {
    setGeneratedContent(null);
    setShowForm(true);
    setProgress(0);
    setCurrentStep('');
    setError(null);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Content Generator</h1>
          <p className="mt-1 text-sm text-gray-500">
            Create professional sales content powered by Claude AI
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

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
                    onSubmit={handleGenerate}
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
                      <div className="text-center">
                        <p className="text-sm text-gray-500">
                          Your content is being generated by Claude AI.
                        </p>
                        <p className="mt-1 text-xs text-gray-400">
                          This typically takes 10-30 seconds...
                        </p>
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
