import Link from "next/link";
import { PlanCard } from "@/components/billing/plan-card";
import { Button } from "@/components/ui/button";

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-6xl space-y-10 px-6 py-16">
      <div className="text-center">
        <p className="text-sm font-medium text-slate-500">Pricing</p>
        <h1 className="mt-2 text-4xl font-bold">Start free. Upgrade when documentation becomes a workflow.</h1>
        <p className="mx-auto mt-4 max-w-2xl text-slate-600">Simple SaaS pricing with monthly AI generation quotas. Use Stripe Checkout for upgrades and the customer portal for subscription management.</p>
        <Link className="mt-6 inline-flex items-center justify-center rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" href="/signup">Create free account</Link>
      </div>
      <section className="grid gap-4 lg:grid-cols-4">
        <PlanCard plan="free" name="Free" price="$0" features={["5 AI documents/month", "10 screenshot uploads/month", "100MB storage", "1 seat"]} />
        <PlanCard plan="starter" name="Starter" price="$19/mo" features={["50 AI documents/month", "100 uploads/month", "1GB storage", "3 seats"]} />
        <PlanCard plan="pro" name="Pro" price="$49/mo" features={["250 AI documents/month", "500 uploads/month", "10GB storage", "10 seats"]} />
        <PlanCard plan="business" name="Business" price="$149/mo" features={["1,000 AI documents/month", "2,000 uploads/month", "100GB storage", "25 seats"]} />
      </section>
    </main>
  );
}
