import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-20">
      <nav className="mb-20 flex items-center justify-between">
        <div className="text-xl font-bold">DocuPilot AI</div>
        <Link href="/login"><Button variant="secondary">Log in</Button></Link>
      </nav>
      <section className="grid gap-10 md:grid-cols-2 md:items-center">
        <div>
          <p className="mb-4 inline-flex rounded-full border bg-white px-3 py-1 text-sm">Screenshot → documentation in minutes</p>
          <h1 className="text-5xl font-bold tracking-tight">Turn screenshots into polished guides, SOPs, and help docs.</h1>
          <p className="mt-6 text-lg text-slate-600">Upload product screenshots, let AI understand the interface, then edit and export professional documentation.</p>
          <div className="mt-8 flex gap-3">
            <Link href="/signup"><Button>Start free</Button></Link>
            <Link href="/login"><Button variant="ghost">View dashboard</Button></Link>
          </div>
        </div>
        <Card>
          <div className="rounded-xl bg-slate-100 p-4">
            <div className="mb-3 h-8 w-40 rounded bg-white" />
            <div className="space-y-3">
              {[1,2,3].map((i) => <div key={i} className="h-16 rounded-xl bg-white p-4 text-sm text-slate-500">Generated step {i}</div>)}
            </div>
          </div>
        </Card>
      </section>
    </main>
  );
}
