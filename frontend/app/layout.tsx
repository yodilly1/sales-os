import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sales OS - Prospect Research & Enrichment',
  description: 'VP of Sales Operating System - Prospect research and enrichment platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <header className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center gap-8">
                  <h1 className="text-xl font-bold text-gray-900">Sales OS</h1>
                  <nav className="hidden md:flex items-center gap-6">
                    <a href="/" className="text-sm text-gray-600 hover:text-gray-900">
                      Dashboard
                    </a>
                    <a href="/prospects" className="text-sm text-primary-600 font-medium">
                      Prospects
                    </a>
                    <a href="/transcripts" className="text-sm text-gray-600 hover:text-gray-900">
                      Transcripts
                    </a>
                    <a href="/content" className="text-sm text-gray-600 hover:text-gray-900">
                      Content
                    </a>
                  </nav>
                </div>
                <div className="flex items-center gap-4">
                  <button className="btn-secondary text-sm">
                    Settings
                  </button>
                </div>
              </div>
            </div>
          </header>
          <main className="flex-1">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
