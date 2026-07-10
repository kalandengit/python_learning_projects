-- Sprint 08: product analytics, admin visibility, onboarding metrics, and feature flags.
-- Apply after 007_sprint07_billing.sql.

create table if not exists analytics_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  event_name text not null,
  source text not null default 'server',
  properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists analytics_events_org_created_idx on analytics_events (organization_id, created_at desc);
create index if not exists analytics_events_org_event_idx on analytics_events (organization_id, event_name, created_at desc);
create index if not exists analytics_events_user_idx on analytics_events (user_id, created_at desc);

alter table analytics_events enable row level security;

create policy "Members can read org analytics events" on analytics_events
  for select using (
    exists (
      select 1 from organization_members om
      where om.organization_id = analytics_events.organization_id
      and om.user_id = auth.uid()
    )
  );

create policy "Members can create org analytics events" on analytics_events
  for insert with check (
    auth.uid() = user_id
    and exists (
      select 1 from organization_members om
      where om.organization_id = analytics_events.organization_id
      and om.user_id = auth.uid()
    )
  );

create table if not exists feature_flags (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references organizations(id) on delete cascade,
  key text not null,
  description text,
  enabled boolean not null default false,
  rollout_percentage integer not null default 0 check (rollout_percentage >= 0 and rollout_percentage <= 100),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, key)
);

create index if not exists feature_flags_org_key_idx on feature_flags (organization_id, key);
alter table feature_flags enable row level security;

create policy "Members can read org feature flags" on feature_flags
  for select using (
    organization_id is null or exists (
      select 1 from organization_members om
      where om.organization_id = feature_flags.organization_id
      and om.user_id = auth.uid()
    )
  );

-- Admin visibility rollups. These are intentionally organization-scoped.
create or replace view organization_analytics_summary as
select
  o.id as organization_id,
  count(distinct p.id) as projects_count,
  count(distinct u.id) as uploads_count,
  count(distinct d.id) as documents_count,
  count(distinct e.id) filter (where e.created_at >= now() - interval '30 days') as events_30d,
  count(distinct aj.id) as ai_jobs_count,
  count(distinct aj.id) filter (where aj.status = 'completed') as completed_ai_jobs_count,
  count(distinct ex.id) as exports_count,
  coalesce(sum((aj.usage ->> 'estimatedCostUsd')::numeric), 0) as estimated_ai_cost_usd
from organizations o
left join projects p on p.organization_id = o.id
left join uploads u on u.organization_id = o.id
left join documents d on d.organization_id = o.id
left join analytics_events e on e.organization_id = o.id
left join ai_jobs aj on aj.organization_id = o.id
left join exports ex on ex.organization_id = o.id
group by o.id;

create or replace view onboarding_funnel_summary as
select
  organization_id,
  count(*) filter (where event_name = 'workspace_created') as workspace_created,
  count(*) filter (where event_name = 'project_created') as project_created,
  count(*) filter (where event_name = 'upload_created') as upload_created,
  count(*) filter (where event_name = 'ai_generation_requested') as ai_generation_requested,
  count(*) filter (where event_name = 'document_created') as document_created,
  count(*) filter (where event_name = 'export_created') as export_created,
  count(*) filter (where event_name = 'share_viewed') as share_viewed
from analytics_events
group by organization_id;
