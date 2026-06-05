#!/usr/bin/env python3
"""
Génère un PDF depuis GUIDE_UTILISATEUR_FR.md (legacy).

Le guide officiel est désormais GUIDE_UTILISATEUR_FR.pdf à la racine (édité manuellement).
Pour le site : ./scripts/sync-guide-pdf.sh
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "GUIDE_UTILISATEUR_FR.md"
OUTPUT = ROOT / "website" / "GUIDE_UTILISATEUR_FR.pdf"

# Palette alignée desktop/web et site (#f6f3ee, #1a2332, #1e4d6b)
COLOR_BG = (246, 243, 238)
COLOR_TEXT = (26, 35, 50)
COLOR_MUTED = (107, 114, 128)
COLOR_ACCENT = (30, 77, 107)
COLOR_ACCENT_SOFT = (232, 240, 244)
COLOR_CARD = (255, 255, 255)
COLOR_WARN_SOFT = (254, 243, 199)
COLOR_WARN_BORDER = (217, 119, 6)
COLOR_SUCCESS_SOFT = (220, 252, 231)
COLOR_SUCCESS_BORDER = (13, 122, 74)

MARGIN_L = 18
MARGIN_R = 18
MARGIN_T = 22
MARGIN_B = 22
HEADER_H = 14
FOOTER_H = 12
LINE_H_BODY = 5.5
LINE_H_TIGHT = 5.0

FONT_CANDIDATES_REG = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _find_font(candidates: list[str]) -> str | None:
    for path in candidates:
        if Path(path).is_file():
            return path
    return None


def _strip_md_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = text.replace("\\<", "<").replace("\\>", ">")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u00a0", " ")
    text = text.replace("[PRIVATE_", "<PRIVATE_").replace("]", ">")
    return text


def _soft_break(text: str, width: int = 88) -> str:
    """Insère des espaces insécables/zéro-width pour éviter les débordements fpdf."""
    zwsp = "\u200b"
    out: list[str] = []
    for token in text.split(" "):
        if len(token) <= width:
            out.append(token)
            continue
        chunk = token
        while len(chunk) > width:
            out.append(chunk[:width] + zwsp)
            chunk = chunk[width:]
        if chunk:
            out.append(chunk)
    return " ".join(out)


class GuidePDF:
    """Mise en page PDF avec en-tête, pied de page et retours à la ligne sûrs."""

    def __init__(self, regular: str, bold: str | None) -> None:
        from fpdf import FPDF

        self._FPDF = FPDF
        self.pdf = FPDF(orientation="P", unit="mm", format="A4")
        self.pdf.set_auto_page_break(auto=False)
        self.pdf.set_margins(MARGIN_L, MARGIN_T, MARGIN_R)
        self.family = "GuideFont"
        self.pdf.add_font(self.family, "", regular)
        self.has_bold = bool(bold)
        if bold:
            self.pdf.add_font(self.family, "B", bold)
        self._page_no = 0
        self._in_cover = False

    @property
    def epw(self) -> float:
        return self.pdf.w - self.pdf.l_margin - self.pdf.r_margin

    @property
    def bottom_limit(self) -> float:
        return self.pdf.h - MARGIN_B - FOOTER_H

    def _font(self, style: str = "", size: int = 11) -> None:
        self.pdf.set_font(self.family, style=style, size=size)

    def _set_color_text(self) -> None:
        self.pdf.set_text_color(*COLOR_TEXT)

    def _set_color_muted(self) -> None:
        self.pdf.set_text_color(*COLOR_MUTED)

    def _reset_x(self) -> None:
        self.pdf.set_x(self.pdf.l_margin)

    def _ensure_space(self, height: float) -> None:
        if self.pdf.get_y() + height > self.bottom_limit:
            self._end_page()
            self._begin_page()

    def _begin_page(self, *, cover: bool = False) -> None:
        self._page_no += 1
        self._in_cover = cover
        self.pdf.add_page()
        if cover:
            self.pdf.set_fill_color(*COLOR_BG)
            self.pdf.rect(0, 0, self.pdf.w, self.pdf.h, style="F")
            self.pdf.set_y(MARGIN_T)
            return
        # Bandeau accent en haut
        self.pdf.set_fill_color(*COLOR_ACCENT)
        self.pdf.rect(0, 0, self.pdf.w, 3, style="F")
        self.pdf.set_fill_color(*COLOR_CARD)
        self.pdf.rect(0, 3, self.pdf.w, HEADER_H, style="F")
        self._font("B", 9)
        self.pdf.set_text_color(*COLOR_ACCENT)
        self.pdf.set_xy(MARGIN_L, 6)
        self.pdf.cell(self.epw * 0.6, 6, "OpenPrivacy.ch", align="L")
        self._font("", 8)
        self._set_color_muted()
        self.pdf.cell(self.epw * 0.4, 6, "Guide utilisateur", align="R")
        self.pdf.set_y(MARGIN_T + 4)
        self._set_color_text()

    def _end_page(self) -> None:
        if self._in_cover:
            return
        self.pdf.set_draw_color(*COLOR_ACCENT_SOFT)
        y = self.pdf.h - MARGIN_B + 2
        self.pdf.line(MARGIN_L, y, self.pdf.w - MARGIN_R, y)
        self._font("", 8)
        self._set_color_muted()
        self.pdf.set_xy(MARGIN_L, y + 2)
        self.pdf.cell(self.epw, 5, "www.openprivacy.ch", align="L")
        self.pdf.cell(self.epw, 5, f"Page {self._page_no}", align="R")

    def _write_lines(
        self,
        text: str,
        *,
        size: int = 10,
        bold: bool = False,
        color: tuple[int, int, int] | None = None,
        line_h: float = LINE_H_BODY,
        indent: float = 0,
    ) -> None:
        text = _soft_break(_strip_md_inline(text.strip()))
        if not text:
            return
        style = "B" if bold and self.has_bold else ""
        self._font(style, size)
        if color:
            self.pdf.set_text_color(*color)
        else:
            self._set_color_text()

        wrap_width = max(40, int(self.epw * 0.42))
        if indent:
            wrap_width = max(30, wrap_width - int(indent * 2.5))

        for paragraph in text.split("\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                self._ensure_space(line_h)
                self.pdf.ln(line_h * 0.6)
                continue
            for line in textwrap.wrap(paragraph, width=wrap_width):
                self._ensure_space(line_h)
                self._reset_x()
                if indent:
                    self.pdf.set_x(self.pdf.l_margin + indent)
                self.pdf.multi_cell(self.epw - indent, line_h, line)
        self.pdf.ln(1.5)

    def _write_heading(self, text: str, level: int) -> None:
        sizes = {1: 17, 2: 13, 3: 11}
        self._ensure_space(12)
        self.pdf.ln(4 if level == 1 else 3 if level == 2 else 2)
        self._write_lines(text, size=sizes.get(level, 11), bold=True, line_h=6.5)
        if level <= 2:
            y = self.pdf.get_y()
            self.pdf.set_draw_color(*COLOR_ACCENT)
            self.pdf.set_line_width(0.4)
            self.pdf.line(MARGIN_L, y, MARGIN_L + 28, y)
            self.pdf.ln(3)

    def _write_bullet(self, text: str) -> None:
        self._ensure_space(LINE_H_BODY)
        self._reset_x()
        self._font("", 10)
        self._set_color_text()
        bullet = "\u2022  "
        self.pdf.set_x(self.pdf.l_margin + 2)
        self.pdf.multi_cell(8, LINE_H_BODY, bullet)
        x_after = self.pdf.l_margin + 7
        y_start = self.pdf.get_y() - LINE_H_BODY
        self.pdf.set_xy(x_after, y_start)
        wrapped = textwrap.wrap(_soft_break(_strip_md_inline(text)), width=int(self.epw * 0.4))
        for i, line in enumerate(wrapped):
            if i > 0:
                self._ensure_space(LINE_H_BODY)
                self.pdf.set_xy(x_after, self.pdf.get_y())
            self.pdf.multi_cell(self.epw - 7, LINE_H_BODY, line)
        self.pdf.ln(1)

    def _write_numbered(self, text: str) -> None:
        m = re.match(r"^(\d+)\.\s+(.*)", text.strip())
        if not m:
            self._write_lines(text, indent=4)
            return
        num, body = m.group(1), m.group(2)
        self._ensure_space(LINE_H_BODY)
        self._font("B", 10)
        self._set_color_accent()
        self.pdf.set_x(self.pdf.l_margin + 2)
        self.pdf.cell(8, LINE_H_BODY, f"{num}.")
        self._font("", 10)
        self._set_color_text()
        x_body = self.pdf.l_margin + 10
        y = self.pdf.get_y()
        self.pdf.set_xy(x_body, y)
        for i, line in enumerate(
            textwrap.wrap(_soft_break(_strip_md_inline(body)), width=int(self.epw * 0.42))
        ):
            if i > 0:
                self._ensure_space(LINE_H_BODY)
                self.pdf.set_xy(x_body, self.pdf.get_y())
            self.pdf.multi_cell(self.epw - 10, LINE_H_BODY, line)
        self.pdf.ln(1.5)

    def _set_color_accent(self) -> None:
        self.pdf.set_text_color(*COLOR_ACCENT)

    def _write_callout(self, title: str, lines: list[str], variant: str = "info") -> None:
        if variant == "warn":
            fill, border = COLOR_WARN_SOFT, COLOR_WARN_BORDER
        elif variant == "success":
            fill, border = COLOR_SUCCESS_SOFT, COLOR_SUCCESS_BORDER
        else:
            fill, border = COLOR_ACCENT_SOFT, COLOR_ACCENT

        pad = 4
        line_count = len(lines) + (1 if title else 0)
        box_h = pad * 2 + line_count * LINE_H_TIGHT + 4
        self._ensure_space(box_h)

        x = self.pdf.l_margin
        y = self.pdf.get_y()
        w = self.epw
        self.pdf.set_fill_color(*fill)
        self.pdf.set_draw_color(*border)
        self.pdf.set_line_width(0.3)
        self.pdf.rect(x, y, w, box_h, style="DF")

        self.pdf.set_xy(x + pad, y + pad)
        if title:
            self._font("B", 10)
            self.pdf.set_text_color(*border)
            self.pdf.multi_cell(w - pad * 2, LINE_H_TIGHT, _strip_md_inline(title))
            self.pdf.ln(1)

        self._font("", 9)
        self._set_color_text()
        for line in lines:
            self.pdf.set_x(x + pad)
            wrapped = textwrap.wrap(
                _soft_break(_strip_md_inline(line)), width=int((w - pad * 2) * 0.45)
            )
            for wl in wrapped:
                self.pdf.multi_cell(w - pad * 2, LINE_H_TIGHT, wl)
        self.pdf.set_y(y + box_h + 3)
        self._set_color_text()

    def _write_table_rows(self, rows: list[list[str]]) -> None:
        if not rows:
            return
        self._ensure_space(8)
        self.pdf.ln(2)
        for row in rows:
            label = row[0] if row else ""
            value = row[1] if len(row) > 1 else ""
            self._ensure_space(LINE_H_BODY * 2)
            y = self.pdf.get_y()
            # Colonne gauche (fond doux)
            self.pdf.set_fill_color(*COLOR_ACCENT_SOFT)
            self.pdf.set_draw_color(*COLOR_ACCENT_SOFT)
            col_w = min(52, self.epw * 0.38)
            self.pdf.rect(self.pdf.l_margin, y, col_w, LINE_H_BODY + 3, style="F")
            self._font("B", 9)
            self._set_color_accent()
            self.pdf.set_xy(self.pdf.l_margin + 2, y + 1.5)
            for line in textwrap.wrap(_strip_md_inline(label), width=22):
                self.pdf.cell(col_w - 4, LINE_H_TIGHT, line)

            # Colonne droite
            self._font("", 9)
            self._set_color_text()
            self.pdf.set_xy(self.pdf.l_margin + col_w + 3, y + 1.5)
            val_lines = textwrap.wrap(_soft_break(_strip_md_inline(value)), width=48)
            max_lines = max(1, len(val_lines))
            row_h = max(LINE_H_BODY + 3, max_lines * LINE_H_TIGHT + 2)
            self.pdf.set_fill_color(*COLOR_CARD)
            self.pdf.set_draw_color(228, 223, 214)
            self.pdf.rect(self.pdf.l_margin + col_w + 2, y, self.epw - col_w - 2, row_h, style="D")
            self.pdf.set_xy(self.pdf.l_margin + col_w + 5, y + 1.5)
            for line in val_lines:
                self.pdf.multi_cell(self.epw - col_w - 8, LINE_H_TIGHT, line)
            self.pdf.set_y(y + row_h + 2)
        self.pdf.ln(2)

    def write_cover(self) -> None:
        self._begin_page(cover=True)
        # Carte centrale
        card_w = self.epw
        card_h = 118
        x = self.pdf.l_margin
        y = 52
        self.pdf.set_fill_color(*COLOR_CARD)
        self.pdf.set_draw_color(228, 223, 214)
        self.pdf.set_line_width(0.2)
        self.pdf.rect(x, y, card_w, card_h, style="DF")

        # Icône bouclier simplifié
        self.pdf.set_fill_color(*COLOR_ACCENT_SOFT)
        self.pdf.rect(x + 14, y + 14, 18, 18, style="F")
        self._font("B", 14)
        self._set_color_accent()
        self.pdf.set_xy(x + 14, y + 16)
        self.pdf.cell(18, 14, "OP", align="C")

        self._font("B", 22)
        self._set_color_text()
        self.pdf.set_xy(x + 40, y + 18)
        self.pdf.cell(card_w - 50, 10, "OpenPrivacy.ch")

        self._font("", 11)
        self._set_color_muted()
        self.pdf.set_xy(x + 40, y + 30)
        self.pdf.cell(card_w - 50, 8, "Guide utilisateur")

        self.pdf.set_draw_color(*COLOR_ACCENT_SOFT)
        self.pdf.line(x + 14, y + 48, x + card_w - 14, y + 48)

        self._font("", 11)
        self._set_color_text()
        self.pdf.set_xy(x + 14, y + 56)
        bullets = [
            "Anonymisation locale des données personnelles",
            "Interface deux panneaux : Source / Résultat",
            "Fichiers texte et Word (.docx)",
            "Traitement 100 % sur votre ordinateur",
        ]
        for b in bullets:
            self.pdf.set_x(x + 14)
            self.pdf.multi_cell(card_w - 28, 6, f"  \u2022  {b}")

        self._font("", 9)
        self._set_color_muted()
        self.pdf.set_xy(x + 14, y + card_h - 14)
        self.pdf.cell(card_w - 28, 6, "Version 1.3.0  |  www.openprivacy.ch")

        self.pdf.set_y(y + card_h + 16)
        self._write_callout(
            "Important — logiciel non signé par Apple / Microsoft",
            [
                "Votre système peut afficher un avertissement de sécurité au premier lancement.",
                "C'est normal pour une distribution sans certificat éditeur payant.",
                "Ce guide explique étape par étape comment autoriser OpenPrivacy en toute confiance.",
            ],
            variant="warn",
        )

    def finish(self) -> None:
        self._end_page()

    def build_from_markdown(self, md_path: Path) -> None:
        lines = md_path.read_text(encoding="utf-8").splitlines()
        self.write_cover()
        self._begin_page()

        in_table = False
        table_rows: list[list[str]] = []
        in_security_mac = False
        in_security_win = False
        pending_question: str | None = None

        for raw in lines:
            line = raw.rstrip()

            # Tables markdown
            if line.startswith("|") and "|" in line[1:]:
                if re.match(r"^\|[\s\-:|]+\|$", line):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                table_rows.append(cells)
                in_table = True
                continue
            if in_table and table_rows:
                self._write_table_rows(
                    [[_strip_md_inline(c) for c in row] for row in table_rows]
                )
                table_rows = []
                in_table = False

            if not line.strip():
                self.pdf.ln(2)
                continue
            if line.strip() == "---":
                self.pdf.ln(2)
                in_security_mac = False
                in_security_win = False
                continue

            if line.startswith("# "):
                self._write_heading(line[2:].strip(), 1)
                continue
            if line.startswith("## "):
                title = line[3:].strip()
                in_security_mac = "Autoriser" in title and "Mac" in title
                in_security_win = "Autoriser" in title and "Windows" in title
                self._write_heading(title, 2)
                if in_security_mac:
                    self._write_callout(
                        "Pourquoi cet avertissement ?",
                        [
                            "OpenPrivacy n'est pas signé avec un certificat Apple Developer ID.",
                            "macOS bloque par précaution les applications téléchargées hors App Store.",
                            "Si vous avez téléchargé depuis openprivacy.ch, vous pouvez autoriser l'app en suivant les étapes ci-dessous.",
                        ],
                        variant="warn",
                    )
                if in_security_win:
                    self._write_callout(
                        "Pourquoi SmartScreen s'affiche ?",
                        [
                            "Windows filtre les exécutables dont l'éditeur n'est pas reconnu commercialement.",
                            "Débloquez le fichier puis confirmez l'exécution — uniquement si la source est de confiance.",
                        ],
                        variant="warn",
                    )
                continue
            if line.startswith("### "):
                self._write_heading(line[4:].strip(), 3)
                continue
            if line.startswith("- "):
                self._write_bullet(line[2:].strip())
                continue
            if re.match(r"^\d+\.\s", line):
                self._write_numbered(line.strip())
                continue
            if line.startswith("*(") and line.endswith(")*"):
                self._write_lines(line.strip("()* "), size=9, color=COLOR_MUTED, line_h=LINE_H_TIGHT)
                continue
            if line.startswith("**") and line.endswith("**") and line.count("**") == 2:
                pending_question = _strip_md_inline(line.strip("* "))
                continue
            if pending_question and line.strip():
                self._write_lines(pending_question, bold=True, size=10)
                self._write_lines(line.strip(), size=10)
                pending_question = None
                continue
            if line.startswith("**") and "**" in line[2:]:
                parts = line.split("**")
                if len(parts) >= 3 and parts[1].strip():
                    q = parts[1].strip()
                    a = parts[2].strip().lstrip(":").strip()
                    self._ensure_space(LINE_H_BODY * 2)
                    self._write_lines(q, bold=True, size=10, line_h=LINE_H_BODY)
                    if a:
                        self._write_lines(a, size=10)
                    continue
            self._write_lines(line)

        if in_table and table_rows:
            self._write_table_rows(
                [[_strip_md_inline(c) for c in row] for row in table_rows]
            )

        self.finish()

    def output(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pdf.output(str(path))


def build_pdf(md_path: Path, out_path: Path) -> None:
    try:
        from fpdf import FPDF  # noqa: F401
    except ImportError as exc:
        raise SystemExit("Installez fpdf2 : pip install fpdf2") from exc

    regular = _find_font(FONT_CANDIDATES_REG)
    bold = _find_font(FONT_CANDIDATES_BOLD)
    if not regular:
        raise SystemExit("Police TrueType introuvable (Arial / DejaVu).")

    guide = GuidePDF(regular, bold)
    guide.build_from_markdown(md_path)
    guide.output(out_path)


def main() -> None:
    if not SOURCE.is_file():
        print(f"Fichier introuvable : {SOURCE}", file=sys.stderr)
        sys.exit(1)
    build_pdf(SOURCE, OUTPUT)
    print(f"✓ PDF créé : {OUTPUT}")


if __name__ == "__main__":
    main()
