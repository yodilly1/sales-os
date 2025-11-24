'use client'

import { Mail, Phone, MapPin, Linkedin, Building2, Briefcase, RefreshCw, ExternalLink, Sparkles } from 'lucide-react'
import type { Prospect, Company, EnrichmentStatus, CRMSyncStatus } from '@/types'
import { cn, formatDateTime, getInitials } from '@/lib/utils'

interface ProspectCardProps {
  prospect: Prospect
  company?: Company | null
  onReEnrich?: (prospectId: string) => void
  onSyncCRM?: (prospectId: string) => void
  onGenerateOutreach?: (prospectId: string) => void
  isReEnriching?: boolean
  showOutreachButton?: boolean
}

function EnrichmentStatusBadge({ status }: { status: EnrichmentStatus }) {
  const statusConfig: Record<EnrichmentStatus, { label: string; className: string }> = {
    pending: { label: 'Pending', className: 'badge-gray' },
    in_progress: { label: 'Enriching...', className: 'badge-primary' },
    completed: { label: 'Enriched', className: 'badge-success' },
    failed: { label: 'Failed', className: 'badge-error' },
    partial: { label: 'Partial', className: 'badge-warning' },
  }

  const config = statusConfig[status]
  return <span className={config.className}>{config.label}</span>
}

function CRMSyncBadge({ status }: { status: CRMSyncStatus }) {
  const statusConfig: Record<CRMSyncStatus, { label: string; className: string }> = {
    not_synced: { label: 'Not Synced', className: 'badge-gray' },
    synced: { label: 'Synced', className: 'badge-success' },
    pending: { label: 'Syncing...', className: 'badge-primary' },
    failed: { label: 'Sync Failed', className: 'badge-error' },
    out_of_sync: { label: 'Out of Sync', className: 'badge-warning' },
  }

  const config = statusConfig[status]
  return <span className={config.className}>{config.label}</span>
}

export function ProspectCard({
  prospect,
  company,
  onReEnrich,
  onSyncCRM,
  onGenerateOutreach,
  isReEnriching,
  showOutreachButton = true,
}: ProspectCardProps) {
  const initials = getInitials(prospect.name)

  return (
    <div className="card">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-lg font-semibold text-primary-700">{initials}</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{prospect.name}</h3>
              {prospect.title && (
                <p className="text-sm text-gray-600 flex items-center gap-1">
                  <Briefcase className="w-3.5 h-3.5" />
                  {prospect.title}
                </p>
              )}
              {prospect.company && (
                <p className="text-sm text-gray-600 flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5" />
                  {prospect.company}
                </p>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <EnrichmentStatusBadge status={prospect.enrichmentStatus} />
            <CRMSyncBadge status={prospect.crmSyncStatus} />
          </div>
        </div>

        {/* Contact Info */}
        <div className="space-y-2 mb-4">
          {prospect.email && (
            <div className="flex items-center gap-2 text-sm">
              <Mail className="w-4 h-4 text-gray-400" />
              <a href={`mailto:${prospect.email}`} className="text-primary-600 hover:underline">
                {prospect.email}
              </a>
              {prospect.enrichmentData?.verifiedEmail && (
                <span className="text-xs text-success-600 bg-success-50 px-1.5 py-0.5 rounded">
                  Verified
                </span>
              )}
            </div>
          )}
          {prospect.phone && (
            <div className="flex items-center gap-2 text-sm">
              <Phone className="w-4 h-4 text-gray-400" />
              <a href={`tel:${prospect.phone}`} className="text-gray-900 hover:text-primary-600">
                {prospect.phone}
              </a>
            </div>
          )}
          {prospect.location && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4 text-gray-400" />
              {prospect.location}
            </div>
          )}
          {prospect.linkedinUrl && (
            <div className="flex items-center gap-2 text-sm">
              <Linkedin className="w-4 h-4 text-gray-400" />
              <a
                href={prospect.linkedinUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline flex items-center gap-1"
              >
                LinkedIn Profile
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>

        {/* LinkedIn Profile Info */}
        {prospect.enrichmentData?.linkedinProfile && (
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              LinkedIn Insights
            </h4>
            {prospect.enrichmentData.linkedinProfile.headline && (
              <p className="text-sm text-gray-700 mb-1">
                {prospect.enrichmentData.linkedinProfile.headline}
              </p>
            )}
            {prospect.enrichmentData.linkedinProfile.connections && (
              <p className="text-xs text-gray-500">
                {prospect.enrichmentData.linkedinProfile.connections.toLocaleString()} connections
              </p>
            )}
          </div>
        )}

        {/* Recent Activity */}
        {prospect.enrichmentData?.recentActivity && prospect.enrichmentData.recentActivity.length > 0 && (
          <div className="mb-4">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              Recent Activity
            </h4>
            <div className="space-y-2">
              {prospect.enrichmentData.recentActivity.slice(0, 3).map((activity, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm">
                  <span className="flex-shrink-0 w-1.5 h-1.5 mt-1.5 bg-primary-500 rounded-full" />
                  <div>
                    <p className="text-gray-700">{activity.title}</p>
                    <p className="text-xs text-gray-500">
                      {activity.source} • {activity.date}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence Score */}
        {prospect.enrichmentData?.confidence !== undefined && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Data Confidence</span>
              <span className="font-medium">{prospect.enrichmentData.confidence}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  prospect.enrichmentData.confidence >= 80
                    ? 'bg-success-500'
                    : prospect.enrichmentData.confidence >= 50
                    ? 'bg-warning-500'
                    : 'bg-error-500'
                )}
                style={{ width: `${prospect.enrichmentData.confidence}%` }}
              />
            </div>
          </div>
        )}

        {/* Metadata */}
        {prospect.lastEnrichedAt && (
          <p className="text-xs text-gray-500">
            Last enriched: {formatDateTime(prospect.lastEnrichedAt)}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-xl">
        <div className="flex items-center justify-between gap-2">
          <button
            onClick={() => onReEnrich?.(prospect.id)}
            disabled={isReEnriching || prospect.enrichmentStatus === 'in_progress'}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <RefreshCw className={cn('w-4 h-4', isReEnriching && 'animate-spin')} />
            {isReEnriching ? 'Enriching...' : 'Re-enrich'}
          </button>
          <button
            onClick={() => onSyncCRM?.(prospect.id)}
            disabled={prospect.crmSyncStatus === 'pending'}
            className={cn(
              'btn-primary text-sm',
              prospect.crmSyncStatus === 'synced' && 'bg-success-600 hover:bg-success-500'
            )}
          >
            {prospect.crmSyncStatus === 'synced' ? 'Synced to CRM' : 'Sync to CRM'}
          </button>
        </div>
        {showOutreachButton && prospect.enrichmentStatus === 'completed' && (
          <button
            onClick={() => onGenerateOutreach?.(prospect.id)}
            className="btn-primary w-full mt-3 flex items-center justify-center gap-2 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-500 hover:to-purple-500"
          >
            <Sparkles className="w-4 h-4" />
            Generate Outreach Campaign
          </button>
        )}
      </div>
    </div>
  )
}

export default ProspectCard
