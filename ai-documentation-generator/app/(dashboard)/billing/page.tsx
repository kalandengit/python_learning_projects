import { CustomerPortalButton } from "@/components/billing/customer-portal-button";
import { PlanCard } from "@/components/billing/plan-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import { getPlanLimit, PLAN_LIMITS } from "@/lib/billing/plans";
import { getMonthlyUsage } from "@/lib/billing/usage";

export default async function BillingPage() {
  const { supabase } = await requireUser();
  const org = await getOrCreateDefaultOrganization();
  const { data: subscription } = await supabase
    .from("subscriptions")
    .select("plan,status,current_period_end,cancel_at_period_end")
    .eq("organization_id", org.id)
    .maybeSingle();

  const currentPlan = subscription?.plan ?? "free";
  const limits = getPlanLimit(currentPlan);
  const uploadUsage = await getMonthlyUsage(supabase, org.id, "upload");
  const generationUsage = await getMonthlyUsage(supabase, org.id, "document_generation");

  return (
    <main className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">Billing</p>
          <h1 className="text-3xl font-bold">Plans, quotas, and subscription</h1>
        </div>
        <CustomerPortalButton />
      </div>

      <Card>
        <CardHeader><CardTitle>Current usage</CardTitle></CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border p-4">
            <p className="text-sm text-slate-500">Plan</p>
            <p className="text-2xl font-bold capitalize">{currentPlan}</p>
            <p className="text-sm text-slate-500">Status: {subscription?.status ?? "active"}</p>
          </div>
          <div className="rounded-2xl border p-4">
            <p className="text-sm text-slate-500">Uploads this month</p>
            <p className="text-2xl font-bold">{uploadUsage} / {limits.monthlyUploads}</p>
          </div>
          <div className="rounded-2xl border p-4">
            <p className="text-sm text-slate-500">Documents this month</p>
            <p className="text-2xl font-bold">{generationUsage} / {limits.monthlyDocuments}</p>
          </div>
        </CardContent>
      </Card>

      <section className="grid gap-4 lg:grid-cols-4">
        <PlanCard plan="free" name="Free" price="$0" current={currentPlan === "free"} features={["5 AI documents/month", "10 screenshot uploads/month", "100MB storage", "1 seat"]} />
        <PlanCard plan="starter" name="Starter" price="$19/mo" current={currentPlan === "starter"} features={["50 AI documents/month", "100 uploads/month", "1GB storage", "3 seats"]} />
        <PlanCard plan="pro" name="Pro" price="$49/mo" current={currentPlan === "pro"} features={["250 AI documents/month", "500 uploads/month", "10GB storage", "10 seats"]} />
        <PlanCard plan="business" name="Business" price="$149/mo" current={currentPlan === "business"} features={["1,000 AI documents/month", "2,000 uploads/month", "100GB storage", "25 seats"]} />
      </section>
    </main>
  );
}
