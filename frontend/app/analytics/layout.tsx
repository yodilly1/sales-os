import { AnalyticsNav } from '@/components/analytics'

export default function AnalyticsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-bold text-gray-900">Sales OS</h1>
              <nav className="hidden md:flex items-center gap-6">
                <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
                  Dashboard
                </a>
                <a href="/analytics" className="text-sm font-medium text-primary-600">
                  Analytics
                </a>
                <a href="/prospects" className="text-sm text-gray-600 hover:text-gray-900">
                  Prospects
                </a>
                <a href="/content" className="text-sm text-gray-600 hover:text-gray-900">
                  Content
                </a>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-700">JD</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <AnalyticsNav />
        </div>
        {children}
      </main>
    </div>
  )
}
