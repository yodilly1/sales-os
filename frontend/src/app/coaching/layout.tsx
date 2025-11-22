import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Coaching Dashboard | Sales OS',
  description: 'Track SPICED performance and get actionable coaching insights based on Winning by Design methodology.',
};

export default function CoachingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
