'use client'

import { Phone } from 'lucide-react'

export default function CallsPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
          <Phone className="w-5 h-5 text-primary-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Calls</h1>
          <p className="text-sm text-slate-500">Analyze and manage your sales calls</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-card p-12 text-center">
        <Phone className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Call Analytics Coming Soon</h2>
        <p className="text-slate-500 max-w-md mx-auto">
          Upload call recordings to get AI-powered transcription, SPICED methodology analysis, and coaching insights.
        </p>
        <button className="btn-primary mt-6">
          Upload First Call
        </button>
      </div>
    </div>
  )
}
