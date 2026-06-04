(function () {
  const cfg = window.SITE_CONFIG || {};
  const apiBase = (cfg.apiBase || "").replace(/\/$/, "");

  const linkMac = document.getElementById("link-mac");
  const linkWin = document.getElementById("link-windows");
  const linkReleases = document.getElementById("link-releases");
  const linkAllVersions = document.getElementById("link-all-versions");
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
  if (cfg.releasesPage && linkAllVersions) {
    linkAllVersions.href = cfg.releasesPage;
  }

  function formatDate(iso) {
    try {
      return new Date(iso + "T12:00:00").toLocaleDateString("fr-CH", {
        day: "numeric",
        month: "long",
        year: "numeric",
      });
    } catch {
      return iso;
    }
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

  async function loadVersions() {
    const list = document.getElementById("versions-list");
    const loading = document.getElementById("versions-loading");
    const errorBox = document.getElementById("versions-error");
    if (!list || !cfg.versionsData) return;

    try {
      const res = await fetch(cfg.versionsData);
      if (!res.ok) throw new Error("Fichier versions introuvable");
      const data = await res.json();
      const releases = Array.isArray(data.releases) ? data.releases : [];
      const latest = data.latest || releases[0]?.version;

      if (latest) {
        const latestRelease = releases.find((r) => r.version === latest) || releases[0];
        applyLatestVersion(latest, latestRelease?.tag);
      }

      list.innerHTML = "";
      releases.forEach((rel, index) => {
        const isLatest = rel.version === latest || index === 0;
        const li = document.createElement("li");
        li.className = "versions-compact-row";

        const mac = rel.downloads?.mac;
        const win = rel.downloads?.windows;
        const links = [];
        if (mac) {
          links.push(`<a href="${mac}" download>Mac</a>`);
        }
        if (win) {
          links.push(`<a href="${win}" download>Win</a>`);
        }
        const linksHtml = links.length
          ? links.join(" · ")
          : '<span class="muted">—</span>';

        const note = rel.title || (rel.highlights && rel.highlights[0]) || "";
        const noteHtml = note
          ? `<span class="versions-compact-note" title="${note.replace(/"/g, "&quot;")}">${note}</span>`
          : "";

        li.innerHTML = `
          <span class="versions-compact-ver">v${rel.version}${isLatest ? '<span class="versions-compact-badge">actuelle</span>' : ""}</span>
          <span class="versions-compact-date">${formatDate(rel.date || "")}</span>
          ${noteHtml}
          <span class="versions-compact-links">${linksHtml}</span>
        `;
        list.appendChild(li);
      });

      if (loading) loading.hidden = true;
      if (errorBox) errorBox.hidden = true;
      if (releases.length === 0 && loading) {
        loading.textContent = "Aucune version publiée pour le moment.";
      }
    } catch (err) {
      if (loading) loading.hidden = true;
      if (errorBox) {
        errorBox.textContent =
          err.message || "Impossible de charger la liste des versions.";
        errorBox.hidden = false;
      }
    }
  }

  loadVersions();

  const form = document.getElementById("register-form");
  const resultNew = document.getElementById("register-result-new");
  const resultExisting = document.getElementById("register-result-existing");
  const existingMessage = document.getElementById("register-existing-message");
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
    if (resultNew) resultNew.hidden = true;
    if (resultExisting) resultExisting.hidden = true;

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
