/** Helpers API OpenPrivacy (CommonJS — compatible Vercel). */

const ALLOWED_ORIGINS = new Set([
  "https://openprivacy.vercel.app",
  "https://www.openprivacy.ch",
  "https://openprivacy.ch",
  "http://localhost:8080",
  "http://127.0.0.1:8080",
]);

function corsHeaders(origin) {
  let allowed = "https://www.openprivacy.ch";
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    allowed = origin;
  }
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

function sendJson(res, status, body, origin) {
  res.statusCode = status;
  Object.entries(corsHeaders(origin)).forEach(([k, v]) => res.setHeader(k, v));
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(body));
}

function normalizeSupabaseUrl(raw) {
  let url = String(raw).trim().replace(/\/$/, "");
  // Certains collent l’URL REST complète par erreur → évite /rest/v1/rest/v1/...
  if (url.endsWith("/rest/v1")) {
    url = url.slice(0, -"/rest/v1".length);
  }
  return url;
}

function supabaseConfig() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis.");
  }
  return { url: normalizeSupabaseUrl(url), key };
}

async function supabaseFetch(path, { method = "GET", body, prefer } = {}) {
  const { url, key } = supabaseConfig();
  const headers = {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
  };
  if (prefer) headers.Prefer = prefer;
  return fetch(`${url}/rest/v1/${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

function normalizeEmail(raw) {
  const email = String(raw || "")
    .trim()
    .toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return null;
  }
  return email;
}

function generateLicenseKey() {
  const { randomBytes } = require("crypto");
  const part = () => randomBytes(4).toString("hex").toUpperCase();
  return `OP-${part()}-${part()}`;
}

function licenseIsValid(row) {
  if (!row || row.status !== "active") return false;
  if (!row.valid_until) return true;
  return new Date(row.valid_until).getTime() > Date.now();
}

function parseJsonBody(req) {
  const raw = req.body;
  if (raw == null || raw === "") return {};
  if (typeof raw === "object" && !Buffer.isBuffer(raw)) return raw;
  const text = Buffer.isBuffer(raw) ? raw.toString("utf8") : String(raw);
  return JSON.parse(text);
}

module.exports = {
  ALLOWED_ORIGINS,
  corsHeaders,
  sendJson,
  supabaseFetch,
  normalizeEmail,
  generateLicenseKey,
  licenseIsValid,
  parseJsonBody,
};
