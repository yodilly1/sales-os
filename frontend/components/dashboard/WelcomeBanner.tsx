'use client'

import { Sparkles, ArrowRight } from 'lucide-react'
import Link from 'next/link'

interface WelcomeBannerProps {
  userName?: string
  pendingCalls?: number
}

export function WelcomeBanner({
  userName = 'Alex',
  pendingCalls = 3,
}: WelcomeBannerProps) {
  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 rounded-2xl p-6 text-white">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

      <div className="relative">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              {getGreeting()}, {userName}!
            </h1>
            <p className="text-primary-100 mt-1">
              Here&apos;s what&apos;s happening with your sales today.
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-lg">
            <Sparkles className="w-4 h-4 text-primary-200" />
            <span className="text-sm font-medium">AI Ready</span>
          </div>
        </div>

        {pendingCalls > 0 && (
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/dashboard/calls"
              className="inline-flex items-center gap-2 bg-white text-primary-700 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary-50 transition-colors shadow-sm"
            >
              {pendingCalls} calls ready for analysis
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
