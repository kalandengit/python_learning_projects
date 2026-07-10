-- Sprint 12: beta launch support, feedback capture, and onboarding state.
create table if not exists public.feedback_submissions (
  id uuid primary key default gen_random_uuid(),
  type text not null default 'contact',
  email text not null,
  company text,
  message text not null,
  status text not null default 'new' check (status in ('new', 'reviewed', 'closed')),
  created_at timestamptz not null default now()
);

alter table public.feedback_submissions enable row level security;

drop policy if exists "Admins can read feedback" on public.feedback_submissions;
create policy "Admins can read feedback" on public.feedback_submissions
for select using (
  exists (
    select 1 from public.organization_members om
    where om.user_id = auth.uid() and om.role in ('owner', 'admin')
  )
);

-- Public insert is intentionally allowed for beta/contact forms. Protect with middleware/rate limiting before broad launch.
drop policy if exists "Anyone can submit feedback" on public.feedback_submissions;
create policy "Anyone can submit feedback" on public.feedback_submissions
for insert with check (true);

alter table public.profiles
  add column if not exists onboarding_completed_at timestamptz,
  add column if not exists launch_source text;

create index if not exists idx_feedback_submissions_created_at on public.feedback_submissions(created_at desc);
create index if not exists idx_feedback_submissions_type on public.feedback_submissions(type);
