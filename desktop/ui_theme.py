"""Thème visuel OpenPrivacy — aligné sur openprivacy.ch (tkinter / ttk)."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk


@dataclass(frozen=True)
class Palette:
    bg: str = "#f6f3ee"
    deep: str = "#1a2332"
    surface: str = "#ffffff"
    text: str = "#1a2332"
    muted: str = "#5c6778"
    accent: str = "#1e4d6b"
    accent_hover: str = "#163a52"
    accent_soft: str = "#e8f0f5"
    border: str = "#d8dde6"
    success: str = "#2d6a4f"
    danger: str = "#9b2226"


def ui_font_family() -> str:
    if sys.platform == "darwin":
        return "Helvetica Neue"
    if sys.platform == "win32":
        return "Segoe UI"
    return "Ubuntu"


def mono_font_family() -> str:
    if sys.platform == "darwin":
        return "Menlo"
    if sys.platform == "win32":
        return "Cascadia Mono"
    return "DejaVu Sans Mono"


def apply_app_theme(root: tk.Tk | tk.Toplevel) -> Palette:
    """Applique couleurs, polices et styles ttk sur la fenêtre racine."""
    p = Palette()
    root.configure(bg=p.bg)

    style = ttk.Style(root)
    # clam permet boutons et cartes aux couleurs de la marque (aqua = style système daté)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    elif sys.platform == "darwin" and "aqua" in style.theme_names():
        style.theme_use("aqua")

    family = ui_font_family()
    mono = mono_font_family()

    try:
        tkfont.nametofont("TkDefaultFont").configure(family=family, size=11)
        tkfont.nametofont("TkTextFont").configure(family=family, size=11)
    except tk.TclError:
        pass

    base = (family, 11)
    base_bold = (family, 11, "bold")
    title = (family, 22, "bold")
    subtitle = (family, 12)
    small = (family, 10)

    style.configure(".", background=p.bg, foreground=p.text, font=base)
    style.configure("App.TFrame", background=p.bg)
    style.configure("Surface.TFrame", background=p.surface)
    style.configure("Toolbar.TFrame", background=p.bg)
    style.configure("Status.TFrame", background=p.accent_soft)

    style.configure("TLabel", background=p.bg, foreground=p.text, font=base)
    style.configure("Muted.TLabel", background=p.bg, foreground=p.muted, font=small)
    style.configure(
        "Status.TLabel", background=p.accent_soft, foreground=p.text, font=base
    )
    style.configure("Footer.TLabel", background=p.bg, foreground=p.muted, font=small)

    style.configure(
        "Card.TLabelframe",
        background=p.surface,
        bordercolor=p.border,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=p.surface,
        foreground=p.text,
        font=base_bold,
    )

    style.configure(
        "TButton",
        background=p.surface,
        foreground=p.text,
        bordercolor=p.border,
        padding=(14, 8),
        font=base,
    )
    style.map(
        "TButton",
        background=[("active", p.accent_soft), ("pressed", p.border)],
        relief=[("pressed", "sunken"), ("!pressed", "flat")],
    )

    style.configure(
        "Secondary.TButton",
        background=p.surface,
        foreground=p.text,
        bordercolor=p.border,
        padding=(14, 8),
        font=base,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", p.accent_soft), ("disabled", p.bg)],
    )

    style.configure(
        "Accent.TButton",
        background=p.accent,
        foreground="#ffffff",
        borderwidth=0,
        focuscolor=p.accent,
        padding=(18, 10),
        font=base_bold,
    )
    style.map(
        "Accent.TButton",
        background=[
            ("disabled", "#8fa8b8"),
            ("active", p.accent_hover),
            ("pressed", p.accent_hover),
        ],
        foreground=[("disabled", "#f0f0f0")],
    )

    style.configure(
        "TEntry",
        fieldbackground=p.surface,
        foreground=p.text,
        bordercolor=p.border,
        lightcolor=p.border,
        darkcolor=p.border,
        padding=8,
        font=base,
    )

    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=p.border,
        background=p.accent,
        bordercolor=p.border,
        lightcolor=p.accent,
        darkcolor=p.accent,
        thickness=6,
    )

    style.configure("TPanedwindow", background=p.bg)
    style.configure("Sash", sashthickness=6, background=p.border)

    root._opf_palette = p  # type: ignore[attr-defined]
    root._opf_font_ui = family  # type: ignore[attr-defined]
    root._opf_font_mono = mono  # type: ignore[attr-defined]
    root._opf_title_font = title  # type: ignore[attr-defined]
    root._opf_subtitle_font = subtitle  # type: ignore[attr-defined]
    return p


def configure_editor_text(
    widget: tk.Text,
    *,
    palette: Palette | None = None,
    mono: str | None = None,
    readonly: bool = False,
) -> None:
    p = palette or Palette()
    font_mono = (mono or mono_font_family(), 13)
    widget.configure(
        font=font_mono,
        bg=p.surface,
        fg=p.text,
        insertbackground=p.accent,
        selectbackground=p.accent_soft,
        selectforeground=p.text,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=p.border,
        highlightcolor=p.accent,
        padx=10,
        pady=10,
        spacing1=2,
        spacing3=4,
        undo=not readonly,
    )
    if readonly:
        widget.configure(state=tk.DISABLED, cursor="arrow")


def build_header(
    parent: tk.Misc,
    *,
    title: str,
    subtitle: str,
    palette: Palette | None = None,
) -> tk.Frame:
    p = palette or Palette()
    header = tk.Frame(parent, bg=p.deep, padx=20, pady=16)
    tk.Label(
        header,
        text=title,
        font=(ui_font_family(), 22, "bold"),
        fg="#ffffff",
        bg=p.deep,
        anchor=tk.W,
    ).pack(anchor=tk.W)
    tk.Label(
        header,
        text=subtitle,
        font=(ui_font_family(), 12),
        fg="#c5d0dc",
        bg=p.deep,
        anchor=tk.W,
        justify=tk.LEFT,
        wraplength=900,
    ).pack(anchor=tk.W, pady=(6, 0))
    return header


def style_activation_dialog(dialog: tk.Toplevel, content: ttk.Frame) -> Palette:
    p = apply_app_theme(dialog)
    dialog.configure(bg=p.bg)
    for w in (dialog, content):
        try:
            style = ttk.Style(dialog)
            style.configure("Dialog.TFrame", background=p.bg)
        except tk.TclError:
            pass
    content.configure(style="Dialog.TFrame")
    return p
