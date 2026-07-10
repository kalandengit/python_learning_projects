# Production Readiness Checklist

## Required before beta
- [ ] Configure Supabase production project.
- [ ] Apply all migrations in order.
- [ ] Enable backups and point-in-time recovery where available.
- [ ] Configure Vercel production environment variables.
- [ ] Configure Stripe live products and webhook endpoint.
- [ ] Configure OpenAI API key and spending limits.
- [ ] Configure Resend production domain and sender.
- [ ] Configure Sentry project and DSN.
- [ ] Configure PostHog project and allowed domains.
- [ ] Confirm storage bucket privacy and signed URL behavior.
- [ ] Run `npm run ci` locally.
- [ ] Run `npm run build` with production env values.
- [ ] Run Playwright smoke tests against preview deployment.

## Security
- [ ] Verify RLS policies for every table.
- [ ] Confirm no service-role key is exposed to browser bundles.
- [ ] Confirm file upload size/type restrictions.
- [ ] Add malware scanning provider before enterprise rollout.
- [ ] Review CSP after all production domains are known.
- [ ] Rotate development secrets before launch.
- [ ] Enable GitHub branch protection.
- [ ] Enable Dependabot alerts.
- [ ] Add rate limits to public and AI-heavy endpoints.

## Reliability
- [ ] Configure AI worker process with Redis in production.
- [ ] Configure job retries and dead-letter handling.
- [ ] Add uptime monitoring.
- [ ] Add queue depth monitoring.
- [ ] Add alerts for failed AI jobs.
- [ ] Add alerts for Stripe webhook failures.

## Product analytics
- [ ] Track activation: signup → first upload → first document → first export/share.
- [ ] Track AI cost per generated document.
- [ ] Track quota limit hits.
- [ ] Track trial-to-paid conversion.
- [ ] Track retention by workspace.

## Launch readiness
- [ ] Landing page final copy.
- [ ] Pricing verified in Stripe live mode.
- [ ] Support email configured.
- [ ] Terms and privacy policy added.
- [ ] Product Hunt assets ready.
- [ ] Onboarding demo video recorded.
