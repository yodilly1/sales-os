'use client'

import {
  Building2,
  Globe,
  Users,
  MapPin,
  Linkedin,
  DollarSign,
  Layers,
  ExternalLink,
} from 'lucide-react'
import type { Company } from '@/types'
import { formatDate } from '@/lib/utils'

interface CompanyCardProps {
  company: Company
  onViewDetails?: (companyId: string) => void
}

export function CompanyCard({ company, onViewDetails }: CompanyCardProps) {
  return (
    <div className="card">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          {company.logoUrl ? (
            <img
              src={company.logoUrl}
              alt={`${company.name} logo`}
              className="w-14 h-14 rounded-lg object-contain bg-gray-100"
            />
          ) : (
            <div className="w-14 h-14 bg-gray-100 rounded-lg flex items-center justify-center">
              <Building2 className="w-7 h-7 text-gray-400" />
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{company.name}</h3>
            {company.industry && (
              <span className="badge-primary">{company.industry}</span>
            )}
          </div>
        </div>

        {/* Description */}
        {company.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{company.description}</p>
        )}

        {/* Company Details Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          {company.size && (
            <div className="flex items-center gap-2 text-sm">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-gray-700">
                {company.employeeCount?.toLocaleString() || company.size} employees
              </span>
            </div>
          )}
          {company.headquarters && (
            <div className="flex items-center gap-2 text-sm">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="text-gray-700">{company.headquarters}</span>
            </div>
          )}
          {company.website && (
            <div className="flex items-center gap-2 text-sm">
              <Globe className="w-4 h-4 text-gray-400" />
              <a
                href={company.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline truncate flex items-center gap-1"
              >
                {company.domain || 'Website'}
                <ExternalLink className="w-3 h-3 flex-shrink-0" />
              </a>
            </div>
          )}
          {company.linkedinUrl && (
            <div className="flex items-center gap-2 text-sm">
              <Linkedin className="w-4 h-4 text-gray-400" />
              <a
                href={company.linkedinUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:underline flex items-center gap-1"
              >
                LinkedIn
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>

        {/* Funding Information */}
        {company.funding && (
          <div className="bg-success-50 rounded-lg p-3 mb-4">
            <h4 className="text-xs font-medium text-success-800 uppercase tracking-wider mb-2 flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              Funding
            </h4>
            <div className="space-y-1">
              {company.funding.totalRaised && (
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Total Raised:</span> {company.funding.totalRaised}
                </p>
              )}
              {company.funding.lastRoundType && company.funding.lastRoundAmount && (
                <p className="text-sm text-gray-700">
                  <span className="font-medium">Last Round:</span> {company.funding.lastRoundType} -{' '}
                  {company.funding.lastRoundAmount}
                  {company.funding.lastRoundDate && (
                    <span className="text-gray-500"> ({company.funding.lastRoundDate})</span>
                  )}
                </p>
              )}
              {company.funding.investors && company.funding.investors.length > 0 && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Investors:</span>{' '}
                  {company.funding.investors.slice(0, 3).join(', ')}
                  {company.funding.investors.length > 3 && (
                    <span className="text-gray-500">
                      {' '}
                      +{company.funding.investors.length - 3} more
                    </span>
                  )}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Tech Stack */}
        {company.techStack && company.techStack.length > 0 && (
          <div className="mb-4">
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Layers className="w-3 h-3" />
              Tech Stack
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {company.techStack.slice(0, 8).map((tech, idx) => (
                <span key={idx} className="badge-gray">
                  {tech}
                </span>
              ))}
              {company.techStack.length > 8 && (
                <span className="badge-gray">+{company.techStack.length - 8} more</span>
              )}
            </div>
          </div>
        )}

        {/* Revenue */}
        {company.revenue && (
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
            <DollarSign className="w-4 h-4 text-gray-400" />
            <span>Est. Revenue: {company.revenue}</span>
          </div>
        )}

        {/* Metadata */}
        {company.lastEnrichedAt && (
          <p className="text-xs text-gray-500">
            Last updated: {formatDate(company.lastEnrichedAt)}
          </p>
        )}
      </div>

      {/* Actions */}
      {onViewDetails && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-xl">
          <button
            onClick={() => onViewDetails(company.id)}
            className="btn-secondary text-sm w-full"
          >
            View Full Company Profile
          </button>
        </div>
      )}
    </div>
  )
}

export default CompanyCard
