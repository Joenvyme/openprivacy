/**
 * i18n client — FR (défaut), EN, DE.
 * Persistance : localStorage « openprivacy-lang ».
 */
(function () {
  "use strict";

  const LOCALES = ["fr", "en", "de"];
  const DEFAULT_LOCALE = "fr";
  const STORAGE_KEY = "openprivacy-lang";

  let locale = DEFAULT_LOCALE;
  let strings = {};

  function detectLocale() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && LOCALES.includes(saved)) return saved;
    const nav = (navigator.language || "").toLowerCase();
    if (nav.startsWith("de")) return "de";
    if (nav.startsWith("en")) return "en";
    return DEFAULT_LOCALE;
  }

  function resolve(obj, path) {
    return path.split(".").reduce((o, k) => (o != null ? o[k] : undefined), obj);
  }

  function t(key, fallback) {
    const val = resolve(strings, key);
    if (val == null || val === "") return fallback != null ? fallback : key;
    return val;
  }

  function applyDom() {
    document.documentElement.lang = locale;

    const title = t("meta.title");
    if (title) document.title = title;

    const desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute("content", t("meta.description"));

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const val = t(key);
      if (typeof val === "string") el.textContent = val;
    });

    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const key = el.getAttribute("data-i18n-html");
      const val = t(key);
      if (typeof val === "string") el.innerHTML = val;
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      const val = t(key);
      if (typeof val === "string") el.setAttribute("placeholder", val);
    });

    document.querySelectorAll("[data-i18n-list]").forEach((ul) => {
      const key = ul.getAttribute("data-i18n-list");
      const items = resolve(strings, key);
      if (!Array.isArray(items)) return;
      const lis = ul.querySelectorAll("li");
      items.forEach((text, i) => {
        if (lis[i]) lis[i].textContent = text;
      });
    });

    document.querySelectorAll(".lang-btn").forEach((btn) => {
      const code = btn.getAttribute("data-lang");
      const active = code === locale;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });

    document.dispatchEvent(
      new CustomEvent("openprivacy:langchange", { detail: { locale } })
    );
  }

  async function loadLocale(code) {
    const res = await fetch(`i18n/${code}.json`);
    if (!res.ok) throw new Error(`i18n/${code}.json`);
    strings = await res.json();
    locale = code;
    localStorage.setItem(STORAGE_KEY, code);
    applyDom();
  }

  async function setLocale(code) {
    if (!LOCALES.includes(code) || code === locale) return;
    await loadLocale(code);
  }

  async function init() {
    const initial = detectLocale();
    try {
      await loadLocale(initial);
    } catch {
      if (initial !== DEFAULT_LOCALE) {
        await loadLocale(DEFAULT_LOCALE);
      }
    }

    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const code = btn.getAttribute("data-lang");
        if (code) setLocale(code);
      });
    });

    window.i18n = { t, getLocale: () => locale, setLocale, LOCALES };
    document.dispatchEvent(new CustomEvent("openprivacy:i18nready"));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
