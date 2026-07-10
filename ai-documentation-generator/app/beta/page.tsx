import { MarketingPage } from "@/components/marketing/marketing-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function BetaPage() {
  return (
    <MarketingPage>
      <section className="mx-auto grid max-w-6xl gap-10 px-6 py-16 md:grid-cols-[1fr_420px] md:items-start">
        <div>
          <p className="font-medium text-slate-500">Private beta</p>
          <h1 className="mt-3 text-5xl font-bold tracking-tight">Help shape the fastest way to create product documentation.</h1>
          <p className="mt-6 text-lg text-slate-600">We are looking for SaaS teams, agencies, product managers, and support leaders who create guides, SOPs, and release notes every week.</p>
          <ul className="mt-8 space-y-3 text-slate-700">
            <li>• Upload screenshots and receive editable documentation.</li>
            <li>• Export Markdown, HTML, and PDF.</li>
            <li>• Give feedback directly to the founding team.</li>
          </ul>
        </div>
        <Card>
          <CardHeader><CardTitle>Beta application</CardTitle></CardHeader>
          <CardContent>
            <form action="/api/feedback" method="post" className="space-y-4">
              <input name="type" value="beta_application" type="hidden" />
              <input required name="email" type="email" placeholder="Work email" className="w-full rounded-xl border px-3 py-2" />
              <input name="company" placeholder="Company" className="w-full rounded-xl border px-3 py-2" />
              <textarea required name="message" placeholder="What documentation do you create today?" className="min-h-32 w-full rounded-xl border px-3 py-2" />
              <button className="w-full rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white">Request access</button>
            </form>
          </CardContent>
        </Card>
      </section>
    </MarketingPage>
  );
}
