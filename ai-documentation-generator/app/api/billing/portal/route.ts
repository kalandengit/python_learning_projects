import { NextResponse } from "next/server";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import { createAdminClient } from "@/lib/supabase/admin";
import { getStripe } from "@/lib/billing/stripe";

export async function POST() {
  try {
    await requireUser();
    const org = await getOrCreateDefaultOrganization();
    const admin = createAdminClient();
    const { data: customer, error } = await admin
      .from("customers")
      .select("stripe_customer_id")
      .eq("organization_id", org.id)
      .maybeSingle();
    if (error) throw error;
    if (!customer?.stripe_customer_id) return NextResponse.json({ error: "No Stripe customer found yet." }, { status: 404 });

    const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
    const session = await getStripe().billingPortal.sessions.create({
      customer: customer.stripe_customer_id,
      return_url: `${appUrl}/billing`
    });
    return NextResponse.json({ url: session.url });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Portal failed" }, { status: 400 });
  }
}
