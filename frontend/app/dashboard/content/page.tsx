'use client'

import { FileText } from 'lucide-react'

export default function ContentPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-accent-100 flex items-center justify-center">
          <FileText className="w-5 h-5 text-accent-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Content</h1>
          <p className="text-sm text-slate-500">Generate sales decks and proposals</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-card p-12 text-center">
        <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Content Generation Coming Soon</h2>
        <p className="text-slate-500 max-w-md mx-auto">
          Create personalized sales decks, proposals, and follow-up emails powered by AI.
        </p>
        <button className="btn-primary mt-6">
          Create Content
        </button>
      </div>
    </div>
  )
}
