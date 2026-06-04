import {
  corsHeaders,
  jsonResponse,
  licenseIsValid,
  supabaseFetch,
} from "./_lib.js";

const CACHE_DAYS = 7;

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

  const license_key = String(payload.license_key || "")
    .trim()
    .toUpperCase();
  if (!license_key || !/^OP-[A-Z0-9]{8}-[A-Z0-9]{8}$/.test(license_key)) {
    return jsonResponse(400, { error: "Clé invalide" }, origin);
  }

  const app_version = String(payload.app_version || "unknown").slice(0, 32);

  try {
    const res = await supabaseFetch(
      `openprivacy_licenses?license_key=eq.${encodeURIComponent(license_key)}&select=id,plan,status,valid_until&limit=1`
    );
    if (!res.ok) {
      return jsonResponse(502, { error: "Service indisponible" }, origin);
    }
    const rows = await res.json();
    if (rows.length === 0) {
      return jsonResponse(
        200,
        { valid: false, reason: "unknown_key", cache_days: 0 },
        origin
      );
    }

    const row = rows[0];
    const valid = licenseIsValid(row);

    if (valid) {
      await supabaseFetch(
        `openprivacy_licenses?id=eq.${encodeURIComponent(row.id)}`,
        {
          method: "PATCH",
          prefer: "return=minimal",
          body: { last_validated_at: new Date().toISOString() },
        }
      );
    }

    return jsonResponse(
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
    return jsonResponse(503, { error: "Configuration serveur incomplète." }, origin);
  }
}
