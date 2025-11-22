import Link from 'next/link';
import { ArrowRight, FileText, Users, Target, TrendingUp } from 'lucide-react';

export default function Home() {
  const quickActions = [
    {
      title: 'Analyze Transcript',
      description: 'Upload a call transcript for SPICED analysis',
      href: '/transcript',
      icon: FileText,
      color: 'primary',
    },
    {
      title: 'Research Prospects',
      description: 'Enrich prospect data with AI-powered research',
      href: '/prospects',
      icon: Users,
      color: 'accent',
    },
    {
      title: 'Generate Content',
      description: 'Create decks, proposals, and one-pagers',
      href: '/content',
      icon: Target,
      color: 'success',
    },
    {
      title: 'Sales Coaching',
      description: 'Get AI coaching insights for your team',
      href: '/coaching',
      icon: TrendingUp,
      color: 'warning',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-900 mb-2">
          Welcome to Sales OS
        </h1>
        <p className="text-neutral-600 text-lg">
          Your AI-powered VP of Sales operating system
        </p>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.title}
                href={action.href}
                className="group card p-6 hover:shadow-elevated transition-shadow duration-200"
              >
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg bg-${action.color}-100 text-${action.color}-600 mb-4`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-neutral-900 mb-1 group-hover:text-primary-600 transition-colors">
                  {action.title}
                </h3>
                <p className="text-sm text-neutral-600 mb-3">
                  {action.description}
                </p>
                <span className="inline-flex items-center text-sm font-medium text-primary-600 group-hover:text-primary-700">
                  Get Started
                  <ArrowRight className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Activity Placeholder */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-neutral-900">
            Recent Activity
          </h2>
        </div>
        <div className="card-body">
          <div className="text-center py-12">
            <p className="text-neutral-500">
              No recent activity yet. Get started by analyzing a transcript or researching prospects.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
