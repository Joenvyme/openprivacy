(function () {
  const cfg = window.SITE_CONFIG || {};
  const apiBase = (cfg.apiBase || "").replace(/\/$/, "");

  const linkMac = document.getElementById("link-mac");
  const linkWin = document.getElementById("link-windows");
  const linkReleases = document.getElementById("link-releases");
  const latestLabel = document.getElementById("download-latest-label");
  const macVersionMeta = document.getElementById("mac-version-meta");

  if (cfg.downloadMac && linkMac && linkMac.tagName === "A") {
    linkMac.href = cfg.downloadMac;
  }
  if (cfg.downloadWindows && linkWin && linkWin.tagName === "A") {
    linkWin.href = cfg.downloadWindows;
  }
  if (cfg.releasesPage && linkReleases) {
    linkReleases.href = cfg.releasesPage;
  }
  function applyLatestVersion(latest, tag) {
    if (latestLabel) {
      latestLabel.textContent = `v${latest}`;
    }
    if (macVersionMeta) {
      macVersionMeta.textContent = `OpenPrivacy-mac.zip · v${latest}`;
    }
    if (linkMac && linkMac.tagName === "A" && tag && !cfg.downloadMac?.includes("latest")) {
      linkMac.href = `https://github.com/Joenvyme/openprivacy/releases/download/${tag}/OpenPrivacy-mac.zip`;
    }
  }

  async function loadLatestVersion() {
    if (!cfg.versionsData) return;
    try {
      const res = await fetch(cfg.versionsData);
      if (!res.ok) return;
      const data = await res.json();
      const releases = Array.isArray(data.releases) ? data.releases : [];
      const latest = data.latest || releases[0]?.version;
      if (!latest) return;
      const latestRelease = releases.find((r) => r.version === latest) || releases[0];
      applyLatestVersion(latest, latestRelease?.tag);
    } catch {
      /* garde les libellés par défaut */
    }
  }

  loadLatestVersion();

  const form = document.getElementById("register-form");
  const resultNew = document.getElementById("register-result-new");
  const resultExisting = document.getElementById("register-result-existing");
  const resultPending = document.getElementById("register-result-pending");
  const existingMessage = document.getElementById("register-existing-message");
  const pendingMessage = document.getElementById("register-pending-message");
  const errorBox = document.getElementById("register-error");
  const keyDisplay = document.getElementById("license-key-display");
  const copyBtn = document.getElementById("copy-key");
  const turnstileHost = document.getElementById("turnstile-widget");

  let turnstileToken = null;
  let turnstileWidgetId = null;

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = !msg;
  }

  function hideResults() {
    if (resultNew) resultNew.hidden = true;
    if (resultExisting) resultExisting.hidden = true;
    if (resultPending) resultPending.hidden = true;
  }

  function loadTurnstile() {
    const siteKey = cfg.turnstileSiteKey;
    if (!siteKey || !turnstileHost) return;

    turnstileHost.hidden = false;
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async = true;
    script.onload = () => {
      if (!window.turnstile) return;
      turnstileWidgetId = window.turnstile.render(turnstileHost, {
        sitekey: siteKey,
        callback: (token) => {
          turnstileToken = token;
        },
        "expired-callback": () => {
          turnstileToken = null;
        },
      });
    };
    document.head.appendChild(script);
  }

  loadTurnstile();

  function handleVerifyRedirect() {
    const hash = window.location.hash || "";
    const query = hash.includes("?") ? hash.split("?")[1] : "";
    const params = new URLSearchParams(query);
    const verify = params.get("verify");
    if (!verify) return;

    hideResults();
    if (verify === "ok") {
      const key = params.get("key");
      if (key && keyDisplay) {
        keyDisplay.textContent = decodeURIComponent(key);
        if (resultNew) {
          resultNew.hidden = false;
          resultNew.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        showError("");
        history.replaceState(null, "", "#acces");
        return;
      }
    }
    const messages = {
      invalid: "Lien de confirmation invalide ou déjà utilisé.",
      expired: "Ce lien a expiré. Refaites une demande de clé.",
      error: "Impossible de confirmer l’e-mail. Réessayez plus tard.",
    };
    showError(messages[verify] || "Confirmation impossible.");
    history.replaceState(null, "", "#acces");
  }

  handleVerifyRedirect();

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");
    hideResults();

    const email = new FormData(form).get("email");
    const company = new FormData(form).get("company");
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = "Création…";

    try {
      const body = { email, company };
      if (cfg.turnstileSiteKey) {
        if (!turnstileToken) {
          throw new Error("Complétez la vérification anti-robot ci-dessous.");
        }
        body.turnstile_token = turnstileToken;
      }

      const res = await fetch(`${apiBase}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(
          text.startsWith("A server error")
            ? "Serveur indisponible. Réessayez dans quelques minutes."
            : text.slice(0, 120) || "Réponse serveur invalide"
        );
      }
      if (!res.ok) {
        throw new Error(data.error || "Erreur serveur");
      }

      if (data.pending_verification) {
        if (pendingMessage) {
          pendingMessage.textContent =
            data.message ||
            "Consultez votre boîte mail et cliquez sur le lien de confirmation.";
        }
        if (resultPending) {
          resultPending.hidden = false;
          resultPending.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        return;
      }

      if (data.existing) {
        if (existingMessage) {
          existingMessage.textContent =
            data.message || "Une clé existe déjà pour cet e-mail.";
        }
        if (resultExisting) {
          resultExisting.hidden = false;
          resultExisting.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        return;
      }

      if (!data.license_key) {
        throw new Error("Réponse serveur incomplète.");
      }
      keyDisplay.textContent = data.license_key;
      if (resultNew) {
        resultNew.hidden = false;
        resultNew.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    } catch (err) {
      showError(err.message || "Impossible de créer la clé. Réessayez plus tard.");
      if (window.turnstile && turnstileWidgetId != null) {
        window.turnstile.reset(turnstileWidgetId);
        turnstileToken = null;
      }
    } finally {
      btn.disabled = false;
      btn.textContent = "Créer ma clé";
    }
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const key = keyDisplay.textContent;
      try {
        await navigator.clipboard.writeText(key);
        copyBtn.textContent = "Copié !";
        setTimeout(() => {
          copyBtn.textContent = "Copier la clé";
        }, 2000);
      } catch {
        showError("Copie impossible — sélectionnez la clé manuellement.");
      }
    });
  }
})();
