'use client'

import { useState, useEffect } from 'react'
import {
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Pause,
  X,
} from 'lucide-react'
import type { EnrichmentBatch, EnrichmentProgress, BatchStatus } from '@/types'
import { cn, formatDateTime, formatTimeAgo } from '@/lib/utils'

interface EnrichmentQueueProps {
  batches: EnrichmentBatch[]
  getProgress?: (batchId: string) => Promise<EnrichmentProgress>
  onCancel?: (batchId: string) => void
  onViewResults?: (batchId: string) => void
  pollInterval?: number
}

function BatchStatusIcon({ status }: { status: BatchStatus }) {
  switch (status) {
    case 'queued':
      return <Clock className="w-5 h-5 text-gray-400" />
    case 'processing':
      return <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-success-600" />
    case 'failed':
      return <XCircle className="w-5 h-5 text-error-600" />
    case 'cancelled':
      return <X className="w-5 h-5 text-gray-400" />
    default:
      return null
  }
}

function BatchStatusBadge({ status }: { status: BatchStatus }) {
  const config: Record<BatchStatus, { label: string; className: string }> = {
    queued: { label: 'Queued', className: 'badge-gray' },
    processing: { label: 'Processing', className: 'badge-primary' },
    completed: { label: 'Completed', className: 'badge-success' },
    failed: { label: 'Failed', className: 'badge-error' },
    cancelled: { label: 'Cancelled', className: 'badge-gray' },
  }

  return <span className={config[status].className}>{config[status].label}</span>
}

interface BatchItemProps {
  batch: EnrichmentBatch
  progress?: EnrichmentProgress | null
  onCancel?: () => void
  onViewResults?: () => void
}

