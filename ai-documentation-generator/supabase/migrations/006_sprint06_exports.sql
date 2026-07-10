-- Sprint 06: export audit records and share/export hardening.
-- Export rows are valuable for analytics, billing limits, and compliance audit trails.

create table if not exists public.exports (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  format text not null check (format in ('markdown', 'html', 'pdf')),
  status text not null check (status in ('created', 'failed')),
  file_name text,
  error_message text,
  created_at timestamptz not null default now()
);

create index if not exists idx_exports_organization_created_at on public.exports(organization_id, created_at desc);
create index if not exists idx_exports_document_created_at on public.exports(document_id, created_at desc);
create index if not exists idx_exports_user_created_at on public.exports(user_id, created_at desc);

alter table public.exports enable row level security;

create policy "members can read organization exports" on public.exports
for select using (
  exists (
    select 1 from public.organization_members m
    where m.organization_id = exports.organization_id
      and m.user_id = auth.uid()
  )
);

create policy "members can create organization exports" on public.exports
for insert with check (
  exists (
    select 1 from public.organization_members m
    where m.organization_id = exports.organization_id
      and m.user_id = auth.uid()
  )
);

-- Keep share tokens unique. Existing null values are allowed.
create unique index if not exists idx_documents_share_token_unique
on public.documents(share_token)
where share_token is not null;
