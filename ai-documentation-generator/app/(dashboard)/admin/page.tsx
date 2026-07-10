import Link from "next/link";
import { MetricCard } from "@/components/analytics/metric-card";
import { getOrganizationAnalytics } from "@/lib/analytics/queries";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";

export default async function AdminPage() {
  const organization = await getOrCreateDefaultOrganization();
  const analytics = await getOrganizationAnalytics(organization.id);
  const summary = analytics.summary as any;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-medium text-slate-500">Internal admin</p>
        <h1 className="text-3xl font-bold tracking-tight">Workspace health</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Operator visibility for support, usage review, and early SaaS health checks. In Sprint 09 this becomes role-gated.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Workspace" value={organization.name} hint={organization.id} />
        <MetricCard label="AI jobs" value={summary?.ai_jobs_count ?? 0} hint="Total generated jobs" />
        <MetricCard label="Estimated AI cost" value={`$${Number(summary?.estimated_ai_cost_usd || 0).toFixed(4)}`} hint="Provider-reported estimate" />
      </div>

      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold">Operational checklist</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>Verify failed AI jobs daily and inspect provider errors.</li>
          <li>Compare generated document count against subscription limits.</li>
          <li>Watch estimated AI cost as a percentage of subscription revenue.</li>
          <li>Use feature flags for risky AI/editor changes before broad rollout.</li>
        </ul>
        <Link href="/admin/audit-logs" className="mt-5 inline-block rounded-xl border px-4 py-2 text-sm font-medium hover:bg-slate-50">View audit logs</Link>
      </section>
    </div>
  );
}
