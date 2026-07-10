import { MarketingPage } from "@/components/marketing/marketing-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const items = [
  ["Access control", "Supabase Auth, organization membership checks, role-based permissions, and Row Level Security policies."],
  ["Data protection", "Private object storage, signed URLs, environment-based secrets, and minimum required service-role usage."],
  ["Auditability", "Audit logs track sensitive collaboration and administrative actions."],
  ["AI safety", "Provider abstraction keeps AI processing replaceable and prepares enterprise data controls."],
  ["Production readiness", "CI, dependency audits, security headers, and migration validation are included."],
  ["Compliance roadmap", "GDPR, SOC 2, DPA, SSO, SCIM, and retention controls are planned for enterprise readiness."]
];

export default function SecurityPage() {
  return (
    <MarketingPage>
      <section className="mx-auto max-w-6xl px-6 py-16">
        <p className="font-medium text-slate-500">Security</p>
        <h1 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight">Designed for teams that document sensitive products.</h1>
        <p className="mt-5 max-w-2xl text-slate-600">Sprint 12 adds public trust pages and a clear security roadmap for beta buyers and design partners.</p>
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map(([title, text]) => (
            <Card key={title}><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent><p className="text-sm text-slate-600">{text}</p></CardContent></Card>
          ))}
        </div>
      </section>
    </MarketingPage>
  );
}
