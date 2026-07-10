-- Sprint 09: team collaboration, invitations, roles, and organization-scoped permissions.
-- Apply after 008_sprint08_analytics_admin.sql.

-- Role helper functions live in Postgres so RLS policies stay centralized and cannot be bypassed by client code.
create or replace function public.current_user_org_role(org_id uuid)
returns text
language sql
security definer
set search_path = public
stable
as $$
  select om.role
  from public.organization_members om
  where om.organization_id = org_id
    and om.user_id = auth.uid()
  limit 1;
$$;

create or replace function public.is_org_member(org_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.organization_members om
    where om.organization_id = org_id
      and om.user_id = auth.uid()
  );
$$;

create or replace function public.is_org_admin(org_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select coalesce(public.current_user_org_role(org_id) in ('owner', 'admin'), false);
$$;

create or replace function public.is_org_owner(org_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select coalesce(public.current_user_org_role(org_id) = 'owner', false);
$$;

grant execute on function public.current_user_org_role(uuid) to authenticated;
grant execute on function public.is_org_member(uuid) to authenticated;
grant execute on function public.is_org_admin(uuid) to authenticated;
grant execute on function public.is_org_owner(uuid) to authenticated;

alter table public.organization_members
  add column if not exists invited_by uuid references auth.users(id) on delete set null,
  add column if not exists joined_at timestamptz default now();

create table if not exists public.organization_invitations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  email text not null,
  role text not null check (role in ('admin', 'member')),
  token text not null unique,
  status text not null default 'pending' check (status in ('pending', 'accepted', 'revoked', 'expired')),
  invited_by uuid not null references auth.users(id) on delete cascade,
  accepted_by uuid references auth.users(id) on delete set null,
  accepted_at timestamptz,
  expires_at timestamptz not null default (now() + interval '7 days'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists organization_members_org_role_idx on public.organization_members (organization_id, role);
create index if not exists organization_members_user_idx on public.organization_members (user_id);
create index if not exists organization_invitations_org_status_idx on public.organization_invitations (organization_id, status, created_at desc);
create index if not exists organization_invitations_email_status_idx on public.organization_invitations (lower(email), status);
create unique index if not exists organization_invitations_one_pending_email_idx
  on public.organization_invitations (organization_id, lower(email))
  where status = 'pending' and accepted_at is null;

alter table public.organization_invitations enable row level security;

-- Replace the early MVP self-insert membership policy with invitation/owner-aware rules.
drop policy if exists "owners can insert membership" on public.organization_members;

create policy "Owners and invited users can insert memberships" on public.organization_members
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and (
      exists (
        select 1 from public.organizations o
        where o.id = organization_members.organization_id
          and o.owner_id = auth.uid()
      )
      or exists (
        select 1 from public.organization_invitations oi
        where oi.organization_id = organization_members.organization_id
          and oi.role = organization_members.role
          and oi.status = 'pending'
          and oi.accepted_at is null
          and oi.expires_at > now()
          and lower(oi.email) = lower(coalesce(auth.jwt() ->> 'email', ''))
      )
    )
  );

create policy "Members can read team roster" on public.organization_members
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Owners can update member roles" on public.organization_members
  for update to authenticated
  using (public.is_org_owner(organization_id) and role <> 'owner')
  with check (public.is_org_owner(organization_id) and role in ('admin', 'member'));

create policy "Owners can remove non-owner members" on public.organization_members
  for delete to authenticated
  using (public.is_org_owner(organization_id) and role <> 'owner' and user_id <> auth.uid());

create policy "Admins can read invitations" on public.organization_invitations
  for select to authenticated
  using (public.is_org_admin(organization_id));

create policy "Invited users can read their own pending invitations" on public.organization_invitations
  for select to authenticated
  using (
    status = 'pending'
    and accepted_at is null
    and lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  );

create policy "Admins can create invitations" on public.organization_invitations
  for insert to authenticated
  with check (public.is_org_admin(organization_id) and invited_by = auth.uid());

create policy "Admins can revoke invitations" on public.organization_invitations
  for update to authenticated
  using (public.is_org_admin(organization_id))
  with check (public.is_org_admin(organization_id));

create policy "Invited users can accept invitations" on public.organization_invitations
  for update to authenticated
  using (
    status = 'pending'
    and accepted_at is null
    and lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  )
  with check (
    status = 'accepted'
    and accepted_by = auth.uid()
    and lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''))
  );

-- Expand MVP permissions from creator-owned rows to organization collaboration.
create policy "Org members can read projects" on public.projects
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Org members can create projects" on public.projects
  for insert to authenticated
  with check (public.is_org_member(organization_id) and created_by = auth.uid());

create policy "Admins can manage projects" on public.projects
  for update to authenticated
  using (public.is_org_admin(organization_id))
  with check (public.is_org_admin(organization_id));

create policy "Org members can read uploads" on public.uploads
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Org members can create uploads" on public.uploads
  for insert to authenticated
  with check (public.is_org_member(organization_id) and user_id = auth.uid());

create policy "Org members can update own uploads" on public.uploads
  for update to authenticated
  using (public.is_org_member(organization_id) and (user_id = auth.uid() or public.is_org_admin(organization_id)))
  with check (public.is_org_member(organization_id));

create policy "Org members can read documents" on public.documents
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Org members can create documents" on public.documents
  for insert to authenticated
  with check (public.is_org_member(organization_id) and created_by = auth.uid());

create policy "Org members can edit documents" on public.documents
  for update to authenticated
  using (public.is_org_member(organization_id))
  with check (public.is_org_member(organization_id));

create policy "Org members can read exports" on public.exports
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Org members can read document versions" on public.document_versions
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Org members can read ai jobs" on public.ai_jobs
  for select to authenticated
  using (public.is_org_member(organization_id));

create policy "Org members can read usage events" on public.usage_events
  for select to authenticated
  using (public.is_org_member(organization_id));
