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

  let supabase_host = null;
  if (process.env.SUPABASE_URL) {
    try {
      supabase_host = new URL(process.env.SUPABASE_URL).hostname;
    } catch {
      supabase_host = "invalid_url";
    }
  }

  sendJson(
    res,
    200,
    {
      ok: true,
      supabase_configured: configured,
      supabase_host,
      supabase_ok,
      supabase_status,
      hint: !supabase_ok
        ? "Créez la table openprivacy_licenses sur CE projet (SQL dans le repo) ou corrigez SUPABASE_URL sur Vercel."
        : null,
    },
    origin
  );
};
