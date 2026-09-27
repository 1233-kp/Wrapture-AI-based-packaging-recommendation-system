-- 0002_reports.sql
-- public.reports: one row per recommendation report a user generates and saves

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  commodity_name text not null,
  input_conditions jsonb not null default '{}'::jsonb,
  recommendation jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists reports_user_id_idx on public.reports (user_id);

alter table public.reports enable row level security;

-- Users can only see their own reports
create policy "reports_select_own"
  on public.reports
  for select
  using (auth.uid() = user_id);

-- Users can only insert reports for themselves
create policy "reports_insert_own"
  on public.reports
  for insert
  with check (auth.uid() = user_id);

-- Users can only update their own reports
create policy "reports_update_own"
  on public.reports
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Users can only delete their own reports
create policy "reports_delete_own"
  on public.reports
  for delete
  using (auth.uid() = user_id);
