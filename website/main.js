(function () {
  const cfg = window.SITE_CONFIG || {};

  function tr(key, fallback) {
    if (window.i18n && typeof window.i18n.t === "function") {
      return window.i18n.t(key, fallback);
    }
    return fallback != null ? fallback : key;
  }

  function run() {
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

    function resolveMacDownload(releases, latestRelease) {
      if (latestRelease?.downloads?.mac) {
        return {
          url: latestRelease.downloads.mac,
          version: latestRelease.version,
          tag: latestRelease.tag,
        };
      }
      for (const r of releases) {
        if (r.downloads?.mac) {
          return { url: r.downloads.mac, version: r.version, tag: r.tag };
        }
      }
      return null;
    }

    function resolveWindowsDownload(releases, latestRelease) {
      if (latestRelease?.downloads?.windows) {
        return {
          url: latestRelease.downloads.windows,
          version: latestRelease.version,
        };
      }
      for (const r of releases) {
        if (r.downloads?.windows) {
          return { url: r.downloads.windows, version: r.version };
        }
      }
      return null;
    }

    function applyLatestVersion(latest, tag, macDl, winDl) {
      if (latestLabel) {
        latestLabel.textContent = `v${latest}`;
      }
      if (macVersionMeta) {
        macVersionMeta.textContent = `OpenPrivacy-mac.zip · v${macDl?.version || latest}`;
      }
      if (linkMac && linkMac.tagName === "A") {
        const macUrl =
          macDl?.url ||
          (tag
            ? `https://github.com/Joenvyme/openprivacy/releases/download/${tag}/OpenPrivacy-mac.zip`
            : null);
        if (macUrl) linkMac.href = macUrl;
      }
      
      // Activate Windows download if available (latest or most recent release with a build)
      if (winDl?.url && linkWin) {
        // Convert span to anchor if Windows download is available
        if (linkWin.tagName === "SPAN") {
          const anchor = document.createElement("a");
          anchor.id = "link-windows";
          anchor.className = "download-card";
          anchor.href = winDl.url;
          anchor.download = true;
          anchor.innerHTML = linkWin.innerHTML;
          linkWin.parentNode.replaceChild(anchor, linkWin);
          
          // Update button text
          const btn = anchor.querySelector(".btn-download");
          if (btn) {
            btn.innerHTML = `
              <i data-lucide="download" class="icon icon-sm" aria-hidden="true"></i>
              <span data-i18n="download.winBtnActive">Télécharger pour Windows</span>
            `;
          }
          
          // Update file meta
          const fileMeta = anchor.querySelector(".file-meta");
          if (fileMeta) {
            fileMeta.textContent = `OpenPrivacy-windows.zip · v${winDl.version}`;
          }
          
          // Recreate icons
          if (window.lucide) {
            window.lucide.createIcons({ attrs: { "stroke-width": 1.75 } });
          }
        } else if (linkWin.tagName === "A") {
          linkWin.href = winDl.url;

          // Update file meta even if already an anchor
          const fileMeta = linkWin.querySelector(".file-meta");
          if (fileMeta) {
            fileMeta.textContent = `OpenPrivacy-windows.zip · v${winDl.version}`;
          }
        }
        
        // Always hide the "coming soon" notice when Windows download is available
        const windowsNotice = document.getElementById("download-notice-windows");
        if (windowsNotice) {
          windowsNotice.hidden = true;
        }
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
        const macDl = resolveMacDownload(releases, latestRelease);
        const winDl = resolveWindowsDownload(releases, latestRelease);
        applyLatestVersion(latest, latestRelease?.tag, macDl, winDl);
      } catch (err) {
        console.error("Error loading versions:", err);
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
    const submitBtn = document.getElementById("register-submit");
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
        invalid: tr("errors.verifyInvalid"),
        expired: tr("errors.verifyExpired"),
        error: tr("errors.verifyError"),
      };
      showError(messages[verify] || tr("errors.verifyUnknown"));
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
      const btn = submitBtn || form.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.textContent = tr("access.submitting");

      try {
        const body = { email, company };
        if (cfg.turnstileSiteKey) {
          if (!turnstileToken) {
            throw new Error(tr("errors.turnstile"));
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
              ? tr("errors.serverDown")
              : text.slice(0, 120) || tr("errors.invalidResponse")
          );
        }
        if (!res.ok) {
          throw new Error(data.error || tr("errors.serverError"));
        }

        if (data.pending_verification) {
          if (pendingMessage) {
            pendingMessage.textContent = data.message || tr("errors.pendingDefault");
          }
          if (resultPending) {
            resultPending.hidden = false;
            resultPending.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
          return;
        }

        if (data.existing) {
          if (existingMessage) {
            existingMessage.textContent = data.message || tr("errors.existingDefault");
          }
          if (resultExisting) {
            resultExisting.hidden = false;
            resultExisting.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
          return;
        }

        if (!data.license_key) {
          throw new Error(tr("errors.incomplete"));
        }
        keyDisplay.textContent = data.license_key;
        if (resultNew) {
          resultNew.hidden = false;
          resultNew.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      } catch (err) {
        showError(err.message || tr("errors.registerFail"));
        if (window.turnstile && turnstileWidgetId != null) {
          window.turnstile.reset(turnstileWidgetId);
          turnstileToken = null;
        }
      } finally {
        btn.disabled = false;
        btn.textContent = tr("access.submit");
      }
    });

    document.addEventListener("openprivacy:langchange", () => {
      const lr = document.getElementById("link-releases");
      if (lr && cfg.releasesPage) lr.href = cfg.releasesPage;
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.textContent = tr("access.submit");
      }
      if (copyBtn && copyBtn.textContent !== tr("access.copied")) {
        copyBtn.textContent = tr("access.copyKey");
      }
    });

    if (copyBtn) {
      copyBtn.addEventListener("click", async () => {
        const key = keyDisplay.textContent;
        try {
          await navigator.clipboard.writeText(key);
          copyBtn.textContent = tr("access.copied");
          setTimeout(() => {
            copyBtn.textContent = tr("access.copyKey");
          }, 2000);
        } catch {
          showError(tr("errors.copyFail"));
        }
      });
    }
  }

  if (window.i18n) {
    run();
  } else {
    document.addEventListener("openprivacy:i18nready", run, { once: true });
  }
})();
