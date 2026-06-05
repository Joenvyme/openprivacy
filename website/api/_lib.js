/** Helpers API OpenPrivacy (CommonJS — compatible Vercel). */

const { createHash, randomBytes } = require("crypto");

const ALLOWED_ORIGINS = new Set([
  "https://openprivacy.vercel.app",
  "https://www.openprivacy.ch",
  "https://openprivacy.ch",
  "http://localhost:8080",
  "http://127.0.0.1:8080",
]);

const RATE_LIMITS = {
  register: { windowSec: 3600, maxHits: 8 },
  validate: { windowSec: 60, maxHits: 40 },
};

const VERIFY_TOKEN_TTL_HOURS = 48;

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
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

function normalizeSupabaseUrl(raw) {
  let url = String(raw).trim().replace(/\/$/, "");
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

function getClientIp(req) {
  const forwarded = req.headers["x-forwarded-for"] || req.headers["X-Forwarded-For"];
  if (forwarded) {
    const first = String(forwarded).split(",")[0].trim();
    if (first) return first.slice(0, 64);
  }
  const realIp = req.headers["x-real-ip"] || req.headers["X-Real-Ip"];
  if (realIp) return String(realIp).trim().slice(0, 64);
  return "unknown";
}

function hashForBucket(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 32);
}

function rateLimitBucket(route, clientIp) {
  return `${route}:${hashForBucket(clientIp)}`;
}

async function enforceRateLimit(route, clientIp) {
  const limits = RATE_LIMITS[route];
  if (!limits) return { ok: true };

  const bucket = rateLimitBucket(route, clientIp);
  const now = Date.now();
  const windowMs = limits.windowSec * 1000;

  let row = null;
  try {
    const existing = await supabaseFetch(
      `openprivacy_rate_limits?bucket=eq.${encodeURIComponent(bucket)}&select=hits,window_start&limit=1`
    );
    if (existing.ok) {
      const rows = await existing.json();
      row = rows[0] || null;
    }
  } catch (err) {
    console.error("rate_limit read", err);
    return { ok: true };
  }

  if (!row) {
    const insert = await supabaseFetch("openprivacy_rate_limits", {
      method: "POST",
      prefer: "resolution=merge-duplicates",
      body: { bucket, hits: 1, window_start: new Date(now).toISOString() },
    });
    if (!insert.ok) {
      console.error("rate_limit insert", insert.status, await insert.text());
    }
    return { ok: true };
  }

  const windowStart = new Date(row.window_start).getTime();
  if (!Number.isFinite(windowStart) || now - windowStart >= windowMs) {
    await supabaseFetch(`openprivacy_rate_limits?bucket=eq.${encodeURIComponent(bucket)}`, {
      method: "PATCH",
      prefer: "return=minimal",
      body: { hits: 1, window_start: new Date(now).toISOString() },
    });
    return { ok: true };
  }

  const hits = Number(row.hits) || 0;
  if (hits >= limits.maxHits) {
    return {
      ok: false,
      retryAfterSec: Math.ceil((windowMs - (now - windowStart)) / 1000),
    };
  }

  await supabaseFetch(`openprivacy_rate_limits?bucket=eq.${encodeURIComponent(bucket)}`, {
    method: "PATCH",
    prefer: "return=minimal",
    body: { hits: hits + 1 },
  });
  return { ok: true };
}

async function verifyTurnstile(token, clientIp) {
  const secret = process.env.TURNSTILE_SECRET_KEY;
  if (!secret) return { ok: true, skipped: true };

  if (!token) {
    return { ok: false, error: "Vérification anti-robot requise." };
  }

  const body = new URLSearchParams({
    secret,
    response: token,
    remoteip: clientIp !== "unknown" ? clientIp : "",
  });

  const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const data = await res.json().catch(() => ({}));
  if (!data.success) {
    return { ok: false, error: "Vérification anti-robot échouée. Réessayez." };
  }
  return { ok: true };
}

function emailVerificationEnabled() {
  return Boolean(process.env.RESEND_API_KEY && process.env.EMAIL_FROM);
}

function publicSiteBase() {
  return (process.env.PUBLIC_SITE_URL || "https://www.openprivacy.ch").replace(/\/$/, "");
}

function generateVerifyToken() {
  return randomBytes(32).toString("hex");
}

async function sendVerificationEmail(email, token) {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.EMAIL_FROM;
  if (!apiKey || !from) {
    throw new Error("RESEND_API_KEY et EMAIL_FROM requis pour l’envoi d’e-mail.");
  }

  const verifyUrl = `${publicSiteBase()}/api/verify-email?token=${encodeURIComponent(token)}`;
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [email],
      subject: "Confirmez votre e-mail — OpenPrivacy",
      html: [
        "<p>Bonjour,</p>",
        "<p>Confirmez votre adresse pour activer votre clé OpenPrivacy :</p>",
        `<p><a href="${verifyUrl}">Confirmer mon e-mail</a></p>`,
        "<p>Ce lien expire sous 48 h. Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.</p>",
      ].join(""),
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    console.error("resend", res.status, detail);
    throw new Error("Envoi d’e-mail impossible.");
  }
}

function normalizeEmail(raw) {
  const email = String(raw || "")
    .trim()
    .toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return null;
  }
  if (email.length > 254) {
    return null;
  }
  return email;
}

function isHoneypotTriggered(payload) {
  const trap = payload.company || payload.website_url || payload.url;
  return Boolean(trap && String(trap).trim());
}

function generateLicenseKey() {
  const part = () => randomBytes(4).toString("hex").toUpperCase();
  return `OP-${part()}-${part()}`;
}

function licenseIsValid(row) {
  if (!row || row.status !== "active") return false;
  if (emailVerificationEnabled() && !row.email_verified_at) return false;
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

function verifyExpiresAt() {
  return new Date(Date.now() + VERIFY_TOKEN_TTL_HOURS * 3600 * 1000).toISOString();
}

module.exports = {
  ALLOWED_ORIGINS,
  VERIFY_TOKEN_TTL_HOURS,
  corsHeaders,
  sendJson,
  supabaseFetch,
  getClientIp,
  enforceRateLimit,
  verifyTurnstile,
  emailVerificationEnabled,
  publicSiteBase,
  generateVerifyToken,
  sendVerificationEmail,
  normalizeEmail,
  isHoneypotTriggered,
  generateLicenseKey,
  licenseIsValid,
  parseJsonBody,
  verifyExpiresAt,
};
