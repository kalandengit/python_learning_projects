import type { ReactNode } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export function MarketingNav() {
  return (
    <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
      <Link href="/" className="text-xl font-bold">DocuPilot AI</Link>
      <div className="flex items-center gap-3 text-sm">
        <Link className="text-slate-600 hover:text-slate-950" href="/pricing">Pricing</Link>
        <Link className="text-slate-600 hover:text-slate-950" href="/security">Security</Link>
        <Link href="/login"><Button variant="secondary">Log in</Button></Link>
        <Link href="/signup"><Button>Start free</Button></Link>
      </div>
    </nav>
  );
}

export function MarketingFooter() {
  return (
    <footer className="mx-auto mt-20 grid max-w-6xl gap-6 border-t px-6 py-10 text-sm text-slate-600 md:grid-cols-4">
      <div>
        <div className="font-semibold text-slate-950">DocuPilot AI</div>
        <p className="mt-2">AI documentation generation for fast-moving product teams.</p>
      </div>
      <Link href="/privacy">Privacy</Link>
      <Link href="/terms">Terms</Link>
      <Link href="/contact">Contact</Link>
    </footer>
  );
}

export function MarketingPage({ children }: { children: ReactNode }) {
  return (
    <main>
      <MarketingNav />
      {children}
      <MarketingFooter />
    </main>
  );
}
