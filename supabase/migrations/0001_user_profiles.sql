-- 0001_user_profiles.sql
-- public.user_profiles: one row per authenticated user, keyed to auth.users

create table if not exists public.user_profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  avatar_url text,
  preferred_budget_tier text check (preferred_budget_tier in ('low', 'medium', 'high')),
  prioritize_sustainability boolean not null default false,
  created_at timestamptz not null default now()
);

alter table public.user_profiles enable row level security;

-- Users can only see their own profile
create policy "user_profiles_select_own"
  on public.user_profiles
  for select
  using (auth.uid() = user_id);

-- Users can only insert a profile row for themselves
create policy "user_profiles_insert_own"
  on public.user_profiles
  for insert
  with check (auth.uid() = user_id);

-- Users can only update their own profile
create policy "user_profiles_update_own"
  on public.user_profiles
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Users can only delete their own profile
create policy "user_profiles_delete_own"
  on public.user_profiles
  for delete
  using (auth.uid() = user_id);
