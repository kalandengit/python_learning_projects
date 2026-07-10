"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PlanKey } from "@/lib/billing/plans";

export function PlanCard({ plan, name, price, features, current }: { plan: PlanKey; name: string; price: string; features: string[]; current?: boolean }) {
  const [loading, setLoading] = useState(false);

  async function subscribe() {
    if (plan === "free" || plan === "enterprise") return;
    setLoading(true);
    const response = await fetch("/api/billing/checkout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ plan })
    });
    const data = await response.json();
    setLoading(false);
    if (data.url) window.location.href = data.url;
    else alert(data.error ?? "Unable to start checkout.");
  }

  return (
    <Card className={current ? "border-slate-900" : undefined}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{name}</span>
          {current ? <span className="rounded-full bg-slate-900 px-2 py-1 text-xs text-white">Current</span> : null}
        </CardTitle>
        <p className="text-3xl font-bold">{price}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="space-y-2 text-sm text-slate-600">
          {features.map((feature) => <li key={feature}>✓ {feature}</li>)}
        </ul>
        {plan === "enterprise" ? (
          <a className="inline-flex w-full items-center justify-center rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800" href="mailto:sales@example.com">Contact sales</a>
        ) : plan === "free" ? (
          <Button disabled className="w-full" variant="secondary">Included</Button>
        ) : (
          <Button onClick={subscribe} disabled={loading || current} className="w-full">{loading ? "Opening..." : current ? "Active" : "Upgrade"}</Button>
        )}
      </CardContent>
    </Card>
  );
}
