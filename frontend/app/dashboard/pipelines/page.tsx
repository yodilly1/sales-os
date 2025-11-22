'use client'

import { Target } from 'lucide-react'

export default function PipelinesPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-warning-100 flex items-center justify-center">
          <Target className="w-5 h-5 text-warning-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pipelines</h1>
          <p className="text-sm text-slate-500">Track and manage your deals</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-card p-12 text-center">
        <Target className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Pipeline Management Coming Soon</h2>
        <p className="text-slate-500 max-w-md mx-auto">
          Visualize your sales pipeline, track deal progress, and get AI-powered forecasting.
        </p>
        <button className="btn-primary mt-6">
          View Pipeline
        </button>
      </div>
    </div>
  )
}
