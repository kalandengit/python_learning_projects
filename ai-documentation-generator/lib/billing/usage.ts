import { getPlanLimit } from "@/lib/billing/plans";

export type QuotaKind = "upload" | "document_generation";

export async function getOrganizationSubscription(supabase: any, organizationId: string) {
  const { data, error } = await supabase
    .from("subscriptions")
    .select("plan,status,current_period_end")
    .eq("organization_id", organizationId)
    .maybeSingle();
  if (error) throw error;
  return data ?? { plan: "free", status: "active", current_period_end: null };
}

export async function getMonthlyUsage(supabase: any, organizationId: string, kind: QuotaKind) {
  const start = new Date();
  start.setUTCDate(1);
  start.setUTCHours(0, 0, 0, 0);
  const eventType = kind === "upload" ? "upload_created" : "document_generated";
  const { count, error } = await supabase
    .from("usage_events")
    .select("id", { count: "exact", head: true })
    .eq("organization_id", organizationId)
    .eq("event_type", eventType)
    .gte("created_at", start.toISOString());
  if (error) throw error;
  return count ?? 0;
}

export async function assertQuotaAvailable(supabase: any, organizationId: string, kind: QuotaKind) {
  const subscription = await getOrganizationSubscription(supabase, organizationId);
  const limits = getPlanLimit(subscription.plan);
  const used = await getMonthlyUsage(supabase, organizationId, kind);
  const limit = kind === "upload" ? limits.monthlyUploads : limits.monthlyDocuments;
  if (used >= limit) {
    throw new Error(`Monthly ${kind.replace("_", " ")} quota reached for the ${limits.name} plan.`);
  }
  return { used, limit, plan: limits.name };
}

export async function recordUsageEvent(supabase: any, payload: { organizationId: string; userId: string; eventType: string; metadata?: Record<string, unknown> }) {
  const { error } = await supabase.from("usage_events").insert({
    organization_id: payload.organizationId,
    user_id: payload.userId,
    event_type: payload.eventType,
    metadata: payload.metadata ?? {}
  });
  if (error) throw error;
}
