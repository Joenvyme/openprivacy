-- Vérification e-mail optionnelle (si RESEND_API_KEY configurée sur Vercel)
alter table public.openprivacy_licenses
  add column if not exists email_verified_at timestamptz,
  add column if not exists verify_token text,
  add column if not exists verify_token_expires_at timestamptz;

alter table public.openprivacy_licenses
  drop constraint if exists openprivacy_licenses_status_check;

alter table public.openprivacy_licenses
  add constraint openprivacy_licenses_status_check
  check (status in ('active', 'revoked', 'pending'));

create unique index if not exists openprivacy_licenses_verify_token_idx
  on public.openprivacy_licenses (verify_token)
  where verify_token is not null;
