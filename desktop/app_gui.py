"""
Interface graphique locale — OpenPrivacy (PyWebview).

UI HTML/CSS/JS embarquée ; logique métier dans desktop/api.py.
Tkinter conservé uniquement pour le dialogue d’activation de licence (thread principal).
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_VERSION = "1.3.1"
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 640


def _web_root() -> Path:
    """Répertoire desktop/web (dev ou bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "desktop" / "web"
    return Path(__file__).resolve().parent / "web"


def _run_license_gate() -> bool:
    """Dialogue d’activation Tk sur le thread principal (avant PyWebview)."""
    import tkinter as tk

    if __package__:
        from .license import ensure_license
    else:
        from license import ensure_license

    lic_root = tk.Tk()
    lic_root.withdraw()
    try:
        return ensure_license(lic_root)
    finally:
        lic_root.destroy()


def main() -> None:
    import webview

    if __package__:
        from .api import Api
    else:
        from api import Api

    if not _run_license_gate():
        return

    web_dir = _web_root()
    index = web_dir / "index.html"
    if not index.is_file():
        raise FileNotFoundError(
            f"Interface web introuvable : {index}\n"
            "Vérifiez que desktop/web/ est présent ou embarqué dans la build."
        )

    api = Api()
    window = webview.create_window(
        title="OpenPrivacy.ch",
        url=index.as_uri(),
        js_api=api,
        width=1200,
        height=800,
        min_size=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
    )
    api.bind_window(window)

    # Pas de Tkinter en arrière-plan : macOS exige NSWindow sur le thread principal.
    webview.start(debug=False)


if __name__ == "__main__":
    main()
