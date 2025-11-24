'use client'

import { useState } from 'react'
import { Mail, Linkedin, Download, Loader2, ChevronDown, ChevronUp, X } from 'lucide-react'
import type { GenerateCampaignResponse, OutreachCampaign, Prospect, Company } from '@/types'
import {
  generateCampaign,
  getCampaign,
  downloadInstantlyCSV,
  downloadHeyReachCSV,
} from '@/lib/api/outreach'
import { cn } from '@/lib/utils'

interface OutreachPanelProps {
  prospect: Prospect
  company?: Company | null
  onClose?: () => void
}

type TabType = 'email' | 'linkedin'

export function OutreachPanel({ prospect, company, onClose }: OutreachPanelProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [campaign, setCampaign] = useState<OutreachCampaign | null>(null)
  const [preview, setPreview] = useState<GenerateCampaignResponse['preview'] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('email')
  const [expandedEmails, setExpandedEmails] = useState<Set<number>>(new Set([1]))
  const [isDownloading, setIsDownloading] = useState<'instantly' | 'heyreach' | null>(null)

  const handleGenerateCampaign = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const response = await generateCampaign({
        prospect_id: prospect.id,
        prospect_email: prospect.email || undefined,
        prospect_name: prospect.name,
        prospect_title: prospect.title || undefined,
        company_name: prospect.company || company?.name || undefined,
        company_description: company?.description || undefined,
        company_industry: company?.industry || undefined,
        company_size: company?.size || undefined,
        linkedin_url: prospect.linkedinUrl || undefined,
      })

      setPreview(response.preview)

      // Fetch full campaign details
      const fullCampaign = await getCampaign(response.campaign_id)
      setCampaign(fullCampaign)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate campaign')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownloadInstantly = async () => {
    if (!campaign) return
    setIsDownloading('instantly')
    try {
      await downloadInstantlyCSV(campaign.campaign_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download CSV')
    } finally {
      setIsDownloading(null)
    }
  }

  const handleDownloadHeyReach = async () => {
    if (!campaign) return
    setIsDownloading('heyreach')
    try {
      await downloadHeyReachCSV(campaign.campaign_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download CSV')
    } finally {
      setIsDownloading(null)
    }
  }

  const toggleEmailExpanded = (emailNumber: number) => {
    setExpandedEmails((prev) => {
      const next = new Set(prev)
      if (next.has(emailNumber)) {
        next.delete(emailNumber)
      } else {
        next.add(emailNumber)
      }
      return next
    })
  }

  return (
    <div className="card">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Outreach Campaign</h3>
          {onClose && (
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Generate personalized email and LinkedIn sequences for {prospect.name}
        </p>
      </div>

      <div className="p-4">
        {/* Generate Button */}
        {!campaign && !preview && (
          <button
            onClick={handleGenerateCampaign}
            disabled={isGenerating}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating Campaign...
              </>
            ) : (
              <>
                <Mail className="w-4 h-4" />
                Generate Outreach Campaign
              </>
            )}
          </button>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Campaign Preview */}
        {campaign && (
          <div className="space-y-4">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setActiveTab('email')}
                className={cn(
                  'flex-1 px-3 py-2 text-sm font-medium rounded-md flex items-center justify-center gap-2',
                  activeTab === 'email'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                <Mail className="w-4 h-4" />
                Email Sequence
              </button>
              <button
                onClick={() => setActiveTab('linkedin')}
                className={cn(
                  'flex-1 px-3 py-2 text-sm font-medium rounded-md flex items-center justify-center gap-2',
                  activeTab === 'linkedin'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                <Linkedin className="w-4 h-4" />
                LinkedIn Sequence
              </button>
            </div>

            {/* Email Sequence */}
            {activeTab === 'email' && (
              <div className="space-y-3">
                {campaign.email_sequence.emails.map((email) => (
                  <div
                    key={email.email_number}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() => toggleEmailExpanded(email.email_number)}
                      className="w-full px-4 py-3 bg-gray-50 flex items-center justify-between hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-medium">
                          {email.email_number}
                        </span>
                        <div className="text-left">
                          <p className="text-sm font-medium text-gray-900 line-clamp-1">
                            {email.subject}
                          </p>
                          <p className="text-xs text-gray-500">
                            {email.delay_days === 0
                              ? 'Send immediately'
                              : `Wait ${email.delay_days} days`}
                          </p>
                        </div>
                      </div>
                      {expandedEmails.has(email.email_number) ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                    {expandedEmails.has(email.email_number) && (
                      <div className="px-4 py-3 bg-white">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {email.body}
                        </p>
                      </div>
                    )}
                  </div>
                ))}

                {/* Download Instantly CSV */}
                <button
                  onClick={handleDownloadInstantly}
                  disabled={isDownloading === 'instantly'}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  {isDownloading === 'instantly' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  Download for Instantly
                </button>
              </div>
            )}

            {/* LinkedIn Sequence */}
            {activeTab === 'linkedin' && (
              <div className="space-y-3">
                {/* Connection Request */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                      1
                    </span>
                    <h4 className="text-sm font-medium text-gray-900">
                      Connection Request
                    </h4>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {campaign.linkedin_sequence.connection_request}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    {campaign.linkedin_sequence.connection_request.length}/300 characters
                  </p>
                </div>

                {/* Follow-up 1 */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                      2
                    </span>
                    <h4 className="text-sm font-medium text-gray-900">
                      Follow-up 1
                    </h4>
                    <span className="text-xs text-gray-500">
                      (after connection accepted)
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {campaign.linkedin_sequence.followup_1}
                  </p>
                </div>

                {/* Follow-up 2 */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                      3
                    </span>
                    <h4 className="text-sm font-medium text-gray-900">
                      Follow-up 2
                    </h4>
                    <span className="text-xs text-gray-500">(5 days later)</span>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {campaign.linkedin_sequence.followup_2}
                  </p>
                </div>

                {/* Download HeyReach CSV */}
                <button
                  onClick={handleDownloadHeyReach}
                  disabled={isDownloading === 'heyreach'}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  {isDownloading === 'heyreach' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  Download for HeyReach
                </button>
              </div>
            )}

            {/* Regenerate Button */}
            <button
              onClick={handleGenerateCampaign}
              disabled={isGenerating}
              className="btn-secondary w-full flex items-center justify-center gap-2 mt-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Regenerating...
                </>
              ) : (
                'Regenerate Campaign'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default OutreachPanel
