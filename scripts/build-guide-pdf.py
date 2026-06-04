#!/usr/bin/env python3
"""Génère le guide utilisateur PDF depuis GUIDE_UTILISATEUR_FR.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "GUIDE_UTILISATEUR_FR.md"
OUTPUT = ROOT / "website" / "GUIDE_UTILISATEUR_FR.pdf"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _find_font(bold: bool = False) -> str | None:
    if bold:
        for path in FONT_CANDIDATES:
            p = Path(path)
            if "Bold" in path or "bd" in path.lower() or "Bold.ttf" in path:
                if p.is_file():
                    return str(p)
        for path in FONT_CANDIDATES:
            if Path(path).is_file():
                return str(path)
        return None
    for path in FONT_CANDIDATES:
        p = Path(path)
        if "Bold" in path or "bd" in path.lower():
            continue
        if p.is_file():
            return str(p)
    return None


def _strip_md_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = text.replace("\\<", "<").replace("\\>", ">")
    return text


def build_pdf(md_path: Path, out_path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise SystemExit(
            "Installez fpdf2 : pip install fpdf2"
        ) from exc

    regular = _find_font(bold=False)
    bold_font = _find_font(bold=True)
    if not regular:
        raise SystemExit("Police TrueType introuvable (Arial / DejaVu).")

    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    family = "GuideFont"
    pdf.add_font(family, "", regular)
    if bold_font:
        pdf.add_font(family, "B", bold_font)

    def set_body(size: int = 11) -> None:
        pdf.set_font(family, size=size)

    def set_bold(size: int = 11) -> None:
        style = "B" if bold_font else ""
        pdf.set_font(family, style=style, size=size)

    def write_paragraph(line: str, *, bold: bool = False, size: int = 11) -> None:
        line = _strip_md_inline(line.strip())
        if not line:
            return
        if bold:
            set_bold(size)
        else:
            set_body(size)
        pdf.multi_cell(pdf.epw, 6, line)
        pdf.ln(2)

    set_bold(18)
    pdf.multi_cell(pdf.epw, 10, "OpenPrivacy.ch")
    pdf.ln(4)
    set_body(10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(pdf.epw, 5, "Guide utilisateur — anonymisation locale")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    in_table = False
    table_rows: list[list[str]] = []

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("|") and "|" in line[1:]:
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_rows.append([_strip_md_inline(c) for c in cells])
            in_table = True
            continue
        if in_table and table_rows:
            set_body(10)
            for row in table_rows:
                label = row[0] if row else ""
                value = row[1] if len(row) > 1 else ""
                pdf.multi_cell(pdf.epw, 5, f"{label} → {value}")
            pdf.ln(3)
            table_rows = []
            in_table = False

        if not line.strip():
            pdf.ln(3)
            continue
        if line.strip() == "---":
            pdf.ln(2)
            continue
        if line.startswith("# "):
            pdf.ln(4)
            set_bold(16)
            pdf.multi_cell(pdf.epw, 8, _strip_md_inline(line[2:].strip()))
            pdf.ln(2)
            continue
        if line.startswith("## "):
            pdf.ln(3)
            set_bold(13)
            pdf.multi_cell(pdf.epw, 7, _strip_md_inline(line[3:].strip()))
            pdf.ln(1)
            continue
        if line.startswith("### "):
            pdf.ln(2)
            set_bold(11)
            pdf.multi_cell(pdf.epw, 6, _strip_md_inline(line[4:].strip()))
            pdf.ln(1)
            continue
        if line.startswith("- "):
            set_body(11)
            pdf.multi_cell(pdf.epw, 6, "  •  " + _strip_md_inline(line[2:].strip()))
            continue
        if re.match(r"^\d+\.\s", line):
            set_body(11)
            pdf.multi_cell(pdf.epw, 6, "  " + _strip_md_inline(line.strip()))
            continue
        if line.startswith("**") and line.endswith("**"):
            write_paragraph(line, bold=True)
            continue
        if line.startswith("*(") and line.endswith(")*"):
            set_body(9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(pdf.epw, 5, _strip_md_inline(line.strip("()* ")))
            pdf.set_text_color(0, 0, 0)
            continue
        if "**" in line and line.strip().endswith("**"):
            parts = line.split("**", 2)
            if len(parts) >= 3:
                write_paragraph(parts[1], bold=True)
                if parts[2].strip():
                    write_paragraph(parts[2].strip())
                continue
        write_paragraph(line)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))


def main() -> None:
    if not SOURCE.is_file():
        print(f"Fichier introuvable : {SOURCE}", file=sys.stderr)
        sys.exit(1)
    build_pdf(SOURCE, OUTPUT)
    print(f"✓ PDF créé : {OUTPUT}")


if __name__ == "__main__":
    main()
