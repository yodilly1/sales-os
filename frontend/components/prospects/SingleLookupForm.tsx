'use client'

import { useState } from 'react'
import { Search, Loader2, AlertCircle } from 'lucide-react'
import type { SingleLookupRequest, SingleLookupResponse } from '@/types'

interface SingleLookupFormProps {
  onLookup: (request: SingleLookupRequest) => Promise<SingleLookupResponse>
  onResult?: (response: SingleLookupResponse) => void
  isCompact?: boolean
}

export function SingleLookupForm({ onLookup, onResult, isCompact }: SingleLookupFormProps) {
  const [formData, setFormData] = useState<SingleLookupRequest>({
    name: '',
    email: '',
    company: '',
    title: '',
    linkedinUrl: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.name.trim() && !formData.email?.trim() && !formData.linkedinUrl?.trim()) {
      setError('Please provide at least a name, email, or LinkedIn URL')
      return
    }

    setIsLoading(true)
    try {
      const response = await onLookup({
        ...formData,
        name: formData.name.trim(),
        email: formData.email?.trim() || undefined,
        company: formData.company?.trim() || undefined,
        title: formData.title?.trim() || undefined,
        linkedinUrl: formData.linkedinUrl?.trim() || undefined,
      })
      onResult?.(response)

      if (!response.success) {
        setError(response.error || 'Lookup failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (field: keyof SingleLookupRequest) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }))
    setError(null)
  }

  if (isCompact) {
    return (
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={formData.name}
          onChange={handleChange('name')}
          placeholder="Search by name..."
          className="input flex-1"
        />
        <input
          type="text"
          value={formData.company || ''}
          onChange={handleChange('company')}
          placeholder="Company (optional)"
          className="input w-48"
        />
        <button type="submit" disabled={isLoading} className="btn-primary flex items-center gap-2">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          Lookup
        </button>
      </form>
    )
  }

  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Single Prospect Lookup</h2>
      <p className="text-sm text-gray-600 mb-6">
        Enter prospect information to search and enrich their profile. More details = better results.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          {/* Name */}
          <div>
            <label className="label">
              Full Name <span className="text-gray-400">(recommended)</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={handleChange('name')}
              placeholder="John Smith"
              className="input"
            />
          </div>

          {/* Email */}
          <div>
            <label className="label">
              Email <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="email"
              value={formData.email || ''}
              onChange={handleChange('email')}
              placeholder="john@company.com"
              className="input"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {/* Company */}
          <div>
            <label className="label">
              Company <span className="text-gray-400">(recommended)</span>
            </label>
            <input
              type="text"
              value={formData.company || ''}
              onChange={handleChange('company')}
              placeholder="Acme Corp"
              className="input"
            />
          </div>

          {/* Title */}
          <div>
            <label className="label">
              Title <span className="text-gray-400">(optional)</span>
            </label>
            <input
              type="text"
              value={formData.title || ''}
              onChange={handleChange('title')}
              placeholder="VP of Sales"
              className="input"
            />
          </div>
        </div>

        {/* Advanced Options */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            {showAdvanced ? '- Hide advanced options' : '+ Show advanced options'}
          </button>

          {showAdvanced && (
            <div className="mt-3">
              <label className="label">
                LinkedIn URL <span className="text-gray-400">(highly recommended if known)</span>
              </label>
              <input
                type="url"
                value={formData.linkedinUrl || ''}
                onChange={handleChange('linkedinUrl')}
                placeholder="https://linkedin.com/in/johnsmith"
                className="input"
              />
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 bg-error-50 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-error-600 flex-shrink-0" />
            <p className="text-sm text-error-700">{error}</p>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Looking up...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Lookup Prospect
            </>
          )}
        </button>
      </form>
    </div>
  )
}

export default SingleLookupForm
