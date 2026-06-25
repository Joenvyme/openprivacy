"""Activation OpenPrivacy — uniquement la clé est envoyée au serveur."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

APP_VERSION = "1.3.3"
LICENSE_DIR = Path.home() / ".openprivacy"
LICENSE_FILE = LICENSE_DIR / "license.json"
DEFAULT_API_BASE = "https://www.openprivacy.ch"
CACHE_DAYS_DEFAULT = 7

ALLOWED_API_HOSTS = frozenset(
    {
        "www.openprivacy.ch",
        "openprivacy.ch",
        "openprivacy.vercel.app",
    }
)


def _api_override_allowed() -> bool:
    if os.environ.get("OPENPRIVACY_ALLOW_API_OVERRIDE") == "1":
        return True
    return not getattr(sys, "frozen", False)


def api_base() -> str:
    override = os.environ.get("OPENPRIVACY_API_URL", "").strip()
    if not override:
        return DEFAULT_API_BASE
    if not _api_override_allowed():
        return DEFAULT_API_BASE
    parsed = urllib.parse.urlparse(override.rstrip("/"))
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"https", "http"} or host not in ALLOWED_API_HOSTS:
        raise RuntimeError(
            "OPENPRIVACY_API_URL invalide. Utilisez https://www.openprivacy.ch "
            "ou définissez OPENPRIVACY_ALLOW_API_OVERRIDE=1 en développement."
        )
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{host}{port}"


def _read_cache() -> dict[str, Any] | None:
    if not LICENSE_FILE.is_file():
        return None
    try:
        return json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(payload: dict[str, Any]) -> None:
    LICENSE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    LICENSE_FILE.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    try:
        os.chmod(LICENSE_DIR, 0o700)
        os.chmod(LICENSE_FILE, 0o600)
    except OSError:
        pass


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
            "pending_verification": (
                "Confirmez votre e-mail via le lien reçu à l’inscription, puis réessayez."
            ),
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
        from .ui_theme import (
            apply_app_theme,
            build_header,
            center_window,
            mono_font_family,
            style_activation_dialog,
        )
    except ImportError:
        from ui_theme import (
            apply_app_theme,
            build_header,
            center_window,
            mono_font_family,
            style_activation_dialog,
        )

    cached_ok, cached_key = cached_license_valid()
    if cached_ok and cached_key:
        return True

    # Fenêtre autonome si le parent est masqué (évite Toplevel minuscule sur macOS).
    own_window = False
    try:
        parent_withdrawn = str(parent.state()) == "withdrawn"
    except tk.TclError:
        parent_withdrawn = True

    if parent_withdrawn:
        dialog = tk.Tk()
        own_window = True
        apply_app_theme(dialog)
    else:
        apply_app_theme(parent)
        dialog = tk.Toplevel(parent)
        dialog.transient(parent)

    dialog.title("Activation — OpenPrivacy.ch")
    dialog.grab_set()
    dialog.resizable(False, False)

    ACTIVATION_W = 560
    ACTIVATION_H = 420

    build_header(
        dialog,
        title="OpenPrivacy.ch",
        subtitle=(
            "Entrez votre clé d’activation (OP-…). "
            "Seule la clé est vérifiée en ligne — vos documents restent sur cet ordinateur."
        ),
    ).pack(fill=tk.X)

    frame = ttk.Frame(dialog, padding=(28, 24, 28, 28))
    frame.pack(fill=tk.BOTH, expand=True)
    style_activation_dialog(dialog, frame)

    ttk.Label(frame, text="Clé d’activation", style="Activation.TLabel").pack(
        anchor=tk.W
    )
    ttk.Label(
        frame,
        text="Obtenez une clé gratuite sur openprivacy.ch si vous n’en avez pas encore.",
        style="ActivationHint.TLabel",
    ).pack(anchor=tk.W, pady=(4, 12))

    key_var = tk.StringVar(value=(cached_key or "") if cached_key else "")
    entry = ttk.Entry(
        frame,
        textvariable=key_var,
        width=32,
        style="Activation.TEntry",
        font=(mono_font_family(), 15),
    )
    entry.pack(fill=tk.X, pady=(0, 20), ipady=6)
    entry.focus_set()

    result = {"ok": False}

    def open_register() -> None:
        webbrowser.open(f"{api_base()}/#acces")

    def submit(_event: object | None = None) -> None:
        ok, msg = activate(key_var.get())
        if ok:
            result["ok"] = True
            dialog.destroy()
        else:
            messagebox.showerror("Activation", msg, parent=dialog)

    entry.bind("<Return>", submit)

    def quit_app() -> None:
        dialog.destroy()

    btns = ttk.Frame(frame)
    btns.pack(anchor=tk.W)
    ttk.Button(btns, text="Activer", command=submit, style="Accent.TButton").pack(
        side=tk.LEFT, padx=(0, 10)
    )
    ttk.Button(
        btns, text="Obtenir une clé…", command=open_register, style="Secondary.TButton"
    ).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(btns, text="Quitter", command=quit_app, style="Secondary.TButton").pack(
        side=tk.LEFT
    )

    dialog.protocol("WM_DELETE_WINDOW", quit_app)

    center_window(dialog, ACTIVATION_W, ACTIVATION_H)
    dialog.lift()
    dialog.attributes("-topmost", True)
    dialog.after(200, lambda: dialog.attributes("-topmost", False))
    dialog.focus_force()

    if not own_window:
        parent.withdraw()
    dialog.wait_window()
    if not own_window:
        parent.deiconify()
    elif own_window:
        try:
            dialog.destroy()
        except tk.TclError:
            pass

    return result["ok"]