function BatchItem({ batch, progress, onCancel, onViewResults }: BatchItemProps) {
  const [isExpanded, setIsExpanded] = useState(batch.status === 'processing')

  const currentProgress = progress || {
    completedCount: batch.completedCount,
    failedCount: batch.failedCount,
    totalCount: batch.totalCount,
    currentProspect: null,
    estimatedTimeRemaining: null,
    errors: [],
  }

  const progressPercent =
    currentProgress.totalCount > 0
      ? Math.round((currentProgress.completedCount / currentProgress.totalCount) * 100)
      : 0

  const formatTimeRemaining = (seconds: number | null) => {
    if (!seconds) return null
    if (seconds < 60) return `${seconds}s remaining`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m remaining`
    return `${Math.round(seconds / 3600)}h remaining`
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <BatchStatusIcon status={batch.status} />
          <div>
            <h4 className="font-medium text-gray-900">{batch.name}</h4>
            <p className="text-sm text-gray-500">
              {batch.totalCount} prospects • {formatTimeAgo(batch.createdAt)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <BatchStatusBadge status={batch.status} />
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {batch.status === 'processing' && (
        <div className="px-4 pb-2">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-600">
              {currentProgress.completedCount} of {currentProgress.totalCount}
            </span>
            <span className="text-gray-500">
              {formatTimeRemaining(currentProgress.estimatedTimeRemaining) || `${progressPercent}%`}
            </span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50 space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-semibold text-gray-900">
                {currentProgress.completedCount}
              </p>
              <p className="text-xs text-gray-500">Completed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-error-600">
                {currentProgress.failedCount}
              </p>
              <p className="text-xs text-gray-500">Failed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-gray-400">
                {currentProgress.totalCount -
                  currentProgress.completedCount -
                  currentProgress.failedCount}
              </p>
              <p className="text-xs text-gray-500">Remaining</p>
            </div>
          </div>

          {/* Current Prospect */}
          {batch.status === 'processing' && currentProgress.currentProspect && (
            <div className="p-2 bg-white rounded border border-gray-200">
              <p className="text-xs text-gray-500">Currently enriching:</p>
              <p className="text-sm font-medium text-gray-900">
                {currentProgress.currentProspect}
              </p>
            </div>
          )}

          {/* Errors */}
          {progress?.errors && progress.errors.length > 0 && (
            <div className="p-3 bg-error-50 rounded-lg">
              <h5 className="text-sm font-medium text-error-800 flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4" />
                Recent Errors
              </h5>
              <div className="space-y-1">
                {progress.errors.slice(0, 3).map((error, idx) => (
                  <p key={idx} className="text-sm text-error-700">
                    <span className="font-medium">{error.prospectName}:</span> {error.error}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Timestamps */}
          <div className="text-xs text-gray-500 space-y-1">
            <p>Created: {formatDateTime(batch.createdAt)}</p>
            {batch.completedAt && <p>Completed: {formatDateTime(batch.completedAt)}</p>}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            {batch.status === 'processing' && onCancel && (
              <button onClick={onCancel} className="btn-secondary text-sm flex items-center gap-1">
                <Pause className="w-4 h-4" />
                Cancel
              </button>
            )}
            {(batch.status === 'completed' || batch.status === 'failed') && onViewResults && (
              <button onClick={onViewResults} className="btn-primary text-sm">
                View Results
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function EnrichmentQueue({
  batches,
  getProgress,
  onCancel,
  onViewResults,
  pollInterval = 3000,
}: EnrichmentQueueProps) {
  const [progressMap, setProgressMap] = useState<Map<string, EnrichmentProgress>>(new Map())

  // Poll progress for processing batches
  useEffect(() => {
    if (!getProgress) return

    const processingBatches = batches.filter((b) => b.status === 'processing')
    if (processingBatches.length === 0) return

    const fetchProgress = async () => {
      const updates = await Promise.all(
        processingBatches.map(async (batch) => {
          try {
            const progress = await getProgress(batch.id)
            return { batchId: batch.id, progress }
          } catch {
            return null
          }
        })
      )

      setProgressMap((prev) => {
        const next = new Map(prev)
        updates.forEach((update) => {
          if (update) {
            next.set(update.batchId, update.progress)
          }
        })
        return next
      })
    }

    fetchProgress()
    const interval = setInterval(fetchProgress, pollInterval)

    return () => clearInterval(interval)
  }, [batches, getProgress, pollInterval])

  if (batches.length === 0) {
    return (
      <div className="card p-8 text-center">
        <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No Enrichment Batches</h3>
        <p className="text-sm text-gray-500">
          Upload a CSV file or run a bulk lookup to start enriching prospects.
        </p>
      </div>
    )
  }

  // Group batches by status
  const processingBatches = batches.filter((b) => b.status === 'processing')
  const queuedBatches = batches.filter((b) => b.status === 'queued')
  const completedBatches = batches.filter(
    (b) => b.status === 'completed' || b.status === 'failed' || b.status === 'cancelled'
  )

  return (
    <div className="space-y-6">
      {/* Processing */}
      {processingBatches.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
            Processing ({processingBatches.length})
          </h3>
          <div className="space-y-3">
            {processingBatches.map((batch) => (
              <BatchItem
                key={batch.id}
                batch={batch}
                progress={progressMap.get(batch.id)}
                onCancel={onCancel ? () => onCancel(batch.id) : undefined}
                onViewResults={onViewResults ? () => onViewResults(batch.id) : undefined}
              />
            ))}
          </div>
        </div>
      )}

      {/* Queued */}
      {queuedBatches.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            Queued ({queuedBatches.length})
          </h3>
          <div className="space-y-3">
            {queuedBatches.map((batch) => (
              <BatchItem
                key={batch.id}
                batch={batch}
                onCancel={onCancel ? () => onCancel(batch.id) : undefined}
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed */}
      {completedBatches.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-success-600" />
            Completed ({completedBatches.length})
          </h3>
          <div className="space-y-3">
            {completedBatches.map((batch) => (
              <BatchItem
                key={batch.id}
                batch={batch}
                onViewResults={onViewResults ? () => onViewResults(batch.id) : undefined}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EnrichmentQueue
