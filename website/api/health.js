const { sendJson, supabaseFetch } = require("./_lib.js");

module.exports = async (req, res) => {
  const origin = req.headers.origin || req.headers.Origin;
  const configured = Boolean(
    process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY
  );
  let supabase_ok = false;
  let supabase_status = null;

  if (configured) {
    try {
      const probe = await supabaseFetch(
        "openprivacy_licenses?select=id&limit=1"
      );
      supabase_status = probe.status;
      supabase_ok = probe.ok;
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
    ok: true,
    supabase_configured: configured,
    supabase_ok,
    ...(isAdmin ? { supabase_status } : {}),
    email_verification: Boolean(process.env.RESEND_API_KEY && process.env.EMAIL_FROM),
    turnstile: Boolean(process.env.TURNSTILE_SECRET_KEY),
    hint: !supabase_ok
      ? "Vérifiez SUPABASE_URL, la clé service_role et les migrations SQL du dépôt."
      : null,
  };

  sendJson(res, 200, body, origin);
};
