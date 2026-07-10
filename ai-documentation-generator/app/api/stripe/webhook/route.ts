import { headers } from "next/headers";
import { NextResponse } from "next/server";
import Stripe from "stripe";
import { getStripe } from "@/lib/billing/stripe";
import { createAdminClient } from "@/lib/supabase/admin";

export const dynamic = "force-dynamic";

function planFromPrice(priceId?: string | null) {
  const pairs = [
    [process.env.STRIPE_PRICE_STARTER_MONTHLY, "starter"],
    [process.env.STRIPE_PRICE_PRO_MONTHLY, "pro"],
    [process.env.STRIPE_PRICE_BUSINESS_MONTHLY, "business"]
  ] as const;
  return pairs.find(([id]) => id && id === priceId)?.[1] ?? "free";
}

async function upsertSubscription(subscription: Stripe.Subscription) {
  const admin = createAdminClient();
  const orgId = subscription.metadata.organization_id;
  const customerId = typeof subscription.customer === "string" ? subscription.customer : subscription.customer.id;
  const firstItem = subscription.items.data[0] ?? null;
  const priceId = firstItem?.price.id ?? null;
  if (!orgId) return;

  // Stripe API 2025-03-31+ (SDK v18+) moved current_period_* from the
  // subscription onto each subscription item.
  const periodStart = firstItem?.current_period_start ?? null;
  const periodEnd = firstItem?.current_period_end ?? null;

  await admin.from("subscriptions").upsert({
    organization_id: orgId,
    stripe_subscription_id: subscription.id,
    stripe_customer_id: customerId,
    stripe_price_id: priceId,
    plan: planFromPrice(priceId),
    status: subscription.status,
    current_period_start: periodStart ? new Date(periodStart * 1000).toISOString() : null,
    current_period_end: periodEnd ? new Date(periodEnd * 1000).toISOString() : null,
    cancel_at_period_end: subscription.cancel_at_period_end,
    trial_end: subscription.trial_end ? new Date(subscription.trial_end * 1000).toISOString() : null
  }, { onConflict: "organization_id" });
}

async function downgradeSubscription(subscription: Stripe.Subscription) {
  const admin = createAdminClient();
  const orgId = subscription.metadata.organization_id;
  if (!orgId) return;
  await admin.from("subscriptions").upsert({
    organization_id: orgId,
    stripe_subscription_id: subscription.id,
    stripe_customer_id: typeof subscription.customer === "string" ? subscription.customer : subscription.customer.id,
    plan: "free",
    status: subscription.status,
    cancel_at_period_end: false
  }, { onConflict: "organization_id" });
}

export async function POST(request: Request) {
  const stripe = getStripe();
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) return NextResponse.json({ error: "Missing webhook secret" }, { status: 500 });

  const rawBody = await request.text();
  const signature = (await headers()).get("stripe-signature");
  if (!signature) return NextResponse.json({ error: "Missing Stripe signature" }, { status: 400 });

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid signature" }, { status: 400 });
  }

  const admin = createAdminClient();
  try {
    if (event.type.startsWith("customer.subscription.")) {
      const subscription = event.data.object as Stripe.Subscription;
      if (event.type === "customer.subscription.deleted") await downgradeSubscription(subscription);
      else await upsertSubscription(subscription);

      const orgId = subscription.metadata.organization_id || null;
      await admin.from("billing_events").insert({ organization_id: orgId, stripe_event_id: event.id, event_type: event.type, payload: event as any });
    }
    return NextResponse.json({ received: true });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Webhook handler failed" }, { status: 500 });
  }
}
