"""API Python exposée à l'interface PyWebview (pont JS ↔ logique métier)."""

from __future__ import annotations

import json
import queue
import shutil
import sys
import threading
from pathlib import Path
from typing import Any

try:
    from .docx_redact import (
        default_output_path,
        docx_available,
        extract_plaintext,
        is_docx_path,
        redact_docx_file,
    )
    from .license import APP_VERSION
except ImportError:
    from docx_redact import (
        default_output_path,
        docx_available,
        extract_plaintext,
        is_docx_path,
        redact_docx_file,
    )
    from license import APP_VERSION

APP_TITLE = "OpenPrivacy.ch"

FILE_TYPES = (
    "Word et texte (*.docx;*.txt;*.md;*.rtf;*.log)",
    "Microsoft Word (*.docx)",
    "Documents texte (*.txt;*.md;*.rtf;*.log)",
    "Tous les fichiers (*.*)",
)

DOCX_SAVE_TYPES = (
    "Document Word (*.docx)",
    "Document texte (*.txt)",
    "Tous les fichiers (*.*)",
)


def _default_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _json_for_js(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


class Api:
    """Pont pywebview : conserve threads, queues et redaction comme app_gui.py."""

    def __init__(self) -> None:
        self._window: Any = None
        self._redactor: Any = None
        self._ready = False
        self._busy = False
        self._device: str | None = None
        self._load_queue: queue.Queue = queue.Queue()
        self._current_file: Path | None = None
        self._input_mode = "text"
        self._docx_output_path: Path | None = None
        self._status = "Préparation du moteur d’anonymisation…"
        self._model_error: str | None = None
        self._start_model_load()

    def bind_window(self, window: Any) -> None:
        self._window = window

    def _evaluate(self, script: str) -> None:
        if not self._window:
            return
        try:
            self._window.evaluate_js(script)
        except Exception:
            pass

    def _emit(self, event: str, payload: dict[str, Any]) -> None:
        detail = _json_for_js(payload)
        self._evaluate(
            f"window.opfApp && window.opfApp.dispatch({json.dumps(event)},{detail})"
        )

    def get_app_info(self) -> dict[str, Any]:
        return {
            "title": APP_TITLE,
            "version": APP_VERSION,
            "min_width": 960,
            "min_height": 640,
        }

    def get_status(self) -> dict[str, Any]:
        return {
            "ready": self._ready,
            "busy": self._busy,
            "loading_model": not self._ready and self._model_error is None,
            "status": self._status,
            "device": self._device,
            "input_mode": self._input_mode,
            "current_file": self._current_file.name if self._current_file else None,
            "docx_output": str(self._docx_output_path) if self._docx_output_path else None,
            "model_error": self._model_error,
        }

    def _start_model_load(self) -> None:
        threading.Thread(target=self._load_model_worker, daemon=True).start()
        threading.Thread(target=self._queue_worker, daemon=True).start()

    def _load_model_worker(self) -> None:
        try:
            from opf import OPF

            device = _default_device()
            self._status = (
                "Premier lancement : téléchargement du modèle (~3 Go) si nécessaire…"
            )
            self._emit("status", {"status": self._status})
            redactor = OPF(device=device, output_text_only=True)
            redactor.redact("test")
            self._load_queue.put(("model_ok", redactor, device))
        except Exception as exc:
            self._load_queue.put(("model_error", str(exc)))

    def _queue_worker(self) -> None:
        while True:
            msg = self._load_queue.get()
            kind = msg[0]
            if kind == "model_ok":
                self._redactor = msg[1]
                self._device = msg[2]
                self._ready = True
                self._status = f"Prêt · {self._device.upper()} · modèle chargé"
                self._emit("model_ready", {"status": self._status, "device": self._device})
            elif kind == "model_error":
                self._model_error = msg[1]
                self._status = "Erreur au chargement du moteur"
                self._emit(
                    "model_error",
                    {
                        "status": self._status,
                        "message": (
                            "Le moteur d’anonymisation n’a pas pu démarrer.\n\n"
                            f"Détail : {msg[1]}\n\n"
                            "Vérifiez votre connexion Internet pour le premier lancement."
                        ),
                    },
                )
            elif kind == "redact_ok":
                self._busy = False
                self._status = "Anonymisation terminée"
                self._emit(
                    "redact_ok",
                    {"output_text": msg[1], "status": self._status},
                )
            elif kind == "docx_ok":
                self._busy = False
                out_path, preview, stats = msg[1], msg[2], msg[3]
                self._docx_output_path = out_path
                self._status = f"Word anonymisé : {out_path.name}"
                header = (
                    f"Document Word anonymisé créé :\n{out_path}\n\n"
                    f"Paragraphes modifiés : {stats.paragraphs_changed} "
                    f"sur {stats.paragraphs_processed}.\n\n"
                    "Utilisez « Enregistrer le résultat… » pour le copier ailleurs.\n"
                    "— Aperçu du texte —\n\n"
                )
                self._emit(
                    "docx_ok",
                    {
                        "output_text": header + preview,
                        "status": self._status,
                        "path": str(out_path),
                        "stats": {
                            "changed": stats.paragraphs_changed,
                            "processed": stats.paragraphs_processed,
                        },
                    },
                )
            elif kind == "redact_error":
                self._busy = False
                self._status = "Erreur lors de l’anonymisation"
                self._emit(
                    "redact_error",
                    {"status": self._status, "message": msg[1]},
                )

    def _require_ready(self) -> dict[str, Any] | None:
        if not self._ready or self._redactor is None:
            return {
                "ok": False,
                "message": "Le moteur se charge encore. Patientez quelques instants.",
            }
        if self._busy:
            return {"ok": False, "message": "Une opération est déjà en cours."}
        return None

    def pick_open_file(self) -> dict[str, Any]:
        import webview

        if not webview.windows:
            return {"ok": False, "message": "Fenêtre indisponible."}
        paths = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=FILE_TYPES,
        )
        if not paths:
            return {"ok": False, "cancelled": True}
        return self._load_file_path(Path(paths[0]))

    def _load_file_path(self, file_path: Path) -> dict[str, Any]:
        suffix = file_path.suffix.lower()
        if suffix == ".doc":
            return {
                "ok": False,
                "message": (
                    "Les anciens fichiers .doc ne sont pas pris en charge.\n"
                    "Enregistrez le document au format .docx dans Word."
                ),
            }
        if is_docx_path(file_path):
            if not docx_available():
                return {
                    "ok": False,
                    "message": "Le module Word n’est pas installé dans cette build.",
                }
            try:
                content = extract_plaintext(file_path)
            except Exception as exc:
                return {"ok": False, "message": f"Impossible de lire le fichier Word : {exc}"}
            self._input_mode = "docx"
            self._docx_output_path = None
            self._current_file = file_path
            self._status = f"Word ouvert : {file_path.name}"
            return {
                "ok": True,
                "mode": "docx",
                "source_text": content,
                "output_text": (
                    "Cliquez sur « Anonymiser » pour générer le fichier Word anonymisé "
                    "(mise en forme conservée)."
                ),
                "filename": file_path.name,
                "status": self._status,
            }
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1")
        except OSError as exc:
            return {"ok": False, "message": f"Impossible d’ouvrir le fichier : {exc}"}
        self._input_mode = "text"
        self._docx_output_path = None
        self._current_file = file_path
        self._status = f"Fichier ouvert : {file_path.name}"
        return {
            "ok": True,
            "mode": "text",
            "source_text": content,
            "output_text": "",
            "filename": file_path.name,
            "status": self._status,
        }

    def clear_all(self) -> dict[str, Any]:
        self._current_file = None
        self._input_mode = "text"
        self._docx_output_path = None
        self._status = "Texte effacé"
        return {"ok": True, "status": self._status}

    def redact_text(self, text: str) -> dict[str, Any]:
        blocked = self._require_ready()
        if blocked:
            return blocked
        if not text.strip():
            return {
                "ok": False,
                "message": "Collez ou saisissez du texte, ou ouvrez un fichier.",
            }
        self._busy = True
        self._status = "Anonymisation en cours…"
        self._emit("status", {"status": self._status, "busy": True})

        def worker() -> None:
            try:
                result = self._redactor.redact(text)
                self._load_queue.put(("redact_ok", result))
            except Exception as exc:
                self._load_queue.put(("redact_error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "started": True}

    def redact_docx(self) -> dict[str, Any]:
        blocked = self._require_ready()
        if blocked:
            return blocked
        if not self._current_file or not is_docx_path(self._current_file):
            return {
                "ok": False,
                "message": "Ouvrez un fichier .docx avant d’anonymiser.",
            }
        out_path = default_output_path(self._current_file)
        self._busy = True
        self._status = "Anonymisation du document Word…"
        self._emit("status", {"status": self._status, "busy": True})
        current = self._current_file

        def worker() -> None:
            try:
                stats = redact_docx_file(current, out_path, self._redactor.redact)
                preview = extract_plaintext(out_path)
                self._load_queue.put(("docx_ok", out_path, preview, stats))
            except Exception as exc:
                self._load_queue.put(("redact_error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "started": True}

    def save_result(self, output_text: str) -> dict[str, Any]:
        import webview

        if not webview.windows:
            return {"ok": False, "message": "Fenêtre indisponible."}

        if self._input_mode == "docx" and self._docx_output_path:
            default_name = self._docx_output_path.name
            path = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=DOCX_SAVE_TYPES,
            )
            if not path:
                return {"ok": False, "cancelled": True}
            dest = Path(path)
            try:
                if dest.resolve() != self._docx_output_path.resolve():
                    shutil.copy2(self._docx_output_path, dest)
            except OSError as exc:
                return {"ok": False, "message": f"Impossible d’enregistrer : {exc}"}
            self._status = f"Enregistré : {dest.name}"
            return {
                "ok": True,
                "message": f"Document Word enregistré :\n{dest}",
                "path": str(dest),
                "status": self._status,
            }

        if not output_text.strip():
            return {
                "ok": False,
                "message": "Anonymisez d’abord un texte, puis enregistrez le résultat.",
            }

        default_name = "document_anonymise.txt"
        if self._current_file:
            default_name = f"{self._current_file.stem}_anonymise.txt"
        path = webview.windows[0].create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
            file_types=("Document texte (*.txt)", "Tous les fichiers (*.*)"),
        )
        if not path:
            return {"ok": False, "cancelled": True}
        try:
            Path(path).write_text(output_text, encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "message": f"Impossible d’enregistrer : {exc}"}
        self._status = f"Enregistré : {Path(path).name}"
        return {
            "ok": True,
            "message": f"Fichier enregistré :\n{path}",
            "path": str(path),
            "status": self._status,
        }
