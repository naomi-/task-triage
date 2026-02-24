import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cozy Triage",
  description: "Sort out your mind with ease.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <header className="border-b bg-white/50 backdrop-blur-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
              <Link href="/" className="text-xl font-bold text-primary tracking-tight">
                Cozy Triage
              </Link>
              <nav className="flex gap-6 text-sm font-medium">
                <Link href="/" className="hover:text-primary transition-colors">Inbox</Link>
                <Link href="/tasks" className="hover:text-primary transition-colors">Tasks</Link>
              </nav>
            </div>
          </header>
          <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8">
            {children}
          </main>
          <footer className="border-t py-6 text-center text-sm text-muted-foreground bg-muted/30">
            © 2026 Cozy Triage • Made with peace of mind.
          </footer>
        </div>
      </body>
    </html>
  );
}
