-- Limitation de débit API (register / validate) — clé service uniquement
create table public.openprivacy_rate_limits (
  bucket text primary key,
  hits integer not null default 1 check (hits >= 0),
  window_start timestamptz not null default now()
);

alter table public.openprivacy_rate_limits enable row level security;

comment on table public.openprivacy_rate_limits is
  'Compteurs rate-limit OpenPrivacy (accès via service_role uniquement).';
