'use client'

import { Mail, Phone, MapPin, Linkedin, Building2, Briefcase, RefreshCw, ExternalLink, Globe, Sparkles, TrendingUp, Newspaper, DollarSign, Lightbulb } from 'lucide-react'
import type { Prospect, Company, EnrichmentStatus, CRMSyncStatus } from '@/types'
import { cn, formatDateTime, getInitials } from '@/lib/utils'

interface ProspectCardProps {
  prospect: Prospect
  company?: Company | null
  onReEnrich?: (prospectId: string) => void
  onSyncCRM?: (prospectId: string) => void
  isReEnriching?: boolean
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
  isReEnriching,
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

        {/* Web Research - Recent News */}
        {prospect.enrichmentData?.webResearch?.news && prospect.enrichmentData.webResearch.news.length > 0 && (
          <div className="bg-blue-50 rounded-lg p-3 mb-4">
            <h4 className="text-xs font-medium text-blue-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Newspaper className="w-3.5 h-3.5" />
              Recent News
            </h4>
            <div className="space-y-2">
              {prospect.enrichmentData.webResearch.news.slice(0, 3).map((article, idx) => (
                <div key={idx} className="text-sm">
                  {article.url ? (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-700 hover:underline flex items-start gap-1"
                    >
                      <span>{article.title}</span>
                      <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
                    </a>
                  ) : (
                    <p className="text-blue-700">{article.title}</p>
                  )}
                  <p className="text-xs text-blue-600">
                    {article.source && `${article.source}`}
                    {article.publishedAt && ` • ${article.publishedAt}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Web Research - Funding Info */}
        {prospect.enrichmentData?.webResearch?.funding && (
          <div className="bg-green-50 rounded-lg p-3 mb-4">
            <h4 className="text-xs font-medium text-green-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5" />
              Funding Information
            </h4>
            <div className="text-sm text-green-800">
              {prospect.enrichmentData.webResearch.funding.amount && (
                <p className="font-medium">{prospect.enrichmentData.webResearch.funding.amount}</p>
              )}
              {prospect.enrichmentData.webResearch.funding.stage && (
                <p className="text-green-700">{prospect.enrichmentData.webResearch.funding.stage}</p>
              )}
              {prospect.enrichmentData.webResearch.funding.sourceTitle && (
                <p className="text-xs text-green-600 mt-1">
                  Source: {prospect.enrichmentData.webResearch.funding.sourceTitle}
                </p>
              )}
            </div>
          </div>
        )}

        {/* AI Insights */}
        {prospect.enrichmentData?.aiInsights && (
          <div className="bg-purple-50 rounded-lg p-3 mb-4">
            <h4 className="text-xs font-medium text-purple-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              AI Insights
            </h4>
            <div className="space-y-2 text-sm">
              {/* Business Info */}
              <div className="flex flex-wrap gap-2">
                {prospect.enrichmentData.aiInsights.revenueModel && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs">
                    <TrendingUp className="w-3 h-3" />
                    {prospect.enrichmentData.aiInsights.revenueModel}
                  </span>
                )}
                {prospect.enrichmentData.aiInsights.businessModel && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs">
                    <Building2 className="w-3 h-3" />
                    {prospect.enrichmentData.aiInsights.businessModel}
                  </span>
                )}
                {prospect.enrichmentData.aiInsights.growthStage && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs">
                    <Globe className="w-3 h-3" />
                    {prospect.enrichmentData.aiInsights.growthStage}
                  </span>
                )}
              </div>

              {/* Key Findings */}
              {prospect.enrichmentData.aiInsights.keyFindings && prospect.enrichmentData.aiInsights.keyFindings.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-purple-700 mb-1 flex items-center gap-1">
                    <Lightbulb className="w-3 h-3" />
                    Key Findings
                  </p>
                  <ul className="space-y-1">
                    {prospect.enrichmentData.aiInsights.keyFindings.slice(0, 3).map((finding, idx) => (
                      <li key={idx} className="text-xs text-purple-800 flex items-start gap-1.5">
                        <span className="flex-shrink-0 w-1 h-1 mt-1.5 bg-purple-500 rounded-full" />
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Opportunities */}
              {prospect.enrichmentData.aiInsights.opportunities && prospect.enrichmentData.aiInsights.opportunities.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-purple-700 mb-1">Opportunities</p>
                  <ul className="space-y-1">
                    {prospect.enrichmentData.aiInsights.opportunities.slice(0, 2).map((opportunity, idx) => (
                      <li key={idx} className="text-xs text-purple-800 flex items-start gap-1.5">
                        <span className="flex-shrink-0 w-1 h-1 mt-1.5 bg-green-500 rounded-full" />
                        {opportunity}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* AI Confidence */}
              {prospect.enrichmentData.aiInsights.confidenceScore > 0 && (
                <div className="mt-2 pt-2 border-t border-purple-200">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-purple-600">AI Confidence</span>
                    <span className="font-medium text-purple-800">
                      {Math.round(prospect.enrichmentData.aiInsights.confidenceScore * 100)}%
                    </span>
                  </div>
                </div>
              )}
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
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between rounded-b-xl">
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
    </div>
  )
}

export default ProspectCard
