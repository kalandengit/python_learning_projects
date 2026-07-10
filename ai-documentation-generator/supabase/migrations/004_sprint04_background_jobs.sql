-- Sprint 04: asynchronous job queue metadata and safer status transitions.

alter table public.ai_jobs
  add column if not exists queue_provider text default 'database' check (queue_provider in ('database','bullmq')),
  add column if not exists queue_job_id text,
  add column if not exists attempts integer not null default 0,
  add column if not exists max_attempts integer not null default 3,
  add column if not exists locked_at timestamptz,
  add column if not exists locked_by text;

-- Replace status constraint so the UI can support future cancellation without a destructive table rebuild.
do $$
declare
  constraint_name text;
begin
  select conname into constraint_name
  from pg_constraint
  where conrelid = 'public.ai_jobs'::regclass
    and contype = 'c'
    and pg_get_constraintdef(oid) like '%status%queued%processing%completed%failed%';

  if constraint_name is not null then
    execute format('alter table public.ai_jobs drop constraint %I', constraint_name);
  end if;
end $$;

alter table public.ai_jobs
  add constraint ai_jobs_status_check check (status in ('queued','processing','completed','failed','cancelled'));

create index if not exists idx_ai_jobs_queue_provider on public.ai_jobs(queue_provider);
create index if not exists idx_ai_jobs_queue_job_id on public.ai_jobs(queue_job_id);
create index if not exists idx_ai_jobs_pending on public.ai_jobs(status, created_at) where status in ('queued','processing');

create or replace view public.organization_ai_usage_daily as
select
  organization_id,
  date_trunc('day', created_at)::date as usage_date,
  count(*) filter (where status = 'completed') as completed_jobs,
  count(*) filter (where status = 'failed') as failed_jobs,
  count(*) filter (where status = 'cancelled') as cancelled_jobs,
  coalesce(sum(total_tokens), 0) as total_tokens,
  coalesce(sum(estimated_cost_usd), 0) as estimated_cost_usd
from public.ai_jobs
group by organization_id, date_trunc('day', created_at)::date;
