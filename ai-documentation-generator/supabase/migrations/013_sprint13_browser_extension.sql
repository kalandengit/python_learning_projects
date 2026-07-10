alter table public.uploads add column if not exists source_url text;
alter table public.uploads add column if not exists source_title text;
alter table public.uploads add column if not exists capture_mode text check (capture_mode in ('visible','region','full_page'));
-- Sprint 13: scoped browser-extension access tokens.
create table if not exists public.extension_tokens (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null default 'Browser extension',
  token_prefix text not null,
  token_hash text not null unique,
  scopes text[] not null default array['capture:write','projects:read','jobs:read']::text[],
  last_used_at timestamptz,
  expires_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists extension_tokens_user_idx on public.extension_tokens(user_id, created_at desc);
create index if not exists extension_tokens_hash_idx on public.extension_tokens(token_hash) where revoked_at is null;
alter table public.extension_tokens enable row level security;
create policy "Users manage their extension tokens" on public.extension_tokens
for all using (user_id = auth.uid()) with check (
  user_id = auth.uid() and exists (
    select 1 from public.organization_members om
    where om.organization_id = extension_tokens.organization_id and om.user_id = auth.uid()
  )
);
