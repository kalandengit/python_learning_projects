-- Sprint 02 persistence hardening. Run after 001_initial_schema.sql.

alter table public.projects add column if not exists description text;
alter table public.projects add column if not exists updated_at timestamptz not null default now();
alter table public.uploads add column if not exists project_id uuid references public.projects(id) on delete set null;
alter table public.uploads add column if not exists error_message text;
alter table public.uploads add column if not exists updated_at timestamptz not null default now();
alter table public.documents add column if not exists project_id uuid references public.projects(id) on delete set null;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_organizations_updated_at on public.organizations;
create trigger set_organizations_updated_at before update on public.organizations for each row execute function public.set_updated_at();
drop trigger if exists set_projects_updated_at on public.projects;
create trigger set_projects_updated_at before update on public.projects for each row execute function public.set_updated_at();
drop trigger if exists set_uploads_updated_at on public.uploads;
create trigger set_uploads_updated_at before update on public.uploads for each row execute function public.set_updated_at();
drop trigger if exists set_documents_updated_at on public.documents;
create trigger set_documents_updated_at before update on public.documents for each row execute function public.set_updated_at();

create index if not exists idx_members_user on public.organization_members(user_id);
create index if not exists idx_projects_org on public.projects(organization_id);
create index if not exists idx_uploads_org on public.uploads(organization_id);
create index if not exists idx_uploads_project on public.uploads(project_id);
create index if not exists idx_documents_org on public.documents(organization_id);
create index if not exists idx_documents_project on public.documents(project_id);
create index if not exists idx_documents_share_token on public.documents(share_token);

-- Replace broad MVP policies with organization-aware policies where possible.
drop policy if exists "users own uploads" on public.uploads;
drop policy if exists "users own documents" on public.documents;
drop policy if exists "members can read memberships" on public.organization_members;
drop policy if exists "owners can insert membership" on public.organization_members;

create policy "members can read memberships" on public.organization_members
for select using (
  user_id = auth.uid()
  or exists (select 1 from public.organization_members m where m.organization_id = organization_members.organization_id and m.user_id = auth.uid())
);

create policy "owners can insert membership" on public.organization_members
for insert with check (
  user_id = auth.uid()
  or exists (select 1 from public.organization_members m where m.organization_id = organization_members.organization_id and m.user_id = auth.uid() and m.role in ('owner','admin'))
);

create policy "members can manage projects" on public.projects
for all using (
  exists (select 1 from public.organization_members m where m.organization_id = projects.organization_id and m.user_id = auth.uid())
) with check (
  exists (select 1 from public.organization_members m where m.organization_id = projects.organization_id and m.user_id = auth.uid())
);

create policy "members can manage uploads" on public.uploads
for all using (
  exists (select 1 from public.organization_members m where m.organization_id = uploads.organization_id and m.user_id = auth.uid())
) with check (
  exists (select 1 from public.organization_members m where m.organization_id = uploads.organization_id and m.user_id = auth.uid())
);

create policy "members can manage documents" on public.documents
for all using (
  exists (select 1 from public.organization_members m where m.organization_id = documents.organization_id and m.user_id = auth.uid())
) with check (
  exists (select 1 from public.organization_members m where m.organization_id = documents.organization_id and m.user_id = auth.uid())
);

create policy "members can insert usage events" on public.usage_events
for insert with check (
  user_id = auth.uid()
  and exists (select 1 from public.organization_members m where m.organization_id = usage_events.organization_id and m.user_id = auth.uid())
);

-- Private upload bucket. Storage RLS still protects objects; app creates signed URLs for previews/AI.
insert into storage.buckets (id, name, public)
values ('uploads', 'uploads', false)
on conflict (id) do nothing;

create policy "members can upload organization files" on storage.objects
for insert with check (
  bucket_id = 'uploads'
  and exists (
    select 1 from public.organization_members m
    where m.organization_id::text = (storage.foldername(name))[1]
    and m.user_id = auth.uid()
  )
);

create policy "members can read organization files" on storage.objects
for select using (
  bucket_id = 'uploads'
  and exists (
    select 1 from public.organization_members m
    where m.organization_id::text = (storage.foldername(name))[1]
    and m.user_id = auth.uid()
  )
);
