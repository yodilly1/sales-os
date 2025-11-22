'use client'

import { Settings, User, Bell, Shield, Link2, Palette } from 'lucide-react'

const settingsSections = [
  {
    title: 'Profile',
    description: 'Manage your personal information',
    icon: User,
  },
  {
    title: 'Notifications',
    description: 'Configure email and push notifications',
    icon: Bell,
  },
  {
    title: 'Security',
    description: 'Password, 2FA, and security settings',
    icon: Shield,
  },
  {
    title: 'Integrations',
    description: 'Connect to HubSpot, Avoma, and more',
    icon: Link2,
  },
  {
    title: 'Appearance',
    description: 'Customize your dashboard theme',
    icon: Palette,
  },
]

export default function SettingsPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
          <Settings className="w-5 h-5 text-slate-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
          <p className="text-sm text-slate-500">Manage your account and preferences</p>
        </div>
      </div>

      <div className="space-y-3">
        {settingsSections.map((section) => {
          const Icon = section.icon
          return (
            <button
              key={section.title}
              className="w-full bg-white rounded-xl border border-slate-100 shadow-card p-5
                       flex items-center gap-4 hover:shadow-card-hover hover:border-primary-200
                       transition-all text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <h3 className="font-medium text-slate-900">{section.title}</h3>
                <p className="text-sm text-slate-500">{section.description}</p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
