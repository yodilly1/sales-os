<<<<<<< HEAD
export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <header className="text-center mb-16">
          <h1 className="text-5xl font-bold text-brand-primary mb-4">
            Sales OS
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            VP-of-Sales Operating System - Generate professional proposals,
            pitch decks, and sales content with SPICED methodology integration.
          </p>
        </header>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureCard
            title="PDF Generation"
            description="Create professional proposals and one-pagers with consistent branding"
            icon="📄"
            href="/content/pdf"
          />
          <FeatureCard
            title="Slide Decks"
            description="Generate pitch decks and QBR presentations with elegant layouts"
            icon="📊"
            href="/content/deck"
          />
          <FeatureCard
            title="Web Viewer"
            description="Share interactive presentations with shareable links"
            icon="🌐"
            href="/deck"
          />
          <FeatureCard
            title="SPICED Analysis"
            description="Extract insights from sales transcripts using SPICED methodology"
            icon="🎯"
            href="/transcript"
          />
          <FeatureCard
            title="Prospect Research"
            description="Enrich prospect data with comprehensive research"
            icon="🔍"
            href="/prospect"
          />
          <FeatureCard
            title="CRM Integration"
            description="Sync data seamlessly with HubSpot and other CRMs"
            icon="🔗"
            href="/integrations"
          />
        </div>
      </div>
    </main>
  );
}

function FeatureCard({
  title,
  description,
  icon,
  href,
}: {
  title: string;
  description: string;
  icon: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="block p-6 bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md hover:border-brand-secondary transition-all"
    >
      <div className="text-4xl mb-4">{icon}</div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
      <p className="text-gray-600">{description}</p>
    </a>
=======
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
>>>>>>> origin/claude/transcript-ui-frontend-01827GXMtwFgZZZSpTQu33aT
  );
}
