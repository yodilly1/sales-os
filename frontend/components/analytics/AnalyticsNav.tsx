'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Phone, FileText, GitBranch, Users, LayoutDashboard } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

const navItems = [
  {
    name: 'Overview',
    href: '/analytics',
    icon: LayoutDashboard,
  },
  {
    name: 'Calls',
    href: '/analytics/calls',
    icon: Phone,
  },
  {
    name: 'Content',
    href: '/analytics/content',
    icon: FileText,
  },
  {
    name: 'Pipeline',
    href: '/analytics/pipeline',
    icon: GitBranch,
  },
  {
    name: 'Team',
    href: '/analytics/team',
    icon: Users,
  },
]

export function AnalyticsNav() {
  const pathname = usePathname()

  return (
    <nav className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
      {navItems.map((item) => {
        const isActive = pathname === item.href
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors',
              isActive
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
            )}
          >
            <item.icon className="w-4 h-4" />
            {item.name}
          </Link>
        )
      })}
    </nav>
  )
}
