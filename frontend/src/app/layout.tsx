import type { Metadata } from "next";
<<<<<<< HEAD
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sales OS - VP Sales Operating System",
  description:
    "A comprehensive sales operating system that automates transcript analysis, generates sales content, and coaches using Winning by Design methodology.",
  keywords: [
    "sales",
    "CRM",
    "sales automation",
    "transcript analysis",
    "sales coaching",
    "SPICED methodology",
  ],
=======
import "./globals.css";

export const metadata: Metadata = {
  title: "Sales OS | VP-of-Sales Operating System",
  description: "Automate transcript analysis, generate sales content, and get SPICED coaching based on Winning by Design methodology.",
>>>>>>> origin/claude/frontend-coaching-ui-01ACvPTYwnXPyzreDZDTsLry
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
<<<<<<< HEAD
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
=======
      <body className="font-sans antialiased">
>>>>>>> origin/claude/frontend-coaching-ui-01ACvPTYwnXPyzreDZDTsLry
        {children}
      </body>
    </html>
  );
}
