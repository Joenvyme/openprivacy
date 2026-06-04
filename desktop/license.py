"""Activation OpenPrivacy — uniquement la clé est envoyée au serveur."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

APP_VERSION = "1.1.0"
LICENSE_DIR = Path.home() / ".openprivacy"
LICENSE_FILE = LICENSE_DIR / "license.json"
DEFAULT_API_BASE = "https://www.openprivacy.ch"
CACHE_DAYS_DEFAULT = 7


def api_base() -> str:
    return os.environ.get("OPENPRIVACY_API_URL", DEFAULT_API_BASE).rstrip("/")


def _read_cache() -> dict[str, Any] | None:
    if not LICENSE_FILE.is_file():
        return None
    try:
        return json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(payload: dict[str, Any]) -> None:
    LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def cached_license_valid() -> tuple[bool, str | None]:
    """True si le cache local autorise l'usage hors ligne."""
    data = _read_cache()
    if not data or not data.get("license_key"):
        return False, None
    until_raw = data.get("cache_valid_until")
    if not until_raw:
        return False, data.get("license_key")
    try:
        until = datetime.fromisoformat(until_raw.replace("Z", "+00:00"))
    except ValueError:
        return False, data.get("license_key")
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) <= until:
        return True, data.get("license_key")
    return False, data.get("license_key")


def validate_license_online(license_key: str) -> dict[str, Any]:
    """POST /api/validate — envoie uniquement la clé et la version app."""
    body = json.dumps(
        {"license_key": license_key.strip().upper(), "app_version": APP_VERSION}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{api_base()}/api/validate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except Exception:
            detail = {"error": exc.reason}
        raise RuntimeError(detail.get("error", "Validation échouée")) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Impossible de joindre le serveur d'activation. Vérifiez votre connexion."
        ) from exc


def save_license(license_key: str, result: dict[str, Any]) -> None:
    days = int(result.get("cache_days") or CACHE_DAYS_DEFAULT)
    until = datetime.now(timezone.utc) + timedelta(days=days)
    _write_cache(
        {
            "license_key": license_key.strip().upper(),
            "plan": result.get("plan", "free"),
            "cache_valid_until": until.isoformat(),
        }
    )


def activate(license_key: str, *, allow_offline_cache: bool = True) -> tuple[bool, str]:
    """
    Valide une clé (en ligne ou cache). Retourne (ok, message).
    """
    key = license_key.strip().upper()
    if not key:
        return False, "Saisissez votre clé d'activation."

    if allow_offline_cache:
        cached_ok, cached_key = cached_license_valid()
        if cached_ok and cached_key == key:
            return True, "Licence valide (mode hors ligne)."

    try:
        result = validate_license_online(key)
    except RuntimeError as exc:
        if allow_offline_cache:
            cached_ok, cached_key = cached_license_valid()
            if cached_ok and cached_key == key:
                return True, "Licence valide (hors ligne, cache)."
        return False, str(exc)

    if not result.get("valid"):
        reason = result.get("reason") or "invalid"
        messages = {
            "unknown_key": "Clé inconnue.",
            "revoked": "Cette clé a été révoquée.",
            "expired": "Cette clé a expiré.",
        }
        return False, messages.get(reason, "Clé non valide.")

    save_license(key, result)
    return True, "Activation réussie."


def ensure_license(parent) -> bool:
    """Affiche la fenêtre d'activation si nécessaire. Retourne False pour quitter."""
    import tkinter as tk
    from tkinter import messagebox, ttk
    import webbrowser

    try:
        from .ui_theme import apply_app_theme, build_header, style_activation_dialog
    except ImportError:
        from ui_theme import apply_app_theme, build_header, style_activation_dialog

    cached_ok, cached_key = cached_license_valid()
    if cached_ok and cached_key:
        return True

    apply_app_theme(parent)

    dialog = tk.Toplevel(parent)
    dialog.title("Activation — OpenPrivacy")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)
    dialog.minsize(480, 0)

    build_header(
        dialog,
        title="Activation",
        subtitle=(
            "Seule votre clé est vérifiée en ligne. "
            "Vos documents ne quittent jamais cet ordinateur."
        ),
    ).pack(fill=tk.X)

    frame = ttk.Frame(dialog, padding=(24, 20, 24, 24))
    frame.pack(fill=tk.BOTH, expand=True)
    style_activation_dialog(dialog, frame)

    ttk.Label(frame, text="Clé d'activation (OP-…)").pack(anchor=tk.W)
    key_var = tk.StringVar(value=(cached_key or "") if cached_key else "")
    entry = ttk.Entry(frame, textvariable=key_var, width=40)
    entry.pack(anchor=tk.W, pady=(6, 16), ipady=4)
    entry.focus()

    result = {"ok": False}

    def open_register() -> None:
        webbrowser.open(f"{api_base()}/#acces")

    def submit() -> None:
        ok, msg = activate(key_var.get())
        if ok:
            result["ok"] = True
            dialog.destroy()
        else:
            messagebox.showerror("Activation", msg, parent=dialog)

    def quit_app() -> None:
        dialog.destroy()

    btns = ttk.Frame(frame)
    btns.pack(anchor=tk.W)
    ttk.Button(btns, text="Activer", command=submit, style="Accent.TButton").pack(
        side=tk.LEFT, padx=(0, 8)
    )
    ttk.Button(
        btns, text="Obtenir une clé…", command=open_register, style="Secondary.TButton"
    ).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btns, text="Quitter", command=quit_app, style="Secondary.TButton").pack(
        side=tk.LEFT
    )

    dialog.protocol("WM_DELETE_WINDOW", quit_app)
    parent.withdraw()
    dialog.wait_window()
    parent.deiconify()
    return result["ok"]
