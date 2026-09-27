-- 0004_cold_chain_events.sql
-- public.cold_chain_events: one row per manually-logged temperature
-- excursion against a saved report. Append-only history — logging a new
-- excursion never overwrites or deletes a prior one, or touches the
-- reports row it references.

create table if not exists public.cold_chain_events (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.reports (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  temperature_reached_c numeric not null,
  duration_hours numeric not null check (duration_hours >= 0),
  remaining_shelf_life_days numeric not null,
  action_urgent boolean not null,
  created_at timestamptz not null default now()
);

create index if not exists cold_chain_events_report_id_idx on public.cold_chain_events (report_id);
create index if not exists cold_chain_events_user_id_idx on public.cold_chain_events (user_id);

alter table public.cold_chain_events enable row level security;

-- Users can only see their own logged excursions
create policy "cold_chain_events_select_own"
  on public.cold_chain_events
  for select
  using (auth.uid() = user_id);

-- Users can only log excursions for themselves
create policy "cold_chain_events_insert_own"
  on public.cold_chain_events
  for insert
  with check (auth.uid() = user_id);

-- Users can only delete their own logged excursions — no update policy:
-- this is an append-only event log, not an editable record.
create policy "cold_chain_events_delete_own"
  on public.cold_chain_events
  for delete
  using (auth.uid() = user_id);
