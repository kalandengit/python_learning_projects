-- Sprint 03: AI pipeline hardening, job tracking, and usage telemetry.

create table if not exists public.ai_jobs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  upload_id uuid references public.uploads(id) on delete set null,
  document_id uuid references public.documents(id) on delete set null,
  user_id uuid not null references auth.users(id) on delete cascade,
  job_type text not null check (job_type in ('document_generation')),
  status text not null default 'queued' check (status in ('queued','processing','completed','failed')),
  provider text not null default 'openai',
  model text,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  total_tokens integer not null default 0,
  estimated_cost_usd numeric(12,6) not null default 0,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_ai_jobs_org on public.ai_jobs(organization_id);
create index if not exists idx_ai_jobs_upload on public.ai_jobs(upload_id);
create index if not exists idx_ai_jobs_document on public.ai_jobs(document_id);
create index if not exists idx_ai_jobs_status on public.ai_jobs(status);
create index if not exists idx_ai_jobs_created_at on public.ai_jobs(created_at desc);

drop trigger if exists set_ai_jobs_updated_at on public.ai_jobs;
create trigger set_ai_jobs_updated_at before update on public.ai_jobs for each row execute function public.set_updated_at();

alter table public.ai_jobs enable row level security;

create policy "members can read ai jobs" on public.ai_jobs
for select using (
  exists (select 1 from public.organization_members m where m.organization_id = ai_jobs.organization_id and m.user_id = auth.uid())
);

create policy "members can insert ai jobs" on public.ai_jobs
for insert with check (
  user_id = auth.uid()
  and exists (select 1 from public.organization_members m where m.organization_id = ai_jobs.organization_id and m.user_id = auth.uid())
);

create policy "members can update ai jobs" on public.ai_jobs
for update using (
  exists (select 1 from public.organization_members m where m.organization_id = ai_jobs.organization_id and m.user_id = auth.uid())
) with check (
  exists (select 1 from public.organization_members m where m.organization_id = ai_jobs.organization_id and m.user_id = auth.uid())
);

create or replace view public.organization_ai_usage_daily as
select
  organization_id,
  date_trunc('day', created_at)::date as usage_date,
  count(*) filter (where status = 'completed') as completed_jobs,
  count(*) filter (where status = 'failed') as failed_jobs,
  coalesce(sum(total_tokens), 0) as total_tokens,
  coalesce(sum(estimated_cost_usd), 0) as estimated_cost_usd
from public.ai_jobs
group by organization_id, date_trunc('day', created_at)::date;
