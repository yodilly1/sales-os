import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sales OS | VP-of-Sales Operating System",
  description: "Automate transcript analysis, generate sales content, and get SPICED coaching based on Winning by Design methodology.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
