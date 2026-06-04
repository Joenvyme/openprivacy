const {
  corsHeaders,
  generateLicenseKey,
  normalizeEmail,
  sendJson,
  supabaseFetch,
} = require("./_lib.js");

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

  const email = normalizeEmail(payload.email);
  if (!email) {
    sendJson(res, 400, { error: "Adresse e-mail invalide" }, origin);
    return;
  }

  try {
    const existing = await supabaseFetch(
      `openprivacy_licenses?email=eq.${encodeURIComponent(email)}&select=license_key,status,plan,valid_until&limit=1`
    );
    if (!existing.ok) {
      console.error("supabase existing", await existing.text());
      sendJson(res, 502, { error: "Service indisponible" }, origin);
      return;
    }
    const rows = await existing.json();
    if (rows.length > 0 && rows[0].status === "active") {
      sendJson(
        res,
        200,
        {
          email,
          license_key: rows[0].license_key,
          plan: rows[0].plan,
          existing: true,
          message:
            "Une clé existe déjà pour cet e-mail. Conservez-la pour activer l'application.",
        },
        origin
      );
      return;
    }

    const license_key = generateLicenseKey();
    const insert = await supabaseFetch("openprivacy_licenses", {
      method: "POST",
      prefer: "return=representation",
      body: {
        email,
        license_key,
        plan: "free",
        status: "active",
        valid_until: null,
      },
    });
    if (insert.status === 201) {
      const created = await insert.json();
      const row = Array.isArray(created) ? created[0] : created;
      sendJson(
        res,
        201,
        {
          email,
          license_key: row.license_key,
          plan: row.plan,
          existing: false,
          message:
            "Votre clé gratuite est créée. Copiez-la avant de fermer cette page.",
        },
        origin
      );
      return;
    }

    console.error("supabase insert", insert.status, await insert.text());
    sendJson(res, 502, { error: "Impossible de créer la clé" }, origin);
  } catch (err) {
    console.error(err);
    sendJson(
      res,
      503,
      { error: "Configuration serveur incomplète (Supabase)." },
      origin
    );
  }
};
