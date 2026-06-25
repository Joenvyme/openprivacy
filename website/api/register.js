const {
  corsHeaders,
  emailVerificationEnabled,
  enforceRateLimit,
  generateLicenseKey,
  generateVerifyToken,
  getClientIp,
  isHoneypotTriggered,
  normalizeEmail,
  parseJsonBody,
  sendJson,
  sendVerificationEmail,
  supabaseFetch,
  verifyExpiresAt,
  verifyTurnstile,
} = require("./_lib.js");

module.exports = async (req, res) => {
  const origin = req.headers.origin || req.headers.Origin;
  const clientIp = getClientIp(req);

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

  const rate = await enforceRateLimit("register", clientIp);
  if (!rate.ok) {
    sendJson(
      res,
      429,
      {
        error: "Trop de tentatives. Réessayez plus tard.",
        retry_after_sec: rate.retryAfterSec,
      },
      origin
    );
    return;
  }

  let payload;
  try {
    payload = parseJsonBody(req);
  } catch {
    sendJson(res, 400, { error: "JSON invalide" }, origin);
    return;
  }

  if (isHoneypotTriggered(payload)) {
    sendJson(res, 400, { error: "Requête refusée." }, origin);
    return;
  }

  const turnstile = await verifyTurnstile(payload.turnstile_token, clientIp);
  if (!turnstile.ok) {
    sendJson(res, 400, { error: turnstile.error }, origin);
    return;
  }

  const email = normalizeEmail(payload.email);
  if (!email) {
    sendJson(res, 400, { error: "Adresse e-mail invalide" }, origin);
    return;
  }

  try {
    const verifyOn = emailVerificationEnabled();
    const selectCols = verifyOn
      ? "id,status,plan,email_verified_at"
      : "id,status,plan";
    const existing = await supabaseFetch(
      `openprivacy_licenses?email=eq.${encodeURIComponent(email)}&select=${selectCols}&limit=1`
    );
    if (!existing.ok) {
      const detail = await existing.text();
      console.error("supabase existing", existing.status, detail);
      const hint =
        existing.status === 404
          ? "Table openprivacy_licenses introuvable. Exécutez les migrations SQL du dépôt."
          : existing.status === 401
            ? "Clé Supabase invalide : utilisez la clé service_role (pas anon)."
            : existing.status === 400 && detail.includes("email_verified_at")
              ? "Migration SQL manquante : exécutez 20260606_openprivacy_email_verify.sql sur Supabase."
              : "Service indisponible";
      sendJson(res, 502, { error: hint }, origin);
      return;
    }
    const rows = await existing.json();
    if (rows.length > 0) {
      const row = rows[0];
      if (row.status === "active" && (!verifyOn || row.email_verified_at)) {
        sendJson(
          res,
          200,
          {
            email,
            existing: true,
            plan: row.plan,
            message:
              "Si une clé a déjà été créée pour cet e-mail, elle ne peut plus être affichée ici. Utilisez la clé enregistrée lors de votre première inscription.",
          },
          origin
        );
        return;
      }
    }

    const license_key = generateLicenseKey();
    const needsEmailVerify = verifyOn;
    const verify_token = needsEmailVerify ? generateVerifyToken() : null;
    const body = {
      email,
      license_key,
      plan: "free",
      status: needsEmailVerify ? "pending" : "active",
      valid_until: null,
    };
    if (verifyOn) {
      body.email_verified_at = needsEmailVerify ? null : new Date().toISOString();
      body.verify_token = verify_token;
      body.verify_token_expires_at = needsEmailVerify ? verifyExpiresAt() : null;
    }

    const insert = await supabaseFetch("openprivacy_licenses", {
      method: "POST",
      prefer: "return=representation",
      body,
    });

    if (insert.status === 409) {
      sendJson(
        res,
        200,
        {
          email,
          existing: true,
          message:
            "Si une clé a déjà été créée pour cet e-mail, elle ne peut plus être affichée ici.",
        },
        origin
      );
      return;
    }

    if (insert.status === 201) {
      const created = await insert.json();
      const row = Array.isArray(created) ? created[0] : created;

      if (needsEmailVerify && verify_token) {
        try {
          await sendVerificationEmail(email, verify_token);
        } catch (err) {
          console.error(err);
          await supabaseFetch(
            `openprivacy_licenses?id=eq.${encodeURIComponent(row.id)}`,
            { method: "DELETE", prefer: "return=minimal" }
          );
          sendJson(res, 502, { error: "Impossible d’envoyer l’e-mail de confirmation." }, origin);
          return;
        }
        sendJson(
          res,
          201,
          {
            email,
            pending_verification: true,
            existing: false,
            message:
              "Un e-mail de confirmation vous a été envoyé. Cliquez sur le lien pour afficher votre clé d’activation.",
          },
          origin
        );
        return;
      }

      sendJson(
        res,
        201,
        {
          email,
          license_key: row.license_key,
          plan: row.plan,
          existing: false,
          message:
            "Votre clé est affichée une seule fois. Copiez-la et conservez-la en lieu sûr avant de quitter cette page.",
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
