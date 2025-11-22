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
  );
}
