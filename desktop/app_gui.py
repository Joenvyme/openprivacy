"""
Interface graphique locale — OpenPrivacy (OpenAI Privacy Filter).

Conçue pour des utilisateurs sans compétences techniques : double-clic, coller
du texte ou ouvrir un fichier, puis anonymiser.
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from .ui_theme import apply_app_theme, build_header, configure_editor_text
except ImportError:
    from ui_theme import apply_app_theme, build_header, configure_editor_text

APP_TITLE = "OpenPrivacy"
APP_VERSION = "1.1.0"
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 640

TEXT_FILE_TYPES = [
    ("Documents texte", "*.txt *.md *.rtf *.log"),
    ("Tous les fichiers", "*.*"),
]


def _default_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


class PrivacyFilterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.palette = apply_app_theme(root)
        self._redactor = None
        self._ready = False
        self._load_queue: queue.Queue = queue.Queue()
        self._current_file: Path | None = None

        self._build_ui()
        self._poll_load_queue()
        self._start_model_load()

    def _build_ui(self) -> None:
        p = self.palette

        build_header(
            self.root,
            title=APP_TITLE,
            subtitle=(
                "Anonymisez des données personnelles sur votre ordinateur. "
                "Seule la clé d'activation est vérifiée en ligne — jamais le contenu "
                "de vos documents."
            ),
            palette=p,
        ).pack(fill=tk.X)

        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=(20, 14, 20, 6))
        toolbar.pack(fill=tk.X)

        self.btn_redact = ttk.Button(
            toolbar,
            text="Anonymiser",
            command=self._run_redaction,
            style="Accent.TButton",
        )
        self.btn_redact.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_open = ttk.Button(
            toolbar,
            text="Ouvrir un fichier…",
            command=self._open_file,
            style="Secondary.TButton",
        )
        self.btn_open.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_save = ttk.Button(
            toolbar,
            text="Enregistrer le résultat…",
            command=self._save_file,
            style="Secondary.TButton",
        )
        self.btn_save.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Effacer",
            command=self._clear_all,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)

        panes = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True, padx=20, pady=(4, 12))

        left = ttk.LabelFrame(
            panes, text="  Texte original  ", style="Card.TLabelframe", padding=4
        )
        right = ttk.LabelFrame(
            panes, text="  Texte anonymisé  ", style="Card.TLabelframe", padding=4
        )
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        self.input_text = tk.Text(left, wrap=tk.WORD, undo=True)
        self.output_text = tk.Text(right, wrap=tk.WORD)
        configure_editor_text(self.input_text, palette=p, readonly=False)
        configure_editor_text(self.output_text, palette=p, readonly=True)

        for panel, text_w in ((left, self.input_text), (right, self.output_text)):
            bar = ttk.Scrollbar(panel, command=text_w.yview)
            text_w.configure(yscrollcommand=bar.set)
            text_w.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
            bar.pack(side=tk.RIGHT, fill=tk.Y, pady=4, padx=(0, 4))

        status_frame = ttk.Frame(self.root, style="Status.TFrame", padding=(20, 10))
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 4))

        self.status_var = tk.StringVar(
            value="Préparation du moteur d’anonymisation…"
        )
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
        ).pack(side=tk.LEFT, anchor=tk.W)

        self.progress = ttk.Progressbar(
            status_frame,
            mode="indeterminate",
            length=200,
            style="Horizontal.TProgressbar",
        )
        self.progress.pack(side=tk.RIGHT)
        self.progress.start(10)

        self._set_controls_enabled(False)

        ttk.Label(
            self.root,
            text=(
                f"Version {APP_VERSION} · Traitement 100 % local · "
                "Premier lancement : téléchargement du modèle (~3 Go, une seule fois)"
            ),
            style="Footer.TLabel",
            padding=(20, 0, 20, 14),
        ).pack(anchor=tk.W)

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_open.configure(state=state)
        self.btn_save.configure(state=state)
        self.btn_redact.configure(state=state)

    def _start_model_load(self) -> None:
        thread = threading.Thread(target=self._load_model_worker, daemon=True)
        thread.start()

    def _load_model_worker(self) -> None:
        try:
            from opf import OPF

            device = _default_device()
            redactor = OPF(device=device, output_text_only=True)
            redactor.redact("test")
            self._load_queue.put(("ok", redactor, device))
        except Exception as exc:
            self._load_queue.put(("error", str(exc)))

    def _poll_load_queue(self) -> None:
        try:
            msg = self._load_queue.get_nowait()
        except queue.Empty:
            self.root.after(200, self._poll_load_queue)
            return

        self.progress.stop()
        self.progress.pack_forget()

        kind = msg[0]
        if kind == "ok":
            self._redactor = msg[1]
            device = msg[2]
            self._ready = True
            self._set_controls_enabled(True)
            self.status_var.set(
                f"Prêt · {device.upper()} · modèle chargé"
            )
        else:
            self.status_var.set("Erreur au chargement du moteur")
            messagebox.showerror(
                "Impossible de démarrer",
                "Le moteur d’anonymisation n’a pas pu démarrer.\n\n"
                f"Détail : {msg[1]}\n\n"
                "Vérifiez votre connexion Internet pour le premier lancement, "
                "puis réessayez.",
            )

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Ouvrir un document",
            filetypes=TEXT_FILE_TYPES,
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = Path(path).read_text(encoding="latin-1")
        except OSError as exc:
            messagebox.showerror("Erreur", f"Impossible d’ouvrir le fichier :\n{exc}")
            return

        self._current_file = Path(path)
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", content)
        self.status_var.set(f"Fichier ouvert : {self._current_file.name}")

    def _save_file(self) -> None:
        default_name = "document_anonymise.txt"
        if self._current_file:
            stem = self._current_file.stem
            default_name = f"{stem}_anonymise.txt"

        path = filedialog.asksaveasfilename(
            title="Enregistrer le texte anonymisé",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Document texte", "*.txt"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return

        content = self._get_output_text()
        if not content.strip():
            messagebox.showwarning(
                "Rien à enregistrer",
                "Anonymisez d’abord un texte, puis enregistrez le résultat.",
            )
            return

        try:
            Path(path).write_text(content, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Erreur", f"Impossible d’enregistrer :\n{exc}")
            return

        self.status_var.set(f"Enregistré : {Path(path).name}")
        messagebox.showinfo("Enregistré", f"Le fichier a été enregistré :\n{path}")

    def _get_input_text(self) -> str:
        return self.input_text.get("1.0", tk.END).rstrip("\n")

    def _get_output_text(self) -> str:
        return self.output_text.get("1.0", tk.END).rstrip("\n")

    def _set_output_text(self, text: str) -> None:
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.configure(state=tk.DISABLED)

    def _clear_all(self) -> None:
        self.input_text.delete("1.0", tk.END)
        self._set_output_text("")
        self._current_file = None
        self.status_var.set("Texte effacé")

    def _run_redaction(self) -> None:
        if not self._ready or self._redactor is None:
            messagebox.showinfo(
                "Patientez",
                "Le moteur se charge encore. Réessayez dans quelques instants.",
            )
            return

        text = self._get_input_text()
        if not text.strip():
            messagebox.showwarning(
                "Texte vide",
                "Collez ou saisissez du texte, ou ouvrez un fichier.",
            )
            return

        self._set_controls_enabled(False)
        self.status_var.set("Anonymisation en cours…")
        self.progress.pack(side=tk.RIGHT)
        self.progress.start(10)

        def worker() -> None:
            try:
                result = self._redactor.redact(text)
                self._load_queue.put(("redact_ok", result))
            except Exception as exc:
                self._load_queue.put(("redact_error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, self._poll_redaction_queue)

    def _poll_redaction_queue(self) -> None:
        try:
            msg = self._load_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_redaction_queue)
            return

        self.progress.stop()
        self.progress.pack_forget()
        self._set_controls_enabled(True)

        if msg[0] == "redact_ok":
            self._set_output_text(msg[1])
            self.status_var.set("Anonymisation terminée")
        else:
            self.status_var.set("Erreur lors de l’anonymisation")
            messagebox.showerror(
                "Erreur",
                f"L’anonymisation a échoué :\n{msg[1]}",
            )


def main() -> None:
    if __package__:
        from .license import ensure_license
    else:
        from license import ensure_license

    root = tk.Tk()
    apply_app_theme(root)
    root.withdraw()
    if sys.platform == "darwin":
        try:
            root.createcommand("::tk::mac::ReopenApplication", root.deiconify)
        except tk.TclError:
            pass
    if not ensure_license(root):
        root.destroy()
        return
    PrivacyFilterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
