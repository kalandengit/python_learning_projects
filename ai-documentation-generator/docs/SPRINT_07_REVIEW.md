# Sprint 07 Review — Stripe Billing, Plans, Quotas

## Completed
- Added Stripe Checkout session route for Starter, Pro, and Business plans.
- Added Stripe Customer Portal route for self-service subscription management.
- Added Stripe webhook route with signature verification and subscription synchronization.
- Added `customers`, `subscriptions`, and `billing_events` tables with RLS policies.
- Added billing dashboard with current plan, monthly upload usage, and monthly AI document usage.
- Added public pricing page.
- Added quota checks before screenshot upload and AI document generation.
- Added usage event recording for uploads and generated documents.

## Security Review
- Stripe webhook validates `stripe-signature` before processing events.
- Service-role Supabase client is isolated to trusted server routes.
- Billing tables use RLS for member/admin reads.
- Client never receives Stripe secret keys or service-role keys.

## Tradeoffs
- MVP uses fixed monthly subscription quotas instead of metered billing. This is simpler to launch and easier for customers to understand.
- Webhook sync is the source of truth for subscription state. Checkout success alone is not trusted for entitlement changes.
- Billing portal is delegated to Stripe instead of building custom subscription-management UI.

## Manual Setup Required
1. Create Stripe products and recurring monthly prices.
2. Add price IDs to `.env`.
3. Configure the Stripe customer portal in the Stripe Dashboard.
4. Add webhook endpoint: `/api/stripe/webhook`.
5. Subscribe webhook to `customer.subscription.created`, `customer.subscription.updated`, and `customer.subscription.deleted`.

## Known Gaps
- No team seat enforcement yet.
- No storage quota enforcement yet.
- No invoice list inside app yet; users manage invoices in Stripe Portal.
- Webhook idempotency is protected by unique `stripe_event_id`, but duplicate insert errors are not silently ignored yet.

## Next Sprint
Sprint 08 should add analytics, event dashboards, onboarding activation metrics, and basic admin visibility.
