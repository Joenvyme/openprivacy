/** Helpers partagés — API OpenPrivacy (aucun contenu utilisateur). */

const ALLOWED_ORIGINS = new Set([
  "https://openprivacy.vercel.app",
  "https://website-six-flame-48.vercel.app",
  "http://localhost:8080",
  "http://127.0.0.1:8080",
]);

export function corsHeaders(origin) {
  const allowed =
    origin && ALLOWED_ORIGINS.has(origin) ? origin : "https://openprivacy.vercel.app";
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

export function jsonResponse(status, body, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(origin),
    },
  });
}

export function supabaseConfig() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis sur Vercel.");
  }
  return { url: url.replace(/\/$/, ""), key };
}

export async function supabaseFetch(path, { method = "GET", body, prefer } = {}) {
  const { url, key } = supabaseConfig();
  const headers = {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
  };
  if (prefer) headers.Prefer = prefer;
  const res = await fetch(`${url}/rest/v1/${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  return res;
}

export function normalizeEmail(raw) {
  const email = String(raw || "")
    .trim()
    .toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return null;
  }
  return email;
}

export function generateLicenseKey() {
  const part = () =>
    crypto.randomUUID().replace(/-/g, "").slice(0, 8).toUpperCase();
  return `OP-${part()}-${part()}`;
}

export function licenseIsValid(row) {
  if (!row || row.status !== "active") return false;
  if (!row.valid_until) return true;
  return new Date(row.valid_until).getTime() > Date.now();
}
