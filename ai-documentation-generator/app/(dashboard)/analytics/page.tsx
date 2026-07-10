import { EventBarList } from "@/components/analytics/event-bar-list";
import { MetricCard } from "@/components/analytics/metric-card";
import { OnboardingFunnel } from "@/components/analytics/onboarding-funnel";
import { getOrganizationAnalytics } from "@/lib/analytics/queries";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";

export default async function AnalyticsPage() {
  const organization = await getOrCreateDefaultOrganization();
  const analytics = await getOrganizationAnalytics(organization.id);
  const summary = analytics.summary as any;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-medium text-slate-500">Sprint 08</p>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Monitor activation, product usage, export activity, AI costs, and onboarding conversion for this workspace.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Projects" value={summary?.projects_count ?? 0} />
        <MetricCard label="Uploads" value={summary?.uploads_count ?? 0} />
        <MetricCard label="Documents" value={summary?.documents_count ?? 0} />
        <MetricCard label="Events 30d" value={summary?.events_30d ?? 0} />
        <MetricCard label="AI jobs" value={summary?.ai_jobs_count ?? 0} />
        <MetricCard label="Completed jobs" value={summary?.completed_ai_jobs_count ?? 0} />
        <MetricCard label="Exports" value={summary?.exports_count ?? 0} />
        <MetricCard label="Estimated AI cost" value={`$${Number(summary?.estimated_ai_cost_usd || 0).toFixed(4)}`} />
      </div>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Onboarding funnel</h2>
        <OnboardingFunnel funnel={analytics.funnel as any} />
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Top events, last 30 days</h2>
          <div className="mt-4"><EventBarList events={analytics.topEvents} /></div>
        </section>

        <section className="rounded-2xl border bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">Recent event stream</h2>
          <div className="mt-4 divide-y">
            {analytics.recentEvents.length ? analytics.recentEvents.map((event: any, index: number) => (
              <div key={`${event.created_at}-${index}`} className="py-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{event.event_name}</span>
                  <span className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">source: {event.source}</p>
              </div>
            )) : <p className="text-sm text-slate-500">No events yet.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}
