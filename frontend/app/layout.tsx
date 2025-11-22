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

export default function RootLayout({
  children,
}: {
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
}
