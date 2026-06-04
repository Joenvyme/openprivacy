const {
  corsHeaders,
  licenseIsValid,
  sendJson,
  supabaseFetch,
} = require("./_lib.js");

const CACHE_DAYS = 7;

module.exports = async (req, res) => {
  const origin = req.headers.origin || req.headers.Origin;

  if (req.method === "OPTIONS") {
    res.statusCode = 204;
    Object.entries(corsHeaders(origin)).forEach(([k, v]) => res.setHeader(k, v));
    res.end();
    return;
  }
  if (req.method !== "POST") {
    sendJson(res, 405, { error: "Method not allowed" }, origin);
    return;
  }

  let payload;
  try {
    payload = JSON.parse(req.body || "{}");
  } catch {
    sendJson(res, 400, { error: "JSON invalide" }, origin);
    return;
  }

  const license_key = String(payload.license_key || "")
    .trim()
    .toUpperCase();
  if (!license_key || !/^OP-[A-Z0-9]{8}-[A-Z0-9]{8}$/.test(license_key)) {
    sendJson(res, 400, { error: "Clé invalide" }, origin);
    return;
  }

  const app_version = String(payload.app_version || "unknown").slice(0, 32);

  try {
    const dbRes = await supabaseFetch(
      `openprivacy_licenses?license_key=eq.${encodeURIComponent(license_key)}&select=id,plan,status,valid_until&limit=1`
    );
    if (!dbRes.ok) {
      sendJson(res, 502, { error: "Service indisponible" }, origin);
      return;
    }
    const rows = await dbRes.json();
    if (rows.length === 0) {
      sendJson(res, 200, { valid: false, reason: "unknown_key", cache_days: 0 }, origin);
      return;
    }

    const row = rows[0];
    const valid = licenseIsValid(row);

    if (valid) {
      await supabaseFetch(`openprivacy_licenses?id=eq.${encodeURIComponent(row.id)}`, {
        method: "PATCH",
        prefer: "return=minimal",
        body: { last_validated_at: new Date().toISOString() },
      });
    }

    sendJson(
      res,
      200,
      {
        valid,
        plan: row.plan,
        reason: valid ? null : row.status === "revoked" ? "revoked" : "expired",
        cache_days: valid ? CACHE_DAYS : 0,
        app_version,
      },
      origin
    );
  } catch (err) {
    console.error(err);
    sendJson(res, 503, { error: "Configuration serveur incomplète." }, origin);
  }
};
