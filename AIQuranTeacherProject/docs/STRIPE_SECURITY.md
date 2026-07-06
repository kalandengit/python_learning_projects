# Stripe Integration — Security Review

Security rules and controls for the payments/subscriptions integration
(`backend/src/billing`, `backend/src/common/stripe`). Mapped to Stripe's
official guidance and OWASP.

## 1. Card data never touches our servers (PCI DSS)
- We use **Stripe Checkout** (hosted) and the **Billing Portal** — the customer
  enters card details on Stripe-hosted pages, not ours.
- No PAN/CVV/expiry is ever received, logged, or stored by this backend. This
  keeps us in the smallest PCI scope (**SAQ A**).
- **Rule:** never add a raw-card endpoint. If you ever need in-app card fields,
  use Stripe Elements/PaymentElement (tokenized client-side) — still SAQ A.

## 2. The client never sets the price
- Clients send a **plan key** (`premium_monthly` / `premium_yearly`), validated
  against an allow-list (`@IsIn`). The server maps it to a Stripe **price ID**
  from configuration (`STRIPE_PRICE_*`).
- **Rule:** never accept an amount, currency, or price ID from the client — a
  tampered request could otherwise create a $0 or attacker-chosen charge.

## 3. Webhooks are authenticated by signature over the raw body
- The webhook endpoint verifies every event with
  `stripe.webhooks.constructEvent(rawBody, sig, webhookSecret)`.
- The app is created with `rawBody: true`; the **unparsed** body is used —
  a JSON-parsed body would fail verification.
- Missing/invalid signature → **400**, event rejected. This prevents forged
  events (e.g. a fake "subscription active") from granting access.
- **Rule:** the webhook is the only trusted source of subscription state.
  Never mark a user premium from a client "success" redirect alone.

## 4. Webhook handling is idempotent
- State is upserted by Stripe customer/subscription id, so Stripe's at-least-once
  retries (and duplicate deliveries) converge to the same result.
- Handlers acknowledge quickly (`200`); on error we return non-2xx so Stripe
  retries — safe because handling is idempotent.

## 5. Idempotent, safe write operations
- Checkout Session creation passes an **idempotency key**, so a retried request
  does not create duplicate sessions/charges.

## 6. Least-privilege, well-managed keys
- **Secret key** is server-only, read from env, never sent to clients or logged.
- **Publishable key** is the only key exposed to clients (`GET /billing/config`).
- **Webhook secret** validates event authenticity.
- **Rules for production:**
  - Use a **restricted** secret key scoped to only the resources used
    (Checkout, Customers, Subscriptions, Billing Portal).
  - Rotate keys periodically and on suspected exposure.
  - Store secrets in a secrets manager (not plaintext env in the image).
  - Use separate test/live keys per environment.

## 7. AuthN / AuthZ on billing routes
- All billing actions require a valid JWT (global `JwtAuthGuard`).
- Checkout/portal act on **the authenticated user's** own customer record only —
  a user cannot start checkout or open a portal for someone else.
- The webhook is `@Public()` (Stripe is not a logged-in user) but is
  authenticated by signature (see §3).

## 8. The premium whitelist is admin-only and audited
- Granting/revoking free access is restricted to `role = admin` via `RolesGuard`
  (the role is read live from the DB, so revoking admin takes effect immediately —
  it is not baked into the JWT).
- Each grant records `grantedBy` (acting admin) and an optional `expiresAt`
  for time-boxed comp access; expiry is enforced on every entitlement check.
- **Rule:** keep the admin role tightly controlled; the whitelist bypasses
  payment.

## 9. Abuse & transport
- Checkout/portal endpoints are rate-limited (`@Throttle`) on top of the global
  limiter, to blunt session-creation abuse.
- All traffic is HTTPS in production; webhook URLs must be HTTPS.

## 10. Data minimization
- We store only what entitlement checks need: Stripe customer/subscription ids,
  status, plan, period end. No card data, no full Stripe event payloads.

---

## Pre-production checklist
- [ ] Restricted live secret key in a secrets manager; test keys elsewhere.
- [ ] Webhook endpoint registered in Stripe with the correct events and secret.
- [ ] `STRIPE_PRICE_*` point to live prices; amounts verified in the dashboard.
- [ ] Verify signature failures are alerted/monitored (possible attack or misconfig).
- [ ] Confirm entitlement is derived from webhook state, not client redirects.
- [ ] Load-test webhook idempotency (replay the same event).
- [ ] Review admin list; ensure least privilege for the whitelist.

## Handled webhook events
| Event | Effect |
| --- | --- |
| `checkout.session.completed` | Fetch subscription, sync local state |
| `customer.subscription.created` / `updated` | Sync status, plan, period end, cancel flag |
| `customer.subscription.deleted` | Mark canceled (premium ends) |

Unlisted events are acknowledged (`200`) and ignored.
