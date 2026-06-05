"""
Interface graphique locale — OpenPrivacy (PyWebview).

UI HTML/CSS/JS embarquée ; logique métier dans desktop/api.py.
Tkinter conservé uniquement pour le dialogue d’activation de licence.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

APP_VERSION = "1.3.0"
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 640


def _web_root() -> Path:
    """Répertoire desktop/web (dev ou bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "desktop" / "web"
    return Path(__file__).resolve().parent / "web"


class _MacReopenBridge:
    """Réaffiche la fenêtre PyWebview au clic sur l’icône Dock (macOS)."""

    def __init__(self, window: object) -> None:
        self._window = window
        threading.Thread(target=self._run_tk_loop, daemon=True).start()

    def _run_tk_loop(self) -> None:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            root.createcommand("::tk::mac::ReopenApplication", self._on_reopen)
        except tk.TclError:
            return
        root.mainloop()

    def _on_reopen(self) -> None:
        try:
            self._window.show()
            self._window.restore()
        except Exception:
            pass


def main() -> None:
    import tkinter as tk
    import webview

    if __package__:
        from .api import Api
        from .license import ensure_license
    else:
        from api import Api
        from license import ensure_license

    # Étape licence : dialogue modal Tk (seul usage conservé de tkinter)
    lic_root = tk.Tk()
    lic_root.withdraw()
    if not ensure_license(lic_root):
        lic_root.destroy()
        return
    lic_root.destroy()

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

    if sys.platform == "darwin":
        _MacReopenBridge(window)

    webview.start(debug=False)


if __name__ == "__main__":
    main()
