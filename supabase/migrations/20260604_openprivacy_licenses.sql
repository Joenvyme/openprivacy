-- OpenPrivacy: e-mail + clés uniquement (jamais de contenu utilisateur)
create table public.openprivacy_licenses (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  license_key text not null,
  plan text not null default 'free' check (plan in ('free', 'pro')),
  valid_until timestamptz,
  status text not null default 'active' check (status in ('active', 'revoked')),
  created_at timestamptz not null default now(),
  last_validated_at timestamptz,
  constraint openprivacy_licenses_email_unique unique (email),
  constraint openprivacy_licenses_key_unique unique (license_key)
);

alter table public.openprivacy_licenses enable row level security;

create index openprivacy_licenses_license_key_idx
  on public.openprivacy_licenses (license_key);

create index openprivacy_licenses_email_idx
  on public.openprivacy_licenses (email);

comment on table public.openprivacy_licenses is
  'OpenPrivacy license registry: email and activation keys only.';
