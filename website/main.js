(function () {
  const cfg = window.SITE_CONFIG || {};

  const linkMac = document.getElementById("link-mac");
  const linkWin = document.getElementById("link-windows");
  const linkReleases = document.getElementById("link-releases");

  if (cfg.downloadMac && linkMac) {
    linkMac.href = cfg.downloadMac;
  }
  if (cfg.downloadWindows && linkWin) {
    linkWin.href = cfg.downloadWindows;
  }
  if (cfg.releasesPage && linkReleases) {
    linkReleases.href = cfg.releasesPage;
    linkReleases.textContent = "page des releases";
  }

  // Masquer la note « build » si les liens pointent vers une URL absolue (prod)
  const buildNote = document.querySelector(".build-note");
  if (
    buildNote &&
    (cfg.downloadMac?.startsWith("http") || cfg.downloadWindows?.startsWith("http"))
  ) {
    buildNote.hidden = true;
  }
})();
