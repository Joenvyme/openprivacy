/**
 * Interface OpenPrivacy — pont pywebview (pywebview.api.*)
 */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const els = {
    btnRedact: $("btn-redact"),
    btnOpen: $("btn-open"),
    btnSave: $("btn-save"),
    btnRestore: $("btn-restore"),
    btnClear: $("btn-clear"),
    sourceText: $("source-text"),
    outputText: $("output-text"),
    statusText: $("status-text"),
    statusDot: $("status-dot"),
    progressWrap: $("progress-wrap"),
    modeBadge: $("mode-badge"),
    sourceFilename: $("source-filename"),
    appVersion: $("app-version"),
    toasts: $("toasts"),
  };

  let state = {
    ready: false,
    busy: false,
    inputMode: "text",
    hasOutput: false,
  };

  function api() {
    return window.pywebview && window.pywebview.api;
  }

  function toast(message, type = "info", duration = 5000) {
    const node = document.createElement("div");
    node.className = "toast" + (type !== "info" ? " " + type : "");
    node.textContent = message;
    els.toasts.appendChild(node);
    setTimeout(() => {
      node.classList.add("leaving");
      setTimeout(() => node.remove(), 220);
    }, duration);
  }

  function setStatus(text, dotState) {
    els.statusText.textContent = text || "";
    if (dotState) {
      els.statusDot.dataset.state = dotState;
    }
  }

  function setBusy(busy) {
    state.busy = busy;
    els.progressWrap.hidden = !busy;
    els.statusDot.dataset.state = busy ? "busy" : state.ready ? "ready" : "loading";
    updateButtons();
  }

  function updateButtons() {
    const canAct = state.ready && !state.busy;
    els.btnRedact.disabled = !canAct;
    els.btnSave.disabled = !canAct || !state.hasOutput;
    els.btnRestore.disabled = !canAct || state.inputMode === "docx";
    els.btnOpen.disabled = state.busy;
    els.btnClear.disabled = state.busy;
  }

  function setMode(mode, filename) {
    state.inputMode = mode;
    els.modeBadge.textContent = mode === "docx" ? "Word" : "Texte";
    els.modeBadge.classList.toggle("docx", mode === "docx");
    els.sourceFilename.textContent = filename || "—";
  }

  async function refreshStatus() {
    const a = api();
    if (!a) return;
    try {
      const s = await a.get_status();
      if (s.model_error) {
        setStatus(s.status, "error");
        toast(s.model_error || s.status, "error", 12000);
        return;
      }
      state.ready = s.ready;
      state.busy = s.busy;
      if (s.status) setStatus(s.status, s.busy ? "busy" : s.ready ? "ready" : "loading");
      if (s.input_mode) setMode(s.input_mode, s.current_file);
      els.progressWrap.hidden = !s.busy;
      updateButtons();
    } catch (e) {
      console.warn("get_status", e);
    }
  }

  async function onRedact() {
    const a = api();
    if (!a) return;
    const text = els.sourceText.value;
    let res;
    if (state.inputMode === "docx") {
      res = await a.redact_docx();
    } else {
      res = await a.redact_text(text);
    }
    if (!res.ok) {
      if (res.message) toast(res.message, "error");
      return;
    }
    if (res.started) {
      setBusy(true);
      setStatus("Anonymisation en cours…", "busy");
    }
  }

  async function onOpen() {
    const a = api();
    if (!a) return;
    const res = await a.pick_open_file();
    if (res.cancelled) return;
    if (!res.ok) {
      if (res.message) toast(res.message, "error");
      return;
    }
    els.sourceText.value = res.source_text || "";
    els.outputText.value = res.output_text || "";
    state.hasOutput = Boolean(res.output_text && res.mode !== "docx");
    setMode(res.mode || "text", res.filename);
    if (res.status) setStatus(res.status, state.ready ? "ready" : "loading");
    updateButtons();
  }

  async function onRestore() {
    const a = api();
    if (!a) return;
    const res = await a.pick_map_and_restore(els.outputText.value);
    if (res.cancelled) return;
    if (!res.ok) {
      if (res.message) toast(res.message, "error");
      return;
    }
    els.sourceText.value = res.source_text || "";
    state.hasOutput = Boolean(els.outputText.value.trim());
    setMode("text", res.map_file || null);
    if (res.status) setStatus(res.status, "ready");
    const count = res.span_count != null ? res.span_count : "";
    toast(
      count !== ""
        ? `Texte restauré (${count} donnée(s) réintégrée(s)).`
        : "Texte restauré.",
      "success"
    );
    updateButtons();
  }

  async function onSave() {
    const a = api();
    if (!a) return;
    const res = await a.save_result(els.outputText.value);
    if (res.cancelled) return;
    if (!res.ok) {
      if (res.message) toast(res.message, "error");
      return;
    }
    if (res.message) toast(res.message, "success");
    if (res.status) setStatus(res.status, "ready");
  }

  async function onClear() {
    const a = api();
    if (!a) return;
    const res = await a.clear_all();
    els.sourceText.value = "";
    els.outputText.value = "";
    state.hasOutput = false;
    setMode("text", null);
    if (res.status) setStatus(res.status, state.ready ? "ready" : "loading");
    updateButtons();
  }

  /** Callbacks Python via evaluate_js */
  window.opfApp = {
    dispatch(event, payload) {
      switch (event) {
        case "status":
          if (payload.status) setStatus(payload.status, payload.busy ? "busy" : undefined);
          if (payload.busy !== undefined) setBusy(payload.busy);
          break;
        case "model_ready":
          state.ready = true;
          setBusy(false);
          if (payload.status) setStatus(payload.status, "ready");
          toast("Moteur prêt — traitement 100 % local.", "success", 3500);
          updateButtons();
          break;
        case "model_error":
          setStatus(payload.status || "Erreur", "error");
          if (payload.message) toast(payload.message, "error", 15000);
          updateButtons();
          break;
        case "redact_ok":
          setBusy(false);
          els.outputText.value = payload.output_text || "";
          state.hasOutput = true;
          if (payload.status) setStatus(payload.status, "ready");
          if (payload.reversible && payload.span_count != null) {
            toast(
              `Anonymisation terminée (${payload.span_count} donnée(s)). ` +
                "Enregistrez pour créer le fichier .opf-map.json de restauration.",
              "success",
              7000
            );
          }
          updateButtons();
          break;
        case "docx_ok":
          setBusy(false);
          els.outputText.value = payload.output_text || "";
          state.hasOutput = true;
          if (payload.status) setStatus(payload.status, "ready");
          toast("Document Word anonymisé créé.", "success");
          updateButtons();
          break;
        case "redact_error":
          setBusy(false);
          if (payload.status) setStatus(payload.status, "error");
          if (payload.message) toast(payload.message, "error");
          updateButtons();
          break;
        default:
          break;
      }
    },
  };

  els.btnRedact.addEventListener("click", onRedact);
  els.btnOpen.addEventListener("click", onOpen);
  els.btnSave.addEventListener("click", onSave);
  els.btnRestore.addEventListener("click", onRestore);
  els.btnClear.addEventListener("click", onClear);

  els.sourceText.addEventListener("input", () => {
    if (state.inputMode === "text") {
      state.hasOutput = false;
      updateButtons();
    }
  });

  function initWhenApiReady() {
    const a = api();
    if (!a) {
      requestAnimationFrame(initWhenApiReady);
      return;
    }
    a.get_app_info().then((info) => {
      if (info.version) {
        els.appVersion.textContent = "v" + info.version;
      }
    });
    refreshStatus();
    setInterval(refreshStatus, 2000);
  }

  window.addEventListener("pywebviewready", initWhenApiReady);
  if (api()) initWhenApiReady();
})();
