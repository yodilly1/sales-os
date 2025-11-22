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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  )
}
