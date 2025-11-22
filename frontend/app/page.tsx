import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Sales OS
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          VP of Sales Operating System
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/auth/login" className="btn-primary">
            Sign In
          </Link>
          <Link href="/auth/register" className="btn-secondary">
            Get Started
          </Link>
        </div>
      </div>
    </main>
  );
}
