'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import {
  User,
  Settings,
  CreditCard,
  LogOut,
  ChevronDown,
  Moon,
  Sun,
} from 'lucide-react'
import { cn, getInitials } from '@/lib/utils'

interface UserInfo {
  name: string
  email: string
  role: string
  avatarUrl?: string
}

// Mock user data - in production this would come from auth context
const mockUser: UserInfo = {
  name: 'Alex Johnson',
  email: 'alex@company.com',
  role: 'VP of Sales',
}

export function UserDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 p-1.5 rounded-lg transition-colors',
          isOpen ? 'bg-slate-100' : 'hover:bg-slate-100'
        )}
      >
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
          <span className="text-xs font-semibold text-white">
            {getInitials(mockUser.name)}
          </span>
        </div>
        <div className="hidden md:block text-left">
          <p className="text-sm font-medium text-slate-900">{mockUser.name}</p>
          <p className="text-xs text-slate-500">{mockUser.role}</p>
        </div>
        <ChevronDown className={cn(
          'w-4 h-4 text-slate-400 transition-transform hidden md:block',
          isOpen && 'rotate-180'
        )} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-slate-200 py-2 animate-fade-in">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-sm font-medium text-slate-900">{mockUser.name}</p>
            <p className="text-xs text-slate-500">{mockUser.email}</p>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <Link
              href="/dashboard/profile"
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <User className="w-4 h-4 text-slate-400" />
              <span>Your Profile</span>
            </Link>
            <Link
              href="/dashboard/settings"
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <Settings className="w-4 h-4 text-slate-400" />
              <span>Settings</span>
            </Link>
            <Link
              href="/dashboard/billing"
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <CreditCard className="w-4 h-4 text-slate-400" />
              <span>Billing & Plans</span>
            </Link>
          </div>

          {/* Theme Toggle */}
          <div className="py-1 border-t border-slate-100">
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="flex items-center justify-between w-full px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                {isDarkMode ? (
                  <Moon className="w-4 h-4 text-slate-400" />
                ) : (
                  <Sun className="w-4 h-4 text-slate-400" />
                )}
                <span>Dark Mode</span>
              </div>
              <div className={cn(
                'w-9 h-5 rounded-full transition-colors relative',
                isDarkMode ? 'bg-primary-600' : 'bg-slate-200'
              )}>
                <div className={cn(
                  'absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                  isDarkMode ? 'translate-x-4' : 'translate-x-0.5'
                )} />
              </div>
            </button>
          </div>

          {/* Sign Out */}
          <div className="py-1 border-t border-slate-100">
            <button
              onClick={() => {
                setIsOpen(false)
                // Handle sign out
              }}
              className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-danger-600 hover:bg-danger-50 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
