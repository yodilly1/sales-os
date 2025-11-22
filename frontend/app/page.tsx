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
  );
}
