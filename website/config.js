/**
 * Configuration du site OpenPrivacy.
 * turnstileSiteKey : clé site Cloudflare Turnstile (si TURNSTILE_SECRET_KEY sur Vercel).
 */
window.SITE_CONFIG = {
  downloadMac:
    "https://github.com/Joenvyme/openprivacy/releases/latest/download/OpenPrivacy-mac.zip",
  downloadWindows: null,

  releasesPage: "https://github.com/Joenvyme/openprivacy/releases",
  versionsData: "versions.json",

  contactUrl: "",
  turnstileSiteKey: "",
};
