-- Sprint 05: document editor hardening and version history.
-- Run after 004_sprint04_background_jobs.sql.

alter table public.documents add column if not exists excerpt text;
alter table public.documents add column if not exists word_count integer not null default 0;
alter table public.documents add column if not exists last_edited_by uuid references auth.users(id) on delete set null;
alter table public.documents add column if not exists last_saved_at timestamptz;

create table if not exists public.document_versions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  version_number integer not null,
  title text not null,
  content_markdown text not null,
  content_json jsonb,
  change_summary text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique(document_id, version_number)
);

create index if not exists idx_document_versions_org on public.document_versions(organization_id);
create index if not exists idx_document_versions_document on public.document_versions(document_id);
create index if not exists idx_document_versions_created_at on public.document_versions(created_at desc);

alter table public.document_versions enable row level security;

create policy "members can read document versions" on public.document_versions
for select using (
  exists (select 1 from public.organization_members m where m.organization_id = document_versions.organization_id and m.user_id = auth.uid())
);

create policy "members can create document versions" on public.document_versions
for insert with check (
  exists (select 1 from public.organization_members m where m.organization_id = document_versions.organization_id and m.user_id = auth.uid())
);

create or replace function public.next_document_version_number(target_document_id uuid)
returns integer
language sql
stable
as $$
  select coalesce(max(version_number), 0) + 1
  from public.document_versions
  where document_id = target_document_id;
$$;

create or replace function public.document_word_count(markdown text)
returns integer
language sql
immutable
as $$
  select case
    when markdown is null or length(trim(markdown)) = 0 then 0
    else array_length(regexp_split_to_array(trim(regexp_replace(markdown, '[#*_>`~\[\]()]', ' ', 'g')), '\s+'), 1)
  end;
$$;

create or replace function public.document_excerpt(markdown text)
returns text
language sql
immutable
as $$
  select nullif(left(trim(regexp_replace(coalesce(markdown, ''), '\s+', ' ', 'g')), 220), '');
$$;

create or replace function public.set_document_metadata()
returns trigger
language plpgsql
as $$
begin
  new.word_count = public.document_word_count(new.content_markdown);
  new.excerpt = public.document_excerpt(new.content_markdown);
  new.last_saved_at = now();
  return new;
end;
$$;

drop trigger if exists set_documents_metadata on public.documents;
create trigger set_documents_metadata
before insert or update of content_markdown on public.documents
for each row execute function public.set_document_metadata();
