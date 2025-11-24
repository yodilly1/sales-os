'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Phone,
  FileText,
  Users,
  Target,
  BookOpen,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Calls', href: '/calls', icon: Phone, badge: '3' },
  { name: 'Transcripts', href: '/transcript', icon: FileText },
  { name: 'Prospects', href: '/prospects', icon: Users },
  { name: 'Pipelines', href: '/pipelines', icon: Target },
  { name: 'Content', href: '/content', icon: BookOpen },
  { name: 'Coaching', href: '/coaching', icon: BookOpen },
];

const bottomNavigation: NavItem[] = [
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Help', href: '/help', icon: HelpCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 280 }}
      className="flex flex-col h-screen bg-white/80 backdrop-blur-xl border-r border-neutral-200/60 sticky top-0 z-50"
    >
      {/* Logo */}
      <div className="flex items-center h-20 px-6 border-b border-neutral-100">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center shadow-lg shadow-primary-500/20">
            {collapsed ? (
              <span className="text-white font-bold text-lg">S</span>
            ) : (
              <Zap className="w-6 h-6 text-white" />
            )}
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
              >
                <h1 className="text-xl font-bold text-neutral-900 tracking-tight">Sales OS</h1>
                <p className="text-xs font-medium text-neutral-500">VP of Sales Platform</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto scrollbar-thin">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 relative overflow-hidden',
                active
                  ? 'text-primary-700 bg-primary-50/80'
                  : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
              )}
              title={collapsed ? item.name : undefined}
            >
              {active && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 bg-primary-50/80 rounded-xl -z-10"
                  initial={false}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <Icon className={cn('w-5 h-5 flex-shrink-0 transition-colors', active ? 'text-primary-600' : 'text-neutral-500 group-hover:text-neutral-700')} />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.name}</span>
                  {item.badge && (
                    <span className="px-2 py-0.5 text-xs font-bold bg-primary-100 text-primary-700 rounded-full shadow-sm">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Navigation */}
      <div className="px-4 py-6 border-t border-neutral-100 space-y-1.5">
        {bottomNavigation.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200',
                active
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm font-medium text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 w-full transition-all duration-200"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span>Collapse Sidebar</span>
            </>
          )}
        </button>
      </div>

      {/* Usage Stats (only shown when not collapsed) */}
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-6 pb-6"
          >
            <div className="p-4 bg-neutral-50 rounded-2xl border border-neutral-100">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-neutral-700">API Usage</span>
                <span className="text-xs font-bold text-primary-600">75%</span>
              </div>
              <div className="w-full h-2 bg-neutral-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full shadow-sm"
                  style={{ width: '75%' }}
                />
              </div>
              <p className="text-xs text-neutral-500 mt-3 font-medium">7,500 / 10,000 calls</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.aside>
  );
}
