import { MarketingPage } from "@/components/marketing/marketing-shell";

export default function ContactPage() {
  return (
    <MarketingPage>
      <section className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-4xl font-bold tracking-tight">Contact</h1>
        <p className="mt-4 text-slate-600">Use this form for beta feedback, support requests, partnership conversations, and security reports.</p>
        <form action="/api/feedback" method="post" className="mt-8 space-y-4 rounded-2xl border bg-white p-6 shadow-sm">
          <input name="type" value="contact" type="hidden" />
          <input required name="email" type="email" placeholder="Email" className="w-full rounded-xl border px-3 py-2" />
          <input name="company" placeholder="Company" className="w-full rounded-xl border px-3 py-2" />
          <textarea required name="message" placeholder="How can we help?" className="min-h-40 w-full rounded-xl border px-3 py-2" />
          <button className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white">Send message</button>
        </form>
      </section>
    </MarketingPage>
  );
}
