-- Sprint 07: Stripe billing, plan quotas, and subscription state.

create table if not exists public.customers (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null unique references public.organizations(id) on delete cascade,
  stripe_customer_id text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null unique references public.organizations(id) on delete cascade,
  stripe_subscription_id text unique,
  stripe_customer_id text,
  stripe_price_id text,
  plan text not null default 'free' check (plan in ('free','starter','pro','business','enterprise')),
  status text not null default 'active',
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  trial_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.billing_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  stripe_event_id text not null unique,
  event_type text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.organizations add column if not exists billing_email text;
alter table public.customers enable row level security;
alter table public.subscriptions enable row level security;
alter table public.billing_events enable row level security;

drop trigger if exists set_customers_updated_at on public.customers;
create trigger set_customers_updated_at before update on public.customers for each row execute function public.set_updated_at();

drop trigger if exists set_subscriptions_updated_at on public.subscriptions;
create trigger set_subscriptions_updated_at before update on public.subscriptions for each row execute function public.set_updated_at();

create index if not exists idx_customers_org on public.customers(organization_id);
create index if not exists idx_customers_stripe_customer on public.customers(stripe_customer_id);
create index if not exists idx_subscriptions_org on public.subscriptions(organization_id);
create index if not exists idx_subscriptions_stripe_subscription on public.subscriptions(stripe_subscription_id);
create index if not exists idx_billing_events_org on public.billing_events(organization_id);
create index if not exists idx_usage_events_org_type_created on public.usage_events(organization_id, event_type, created_at desc);

create policy "members can read customer mapping" on public.customers
for select using (
  exists (select 1 from public.organization_members m where m.organization_id = customers.organization_id and m.user_id = auth.uid())
);

create policy "members can read subscriptions" on public.subscriptions
for select using (
  exists (select 1 from public.organization_members m where m.organization_id = subscriptions.organization_id and m.user_id = auth.uid())
);

create policy "admins can manage subscriptions" on public.subscriptions
for update using (
  exists (select 1 from public.organization_members m where m.organization_id = subscriptions.organization_id and m.user_id = auth.uid() and m.role in ('owner','admin'))
) with check (
  exists (select 1 from public.organization_members m where m.organization_id = subscriptions.organization_id and m.user_id = auth.uid() and m.role in ('owner','admin'))
);

create policy "admins can read billing events" on public.billing_events
for select using (
  exists (select 1 from public.organization_members m where m.organization_id = billing_events.organization_id and m.user_id = auth.uid() and m.role in ('owner','admin'))
);

-- Service role writes subscription/customer/billing events from Stripe webhook and checkout routes.
