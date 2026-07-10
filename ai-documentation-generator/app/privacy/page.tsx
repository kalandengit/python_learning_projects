import { MarketingPage } from "@/components/marketing/marketing-shell";

export default function PrivacyPage() {
  return (
    <MarketingPage>
      <section className="mx-auto max-w-3xl px-6 py-16">
        <p className="text-sm font-medium text-slate-500">Last updated: 2026-07-08</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight">Privacy Policy</h1>
        <p className="mt-6 text-slate-600">This starter privacy policy is provided for beta launch preparation and must be reviewed by qualified counsel before production use.</p>
        <div className="prose prose-slate mt-10 max-w-none space-y-6">
          <section><h2>1. Data we collect</h2><p>We collect account details, organization membership data, uploaded screenshots, generated documents, billing metadata, usage events, support messages, and technical logs needed to operate the service.</p></section>
          <section><h2>2. How we use data</h2><p>We use data to authenticate users, generate documentation, enforce quotas, provide support, improve product quality, protect the service, and comply with legal obligations.</p></section>
          <section><h2>3. AI processing</h2><p>Uploaded media and document content may be processed by configured AI providers to generate documentation. Enterprise plans should support provider selection, data retention controls, and private processing options.</p></section>
          <section><h2>4. Data retention</h2><p>Workspace owners can delete uploads and documents. Operational logs and billing records may be retained for security, fraud prevention, accounting, and compliance.</p></section>
          <section><h2>5. Security</h2><p>We use row-level access controls, encrypted infrastructure, signed storage URLs, audit logging, and least-privilege service credentials.</p></section>
          <section><h2>6. Contact</h2><p>For privacy requests, contact the company address configured in production.</p></section>
        </div>
      </section>
    </MarketingPage>
  );
}
