import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sales OS',
  description: 'VP-of-Sales Operating System - Professional sales content and deck generation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
