create extension if not exists "uuid-ossp";

create table public.organizations (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  owner_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.organization_members (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner','admin','member')),
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create table public.projects (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table public.uploads (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  storage_path text not null,
  file_name text not null,
  mime_type text not null,
  size_bytes bigint not null default 0,
  status text not null default 'uploaded' check (status in ('uploaded','processing','completed','failed')),
  created_at timestamptz not null default now()
);

create table public.documents (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid references public.organizations(id) on delete cascade,
  upload_id uuid references public.uploads(id) on delete set null,
  title text not null,
  slug text not null,
  content_json jsonb not null default '{}'::jsonb,
  content_markdown text not null default '',
  visibility text not null default 'private' check (visibility in ('private','shared','public')),
  share_token text unique,
  created_by uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.usage_events (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid references public.organizations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  event_type text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
alter table public.projects enable row level security;
alter table public.uploads enable row level security;
alter table public.documents enable row level security;
alter table public.usage_events enable row level security;

create policy "members can read orgs" on public.organizations for select using (
  exists (select 1 from public.organization_members m where m.organization_id = id and m.user_id = auth.uid())
);
create policy "users can create orgs" on public.organizations for insert with check (owner_id = auth.uid());

create policy "members can read memberships" on public.organization_members for select using (user_id = auth.uid());
create policy "owners can insert membership" on public.organization_members for insert with check (user_id = auth.uid());

create policy "users own uploads" on public.uploads for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "users own documents" on public.documents for all using (created_by = auth.uid()) with check (created_by = auth.uid());
create policy "public can read shared docs" on public.documents for select using (visibility in ('shared','public'));
create policy "users read own usage" on public.usage_events for select using (user_id = auth.uid());

insert into storage.buckets (id, name, public) values ('uploads', 'uploads', false) on conflict (id) do nothing;
