import {
  corsHeaders,
  generateLicenseKey,
  jsonResponse,
  normalizeEmail,
  supabaseFetch,
} from "./_lib.js";

export default async function handler(request) {
  const origin = request.headers.get("origin");

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(origin) });
  }
  if (request.method !== "POST") {
    return jsonResponse(405, { error: "Method not allowed" }, origin);
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse(400, { error: "JSON invalide" }, origin);
  }

  const email = normalizeEmail(payload.email);
  if (!email) {
    return jsonResponse(400, { error: "Adresse e-mail invalide" }, origin);
  }

  try {
    const existing = await supabaseFetch(
      `openprivacy_licenses?email=eq.${encodeURIComponent(email)}&select=license_key,status,plan,valid_until&limit=1`
    );
    if (!existing.ok) {
      const detail = await existing.text();
      console.error("supabase existing", detail);
      return jsonResponse(502, { error: "Service indisponible" }, origin);
    }
    const rows = await existing.json();
    if (rows.length > 0 && rows[0].status === "active") {
      return jsonResponse(
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
      return jsonResponse(
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
    }

    const errText = await insert.text();
    console.error("supabase insert", insert.status, errText);
    return jsonResponse(502, { error: "Impossible de créer la clé" }, origin);
  } catch (err) {
    console.error(err);
    return jsonResponse(
      503,
      { error: "Configuration serveur incomplète (Supabase)." },
      origin
    );
  }
}
