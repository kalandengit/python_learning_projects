import { createClient } from "@/lib/supabase/server";

export async function getOrganizationAnalytics(organizationId: string) {
  const supabase = await createClient();
  const [{ data: summary }, { data: funnel }, { data: recentEvents }, { data: topEvents }] = await Promise.all([
    supabase.from("organization_analytics_summary").select("*").eq("organization_id", organizationId).maybeSingle(),
    supabase.from("onboarding_funnel_summary").select("*").eq("organization_id", organizationId).maybeSingle(),
    supabase
      .from("analytics_events")
      .select("event_name, source, properties, created_at")
      .eq("organization_id", organizationId)
      .order("created_at", { ascending: false })
      .limit(20),
    supabase
      .from("analytics_events")
      .select("event_name")
      .eq("organization_id", organizationId)
      .gte("created_at", new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())
      .limit(1000)
  ]);

  const counts = new Map<string, number>();
  for (const row of topEvents || []) counts.set(row.event_name, (counts.get(row.event_name) || 0) + 1);

  return {
    summary,
    funnel,
    recentEvents: recentEvents || [],
    topEvents: [...counts.entries()]
      .map(([eventName, count]) => ({ eventName, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  };
}
