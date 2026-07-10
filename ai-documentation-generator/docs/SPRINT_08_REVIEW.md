# Sprint 08 Review — Analytics, Admin Visibility, and Onboarding Metrics

## Goal
Add first-party analytics, PostHog integration, onboarding funnel metrics, and internal admin visibility without blocking the MVP on a third-party analytics provider.

## What changed
- Added `analytics_events` table with organization-scoped RLS.
- Added `feature_flags` table for controlled rollout foundations.
- Added analytics rollup views for workspace health and onboarding funnel.
- Added server-side analytics capture with optional PostHog mirroring.
- Added client-side PostHog provider for pageviews and future product events.
- Added `/analytics` dashboard with metrics, funnel, top events, and recent stream.
- Added `/admin` workspace health page for operator visibility.
- Instrumented projects, uploads, AI generation requests, generated documents, exports, document saves, share links, and restores.

## Architecture decisions
1. **First-party event store first**
   Analytics events are saved to Supabase before optional external capture. This prevents product KPIs from disappearing if PostHog is disabled or misconfigured.

2. **PostHog is optional**
   The app works without PostHog env vars. This keeps local development and early deployment simple.

3. **Organization-scoped analytics**
   All analytics are keyed by `organization_id`, matching the SaaS multi-tenant model.

4. **Views instead of heavy app-side aggregation**
   MVP analytics use SQL views for simple rollups. Later sprints can replace this with materialized views or a warehouse.

## Security review
- RLS is enabled on new tables.
- Members can only read events for organizations they belong to.
- Event insert policies require matching authenticated users.
- Server and worker events use the service role through controlled server-side code only.

## Tradeoffs
- The admin page is workspace-local in Sprint 08. A true platform-super-admin role will be introduced later.
- Charts use lightweight CSS instead of a charting dependency to keep the MVP smaller.
- Event properties are JSONB for flexibility; high-cardinality indexes are intentionally avoided until usage patterns are proven.

## Definition of done
- New migration created.
- New pages added to the dashboard sidebar.
- Key product actions emit durable analytics events.
- PostHog integration is configurable through environment variables.
- Recap files updated.

## Next sprint recommendation
Sprint 09 should add role-based team collaboration: organization roles, invitations, team member management, and route-level permissions.
