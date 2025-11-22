<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import type { Metadata } from 'next';
<<<<<<< HEAD
<<<<<<< HEAD
import './globals.css';

export const metadata: Metadata = {
  title: 'Sales OS',
  description: 'VP-of-Sales Operating System - Professional sales content and deck generation',
=======
import { Inter } from 'next/font/google';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
=======
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
>>>>>>> origin/claude/frontend-content-ui-01SUCiGQU6dN2Z9rPASZfehV
  variable: '--font-inter',
});

export const metadata: Metadata = {
<<<<<<< HEAD
  title: 'Sales OS - VP of Sales Operating System',
  description: 'AI-powered sales intelligence platform for modern sales teams',
>>>>>>> origin/claude/transcript-ui-frontend-01827GXMtwFgZZZSpTQu33aT
=======
  title: 'Sales OS - Content Generator',
  description: 'Generate professional sales content with AI',
>>>>>>> origin/claude/frontend-content-ui-01SUCiGQU6dN2Z9rPASZfehV
};
=======
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sales OS - Prospect Research & Enrichment',
  description: 'VP of Sales Operating System - Prospect research and enrichment platform',
}
>>>>>>> origin/claude/prospect-ui-frontend-01F9BktJJ2Zg4J6voVhwdpQH
=======
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'Sales OS - VP of Sales Operating System',
  description: 'AI-powered platform for sales leaders. Automate call analysis, generate content, enrich prospects, and coach your team.',
  keywords: ['sales', 'AI', 'CRM', 'sales intelligence', 'call analytics', 'sales coaching'],
}
>>>>>>> origin/claude/build-dashboard-navigation-01MVV3BST4NwmsmDM3US68rm
=======
/**
 * Root layout for Sales OS frontend.
 */

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sales OS",
  description: "AI-powered sales operations platform",
};
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Sales OS',
  description: 'VP of Sales Operating System',
};
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
=======
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Sales OS - Analytics Dashboard',
  description: 'Comprehensive analytics dashboard for sales performance insights',
}
>>>>>>> origin/claude/analytics-dashboard-01M24DLkEb1rR8wBY9c26gKw

export default function RootLayout({
  children,
}: {
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
  children: React.ReactNode;
}) {
  return (
<<<<<<< HEAD
<<<<<<< HEAD
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
=======
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-neutral-50">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-auto p-6">
              {children}
            </main>
          </div>
        </div>
      </body>
>>>>>>> origin/claude/transcript-ui-frontend-01827GXMtwFgZZZSpTQu33aT
=======
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen font-sans antialiased">
        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/95 backdrop-blur">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white font-bold text-sm">
                  S
                </div>
                <span className="text-xl font-semibold text-gray-900">Sales OS</span>
              </div>
              <nav className="flex items-center gap-6">
                <a
                  href="/content"
                  className="text-sm font-medium text-gray-600 transition-colors hover:text-gray-900"
                >
                  Content Generator
                </a>
              </nav>
            </div>
          </header>
          <main className="flex-1">{children}</main>
        </div>
      </body>
>>>>>>> origin/claude/frontend-content-ui-01SUCiGQU6dN2Z9rPASZfehV
    </html>
  );
=======
=======
>>>>>>> origin/claude/analytics-dashboard-01M24DLkEb1rR8wBY9c26gKw
  children: React.ReactNode
}) {
  return (
    <html lang="en">
<<<<<<< HEAD
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
>>>>>>> origin/claude/prospect-ui-frontend-01F9BktJJ2Zg4J6voVhwdpQH
=======
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  )
>>>>>>> origin/claude/build-dashboard-navigation-01MVV3BST4NwmsmDM3US68rm
=======
=======
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
<<<<<<< HEAD
      <body className="min-h-screen bg-gray-50 antialiased">
        {children}
      </body>
    </html>
  );
>>>>>>> origin/claude/notification-system-011TGLjzAos8ag9kBQK32dgF
=======
      <body className={inter.className}>{children}</body>
    </html>
  );
>>>>>>> origin/claude/team-management-features-01YbA13LtG8bARp7mPDMFyPw
=======
      <body className="min-h-screen">{children}</body>
    </html>
  )
>>>>>>> origin/claude/analytics-dashboard-01M24DLkEb1rR8wBY9c26gKw
}
