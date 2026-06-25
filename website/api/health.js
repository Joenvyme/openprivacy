const { emailVerificationEnabled, sendJson, supabaseFetch } = require("./_lib.js");

module.exports = async (req, res) => {
  const origin = req.headers.origin || req.headers.Origin;
  const configured = Boolean(
    process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY
  );
  let supabase_ok = false;
  let supabase_status = null;
  let rate_limits_ok = false;
  let email_verify_columns = false;

  if (configured) {
    try {
      const probe = await supabaseFetch(
        "openprivacy_licenses?select=id&limit=1"
      );
      supabase_status = probe.status;
      supabase_ok = probe.ok;

      const rateProbe = await supabaseFetch(
        "openprivacy_rate_limits?select=bucket&limit=1"
      );
      rate_limits_ok = rateProbe.ok;

      const verifyProbe = await supabaseFetch(
        "openprivacy_licenses?select=email_verified_at&limit=1"
      );
      email_verify_columns = verifyProbe.ok;
    } catch (err) {
      console.error("health probe", err);
    }
  }

  const adminToken = process.env.HEALTH_ADMIN_TOKEN;
  const provided =
    req.headers["x-health-token"] ||
    req.headers["X-Health-Token"] ||
    req.query?.token;
  const isAdmin = Boolean(adminToken && provided && provided === adminToken);

  const body = {
    ok: supabase_ok,
    supabase_configured: configured,
    supabase_ok,
    rate_limits_ok,
    email_verify_columns,
    ...(isAdmin ? { supabase_status } : {}),
    email_verification: Boolean(process.env.RESEND_API_KEY && process.env.EMAIL_FROM),
    turnstile: Boolean(process.env.TURNSTILE_SECRET_KEY),
    hint: !supabase_ok
      ? "Vérifiez SUPABASE_URL, la clé service_role et les migrations SQL du dépôt."
      : !rate_limits_ok
        ? "Exécutez supabase/migrations/20260605_openprivacy_rate_limits.sql"
        : emailVerificationEnabled() && !email_verify_columns
          ? "Exécutez supabase/migrations/20260606_openprivacy_email_verify.sql"
          : null,
  };

  sendJson(res, 200, body, origin);
};
