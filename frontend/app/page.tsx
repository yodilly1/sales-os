<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
import Link from 'next/link';
import { Button } from '@/components/ui';

export default function HomePage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Sales OS
        </h1>
        <p className="mt-4 text-lg text-gray-600">
          Generate professional sales content powered by AI
        </p>
        <div className="mt-8">
          <Link href="/content">
            <Button size="lg">
              Start Creating Content
            </Button>
          </Link>
        </div>
      </div>
    </div>
>>>>>>> origin/claude/frontend-content-ui-01SUCiGQU6dN2Z9rPASZfehV
  );
=======
import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Sales OS
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Your VP of Sales Operating System. Research prospects, enrich data,
          and sync with your CRM seamlessly.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <Link href="/prospects" className="card p-6 hover:shadow-md transition-shadow">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Prospect Research
          </h2>
          <p className="text-sm text-gray-600">
            Look up individuals or bulk upload lists. Get enriched profiles with
            company insights.
          </p>
        </Link>

        <div className="card p-6 opacity-60">
          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Transcripts
          </h2>
          <p className="text-sm text-gray-600">
            Upload call transcripts and extract SPICED insights automatically.
          </p>
          <span className="badge-gray mt-3">Coming Soon</span>
        </div>

        <div className="card p-6 opacity-60">
          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Content Generator
          </h2>
          <p className="text-sm text-gray-600">
            Generate decks, proposals, and one-pagers with AI assistance.
          </p>
          <span className="badge-gray mt-3">Coming Soon</span>
        </div>
      </div>
    </div>
  )
>>>>>>> origin/claude/prospect-ui-frontend-01F9BktJJ2Zg4J6voVhwdpQH
=======
import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/dashboard')
>>>>>>> origin/claude/build-dashboard-navigation-01MVV3BST4NwmsmDM3US68rm
}
