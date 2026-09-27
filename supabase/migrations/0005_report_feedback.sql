-- 0005_report_feedback.sql
-- Adds optional user feedback on a saved report's accuracy. Pure data
-- capture — no retraining/auto-improvement logic reads these columns
-- anywhere in this codebase; they exist only to be collected and, later,
-- reviewed by a human.

alter table public.reports
  add column if not exists feedback_outcome text
    check (feedback_outcome in ('spoiled_early', 'as_expected', 'lasted_longer')),
  add column if not exists feedback_submitted_at timestamptz;

-- No new RLS policies needed: the existing reports_update_own policy
-- (0002_reports.sql) already lets a user update only their own rows, which
-- is exactly what submitting feedback does (a PATCH on these two columns).
