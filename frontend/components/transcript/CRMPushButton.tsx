'use client';

import { useState } from 'react';
import { ArrowUpRight, Check, AlertCircle, ExternalLink } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Modal, ModalFooter } from '@/components/common/Modal';
import { cn } from '@/lib/utils';
import { CRMStatus, CRMPushRequest, CRMPushResponse } from '@/lib/types';

interface CRMPushButtonProps {
  transcriptId: string;
  crmStatus: CRMStatus;
  crmRecordUrl?: string;
  onPush: (request: CRMPushRequest) => Promise<CRMPushResponse>;
  className?: string;
}

export function CRMPushButton({
  transcriptId,
  crmStatus,
  crmRecordUrl,
  onPush,
  className,
}: CRMPushButtonProps) {
  const [showModal, setShowModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<CRMPushResponse | null>(null);
  const [options, setOptions] = useState({
    includeNotes: true,
    includeTasks: true,
    includeAnalysis: true,
  });

  const handlePush = async () => {
    setIsLoading(true);
    setResult(null);

    try {
      const response = await onPush({
        transcriptId,
        ...options,
      });
      setResult(response);

      if (response.success) {
        // Auto-close after success
        setTimeout(() => {
          setShowModal(false);
          setResult(null);
        }, 3000);
      }
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to push to CRM',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Already synced - show link to CRM
  if (crmStatus === 'synced' && crmRecordUrl) {
    return (
      <a
        href={crmRecordUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          'inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
          'bg-success-50 text-success-700 hover:bg-success-100 transition-colors',
          className
        )}
      >
        <Check className="w-4 h-4" />
        Synced to HubSpot
        <ExternalLink className="w-4 h-4" />
      </a>
    );
  }

  return (
    <>
      <Button
        variant={crmStatus === 'failed' ? 'danger' : 'primary'}
        onClick={() => setShowModal(true)}
        leftIcon={
          crmStatus === 'failed' ? (
            <AlertCircle className="w-4 h-4" />
          ) : (
            <ArrowUpRight className="w-4 h-4" />
          )
        }
        className={className}
      >
        {crmStatus === 'failed' ? 'Retry CRM Push' : 'Push to HubSpot'}
      </Button>

      <Modal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setResult(null);
        }}
        title="Push to HubSpot"
        description="Sync this transcript data to your CRM"
        size="md"
      >
        {!result ? (
          <>
            <div className="space-y-4">
              <p className="text-sm text-neutral-600">
                Select what you want to sync to HubSpot:
              </p>

              <div className="space-y-3">
                <CheckboxOption
                  checked={options.includeNotes}
                  onChange={(checked) =>
                    setOptions((prev) => ({ ...prev, includeNotes: checked }))
                  }
                  label="Call Notes"
                  description="Add formatted notes as a HubSpot engagement"
                />

                <CheckboxOption
                  checked={options.includeTasks}
                  onChange={(checked) =>
                    setOptions((prev) => ({ ...prev, includeTasks: checked }))
                  }
                  label="Follow-up Tasks"
                  description="Create tasks in HubSpot for suggested follow-ups"
                />

                <CheckboxOption
                  checked={options.includeAnalysis}
                  onChange={(checked) =>
                    setOptions((prev) => ({ ...prev, includeAnalysis: checked }))
                  }
                  label="SPICED Analysis"
                  description="Store SPICED scores and insights on the deal"
                />
              </div>
            </div>

            <ModalFooter>
              <Button variant="secondary" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
              <Button
                onClick={handlePush}
                isLoading={isLoading}
                disabled={!options.includeNotes && !options.includeTasks && !options.includeAnalysis}
              >
                Push to HubSpot
              </Button>
            </ModalFooter>
          </>
        ) : (
          <div className="py-4">
            {result.success ? (
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-success-100 flex items-center justify-center mx-auto mb-4">
                  <Check className="w-6 h-6 text-success-600" />
                </div>
                <h3 className="font-semibold text-neutral-900 mb-2">
                  Successfully synced!
                </h3>
                <p className="text-sm text-neutral-600 mb-4">
                  Your data has been pushed to HubSpot.
                </p>
                {result.recordUrl && (
                  <a
                    href={result.recordUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                  >
                    View in HubSpot
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            ) : (
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-danger-100 flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="w-6 h-6 text-danger-600" />
                </div>
                <h3 className="font-semibold text-neutral-900 mb-2">
                  Sync failed
                </h3>
                <p className="text-sm text-danger-600 mb-4">
                  {result.error || 'An unexpected error occurred'}
                </p>
                <Button onClick={handlePush} variant="danger" isLoading={isLoading}>
                  Try Again
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}

interface CheckboxOptionProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description: string;
}

function CheckboxOption({
  checked,
  onChange,
  label,
  description,
}: CheckboxOptionProps) {
  return (
    <label className="flex items-start gap-3 p-3 rounded-lg border border-neutral-200 hover:bg-neutral-50 cursor-pointer transition-colors">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1 w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
      />
      <div>
        <p className="font-medium text-sm text-neutral-900">{label}</p>
        <p className="text-sm text-neutral-500">{description}</p>
      </div>
    </label>
  );
}
