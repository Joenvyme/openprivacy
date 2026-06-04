(function () {
  const cfg = window.SITE_CONFIG || {};
  const apiBase = (cfg.apiBase || "").replace(/\/$/, "");

  const linkMac = document.getElementById("link-mac");
  const linkWin = document.getElementById("link-windows");
  const linkReleases = document.getElementById("link-releases");

  if (cfg.downloadMac && linkMac && linkMac.tagName === "A") linkMac.href = cfg.downloadMac;
  if (cfg.downloadWindows && linkWin && linkWin.tagName === "A") {
    linkWin.href = cfg.downloadWindows;
  }
  if (cfg.releasesPage && linkReleases) {
    linkReleases.href = cfg.releasesPage;
    linkReleases.textContent = "page des releases";
  }

  const buildNote = document.querySelector(".build-note");
  if (
    buildNote &&
    (cfg.downloadMac?.startsWith("http") || cfg.downloadWindows?.startsWith("http"))
  ) {
    buildNote.hidden = true;
  }

  const form = document.getElementById("register-form");
  const resultBox = document.getElementById("register-result");
  const errorBox = document.getElementById("register-error");
  const keyDisplay = document.getElementById("license-key-display");
  const copyBtn = document.getElementById("copy-key");

  if (!form) return;

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = !msg;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");
    resultBox.hidden = true;

    const email = new FormData(form).get("email");
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = "Création…";

    try {
      const res = await fetch(`${apiBase}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
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
      keyDisplay.textContent = data.license_key;
      resultBox.hidden = false;
      resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      showError(err.message || "Impossible de créer la clé. Réessayez plus tard.");
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
