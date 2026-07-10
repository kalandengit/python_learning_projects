import { MarketingPage } from "@/components/marketing/marketing-shell";

export default function TermsPage() {
  return (
    <MarketingPage>
      <section className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm font-medium text-slate-500">Last updated: 2026-07-08</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight">Terms of Service</h1>
        <p className="mt-6 text-slate-600">These beta terms are a launch placeholder and must be reviewed by counsel before accepting paying customers.</p>
        <div className="prose prose-slate mt-10 max-w-none space-y-6">
          <section><h2>1. Service</h2><p>DocuPilot AI helps users transform screenshots and related inputs into editable documentation. Generated outputs should be reviewed before publication.</p></section>
          <section><h2>2. Accounts</h2><p>Users are responsible for maintaining account security and ensuring uploaded content may lawfully be processed through the service.</p></section>
          <section><h2>3. Subscriptions</h2><p>Paid plans renew automatically through Stripe unless cancelled. Usage limits and AI credits are enforced according to the active plan.</p></section>
          <section><h2>4. Acceptable use</h2><p>Users may not upload unlawful data, malware, secrets they are not authorized to process, or content that violates third-party rights.</p></section>
          <section><h2>5. Disclaimer</h2><p>The product is provided as-is during beta. AI-generated documentation can contain errors and requires human review.</p></section>
        </div>
      </section>
    </MarketingPage>
  );
}
