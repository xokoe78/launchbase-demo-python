-- Apply once to the app's database using Launchbase database migrations.
create table if not exists public.client_requests (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
 title text not null check(length(title) between 1 and 120),
 description text not null check(length(description) between 1 and 3000),
 category text not null check(category in ('Website','Brand','Content','Other')),
 status text not null default 'new' check(status in ('new','in_progress','done')),
 created_at timestamptz not null default now()
);
alter table public.client_requests enable row level security;
revoke all on public.client_requests from anon;
grant select,insert,update,delete on public.client_requests to authenticated;
drop policy if exists own_requests on public.client_requests;
create policy own_requests on public.client_requests for all to authenticated
 using(user_id=auth.uid()) with check(user_id=auth.uid());
create index if not exists client_requests_user_created on public.client_requests(user_id,created_at desc);
