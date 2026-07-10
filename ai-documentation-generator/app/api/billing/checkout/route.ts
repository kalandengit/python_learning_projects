import { NextResponse } from "next/server";
import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { getOrCreateDefaultOrganization } from "@/lib/data/organizations";
import { createAdminClient } from "@/lib/supabase/admin";
import { getStripe } from "@/lib/billing/stripe";
import { getStripePriceId, PAID_PLANS } from "@/lib/billing/plans";

const schema = z.object({ plan: z.enum(PAID_PLANS as ["starter", "pro", "business"]) });

export async function POST(request: Request) {
  try {
    const { user } = await requireUser();
    const org = await getOrCreateDefaultOrganization();
    const { plan } = schema.parse(await request.json());
    const priceId = getStripePriceId(plan);
    if (!priceId) return NextResponse.json({ error: `Missing Stripe price env for ${plan}` }, { status: 500 });

    const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
    const stripe = getStripe();
    const admin = createAdminClient();

    const { data: existingCustomer } = await admin
      .from("customers")
      .select("stripe_customer_id")
      .eq("organization_id", org.id)
      .maybeSingle();

    let customerId = existingCustomer?.stripe_customer_id as string | undefined;
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email ?? undefined,
        name: org.name,
        metadata: { organization_id: org.id, user_id: user.id }
      });
      customerId = customer.id;
      const { error } = await admin.from("customers").insert({ organization_id: org.id, stripe_customer_id: customerId });
      if (error) throw error;
    }

    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${appUrl}/billing?checkout=success`,
      cancel_url: `${appUrl}/billing?checkout=cancelled`,
      allow_promotion_codes: true,
      subscription_data: { metadata: { organization_id: org.id, plan } },
      metadata: { organization_id: org.id, plan }
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Checkout failed" }, { status: 400 });
  }
}
