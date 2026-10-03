#!/usr/bin/env python3
"""
generate_report.py — locked report template for the social-media-report skill.

USAGE:
    python3 generate_report.py <input_data.json> <output.pdf>

This script owns ALL visual styling (fonts, colors, chart style, table style,
page layout). Do not restyle reports by editing prose instructions elsewhere —
if the look needs to change, change it here, once, so every past and future
report stays visually consistent.

INPUT JSON SCHEMA (see references/report-spec.md for the content rules that
produce this data):

{
  "meta": {
    "account_name": str, "platform": str, "period_label": str,
    "comparison_labels": [str, ...], "report_type": "monthly"|"yearly",
    "data_sources": [str, ...], "currency": str, "prepared_date": str
  },
  "kpis": [
    {"name": str, "value_display": str, "per_day_display": str|None,
     "change_pct": float|None, "change_pt": float|None, "change_label": str,
     "unavailable": bool}
  ],
  "performance_table": {"id": str, "title": str, "columns": [str,...],
    "rows": [[cell, ...], ...]},   # cell is a str, OR a dict for values that
                                    # should carry an inline change marker:
                                    # {"value": str, "change_pct": float} or
                                    # {"value": str, "change_pt": float}
  "segment_table": {"id": str, "title": str, "columns": [str,...], "rows": [[cell,...],...]} | None,
  "charts": [
    {"id": str, "type": "trend"|"composition"|"waterfall"|"benchmark",
     "title": str, "takeaway": str, ...type-specific fields, see build_chart()}
    # benchmark charts: "account_value", "benchmark_value", and optionally
    # "account_basis" / "benchmark_basis" (the denominator, e.g. "reach",
    # "followers", "views"). Give both: a mismatch is drawn as not comparable.
  ],
  "findings": [str, ...],            # may contain [[link text|ref_id]] markup
  "analysis_paragraphs": [str, ...], # may contain [[link text|ref_id]] markup
  "recommendations": [
    {"priority": str, "title": str, "body": str}  # body may contain [[..|..]] markup
  ],
  "glossary": {
    "definitions": [{"term": str, "meaning": str}],
    "formulas": [{"measure": str, "formula": str}],
    "benchmark_sources": [{"platform": str, "metric": str, "value": str, "source": str}],
    "data_notes": [str, ...]
  }
}

"Unavailable" values should already be formatted as the string "Unavailable" in
table cells by the caller — this script renders them in muted italic automatically.
For dict-form cells, put "Unavailable" as the "value" and omit change_pct/change_pt.

CHANGE MARKERS: don't add a separate "Change vs X" column. Put the change on the
cell it belongs to instead — a dict cell with change_pct (or change_pt for an
already-percentage metric like engagement rate) renders as the value followed by
a colored arrow marker (▲ green for increase, ▼ red for decrease, dash for no
change or for a suppressed small-base comparison per report-spec.md). Same
mechanism for KPI cards via change_pct/change_pt + change_label on the kpi dict.
Only put a change marker on the metric's own current-period cell — comparison-only
columns (last month, two months back) stay plain strings with no marker, since
they aren't "the current value vs. something," they're the baseline being
compared against.
"""

import json
import math
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, CondPageBreak, Flowable, KeepTogether,
)

# ---------------------------------------------------------------------------
# LOCKED STYLE — change here, nowhere else
# ---------------------------------------------------------------------------

NAVY = colors.HexColor("#0B2545")
SLATE = colors.HexColor("#334155")
SLATE_LIGHT = colors.HexColor("#F1F5F9")
SLATE_MID = colors.HexColor("#CBD5E1")
ACCENT = colors.HexColor("#2563EB")
KPI_DIVIDER = colors.HexColor("#1E3A5F")

# Per-platform brand color, applied by apply_platform_theme() at the start of
# build_report(). Everything else in the template — body text, table banding,
# grid lines, the universal green/red change markers — stays fixed, so a
# report is still recognizably "this skill's report" across every platform;
# only the header/KPI-card color and the primary chart accent shift.
#
# "dark" needs enough contrast for white text (KPI cards, table headers) and
# should not be a color already used for something semantic elsewhere (the
# green/red change markers, in particular) — hence YouTube and TikTok use
# near-black rather than their literal brand red/cyan for backgrounds, saving
# the bright brand color for chart lines and accents instead, where a pure
# saturated brand color reads well against a white page.
PLATFORM_THEMES = {
    "facebook": {"dark": "#0B2A4A", "accent": "#1877F2",
                 "divider": "#1E3A5F", "name": "Facebook"},
    "instagram": {"dark": "#4C1D3D", "accent": "#D6249F", "accent2": "#F77737",
                  "divider": "#6B2F5E", "name": "Instagram"},
    "tiktok": {"dark": "#0A0A0A", "accent": "#00C4CC", "accent2": "#FE2C55",
               "divider": "#2A2A2A", "name": "TikTok"},
    "youtube": {"dark": "#141414", "accent": "#FF0000",
                "divider": "#2E2E2E", "name": "YouTube"},
}
DEFAULT_THEME = {"dark": "#0B2545", "accent": "#2563EB",
                  "divider": "#1E3A5F", "name": "Platform"}


def apply_platform_theme(platform: str) -> dict:
    """Recolor the header/KPI-card accent and primary chart color for this
    platform. Called once at the start of build_report(); every function that
    reads NAVY/ACCENT/CHART_PALETTE as a module global picks up the new value
    because Python resolves globals at call time, not at def time.
    """
    theme = PLATFORM_THEMES.get((platform or "").strip().lower(), DEFAULT_THEME)
    global NAVY, ACCENT, KPI_DIVIDER
    NAVY = colors.HexColor(theme["dark"])
    ACCENT = colors.HexColor(theme["accent"])
    KPI_DIVIDER = colors.HexColor(theme["divider"])
    CHART_PALETTE[0] = theme["accent"]
    if theme.get("accent2"):
        CHART_PALETTE[1] = theme["accent2"]
    for style_name in ("Title", "H1", "H2", "GlossaryTerm", "RecTitle"):
        STYLES[style_name].textColor = NAVY
    STYLES["RecPriority"].textColor = ACCENT
    return theme
POSITIVE = colors.HexColor("#15803D")
NEGATIVE = colors.HexColor("#B91C1C")
MUTED = colors.HexColor("#94A3B8")
WHITE = colors.white

# Light-on-dark variants for markers drawn on the navy KPI-card background —
# the standard POSITIVE/NEGATIVE greens/reds are too dark to read on navy.
POSITIVE_ON_DARK = "#4ADE80"
NEGATIVE_ON_DARK = "#FCA5A5"
MUTED_ON_DARK = "#CBD5E1"

ARROW_UP = "\u25B2"
ARROW_DOWN = "\u25BC"


def change_marker(change, unit="%", on_dark=False) -> str:
    """Inline colored arrow + change amount, for embedding directly in a cell
    or KPI value instead of putting the change in its own table column.

    change: numeric delta, already suppressed to None upstream if the base
    was too small to be meaningful (see references/report-spec.md). unit is
    "%" for a percent change or "pt" for a percentage-point change.
    """
    if change is None:
        color = MUTED_ON_DARK if on_dark else MUTED
        return f' <font color="{color}">\u2014</font>'
    pos = POSITIVE_ON_DARK if on_dark else "#15803D"
    neg = NEGATIVE_ON_DARK if on_dark else "#B91C1C"
    if change > 0:
        return f' <font color="{pos}">{ARROW_UP} +{change:g}{unit}</font>'
    if change < 0:
        return f' <font color="{neg}">{ARROW_DOWN} {change:g}{unit}</font>'
    mut = MUTED_ON_DARK if on_dark else MUTED
    return f' <font color="{mut}">\u2014 0{unit}</font>'

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"

CHART_PALETTE = ["#0B2545", "#2563EB", "#D97706", "#15803D", "#B91C1C", "#7C3AED"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#CBD5E1",
    "axes.labelcolor": "#334155",
    "text.color": "#334155",
    "xtick.color": "#334155",
    "ytick.color": "#334155",
    "axes.grid": True,
    "grid.color": "#E2E8F0",
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 200,
})

STYLES = {
    "Title": ParagraphStyle("Title", fontName=FONT_BOLD, fontSize=20, textColor=NAVY,
                             spaceAfter=4, leading=24),
    "Subtitle": ParagraphStyle("Subtitle", fontName=FONT, fontSize=11, textColor=SLATE,
                                spaceAfter=14, leading=14),
    "H1": ParagraphStyle("H1", fontName=FONT_BOLD, fontSize=15, textColor=NAVY,
                          spaceBefore=18, spaceAfter=8, leading=18, keepWithNext=1),
    # keepWithNext: a heading never sits alone at the foot of a page while its
    # table or text starts on the next one.
    "H2": ParagraphStyle("H2", fontName=FONT_BOLD, fontSize=12, textColor=NAVY,
                          spaceBefore=12, spaceAfter=6, leading=15, keepWithNext=1),
    "Body": ParagraphStyle("Body", fontName=FONT, fontSize=9.5, textColor=SLATE,
                            leading=14, spaceAfter=8, alignment=TA_LEFT),
    "Bullet": ParagraphStyle("Bullet", fontName=FONT, fontSize=9.5, textColor=SLATE,
                              leading=14, spaceAfter=6, leftIndent=14, bulletIndent=2),
    "Caption": ParagraphStyle("Caption", fontName=FONT_ITALIC, fontSize=8.5,
                               textColor=MUTED, leading=11, spaceAfter=10),
    "KPILabel": ParagraphStyle("KPILabel", fontName=FONT, fontSize=8.5, textColor=WHITE,
                                leading=11),
    "KPIValue": ParagraphStyle("KPIValue", fontName=FONT_BOLD, fontSize=16, textColor=WHITE,
                                leading=19, spaceBefore=2),
    "KPIChange": ParagraphStyle("KPIChange", fontName=FONT, fontSize=8.5, textColor=WHITE,
                                 leading=11),
    "TableCell": ParagraphStyle("TableCell", fontName=FONT, fontSize=8.5, textColor=SLATE,
                                 leading=11),
    "TableCellSmall": ParagraphStyle("TableCellSmall", fontName=FONT, fontSize=7.3,
                                      textColor=SLATE, leading=9.5),
    "TableCellMuted": ParagraphStyle("TableCellMuted", fontName=FONT_ITALIC, fontSize=8.5,
                                      textColor=MUTED, leading=11),
    "TableCellMutedSmall": ParagraphStyle("TableCellMutedSmall", fontName=FONT_ITALIC,
                                           fontSize=7.3, textColor=MUTED, leading=9.5),
    "TableHeader": ParagraphStyle("TableHeader", fontName=FONT_BOLD, fontSize=8.5,
                                   textColor=WHITE, leading=11),
    "TableHeaderSmall": ParagraphStyle("TableHeaderSmall", fontName=FONT_BOLD, fontSize=7.3,
                                        textColor=WHITE, leading=9.5),
    "GlossaryTerm": ParagraphStyle("GlossaryTerm", fontName=FONT_BOLD, fontSize=9,
                                    textColor=NAVY, leading=12, keepWithNext=1),
    "RecTitle": ParagraphStyle("RecTitle", fontName=FONT_BOLD, fontSize=10.5,
                                textColor=NAVY, leading=13, spaceAfter=2),
    "RecPriority": ParagraphStyle("RecPriority", fontName=FONT_BOLD, fontSize=7.5,
                                   textColor=ACCENT, leading=10, spaceAfter=4),
}

LINK_RE = re.compile(r"\[\[(.*?)\|(.*?)\]\]")


def linkify(text: str) -> str:
    """Convert [[label|ref_id]] markup into a clickable internal PDF link."""
    def repl(m):
        label, ref_id = m.group(1), m.group(2)
        return f'<a href="#{ref_id}" color="#2563EB"><u>{label}</u></a>'
    return LINK_RE.sub(repl, text)


class Bookmark(Flowable):
    """Invisible flowable that registers a named internal-link destination
    at the point it's placed, so [[label|ref_id]] links elsewhere can jump here."""
    def __init__(self, name):
        Flowable.__init__(self)
        self.name = name

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        self.canv.bookmarkPage(self.name)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def _fmt_value(x, _pos=None):
    """Format axis ticks readably across the full range these reports span.

    Views run to the tens of millions while rates like CTR sit between 4 and 6,
    so a single integer format would render a percentage axis as "5, 5, 5, 4, 4"
    with every tick collapsed to the same label.
    """
    ax = abs(x)
    if ax >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if ax >= 1_000:
        return f"{x/1_000:.0f}K"
    if ax >= 100 or x == 0:
        return f"{x:.0f}"
    if ax >= 1:
        return f"{x:.1f}"
    return f"{x:.2f}"


# Kept as an alias so existing callers and any external references keep working.
_fmt_thousands = _fmt_value


class _AxisValueFormatter(mticker.Formatter):
    """Tick labels whose precision follows the tick spacing, not the value.

    _fmt_value picks decimals from each value's magnitude alone, so a narrow
    range collapses: engagement rates of 1.83-1.96 all read "1.9", interactions
    of 2.9K-4.1K all read "3K". Here one unit (M, K or none) is chosen for the
    whole axis from its largest tick, and just enough decimals to tell adjacent
    ticks apart.
    """

    _ticks: list = []

    def set_locs(self, locs):
        self._ticks = [float(v) for v in locs]

    def format_ticks(self, values):
        self.set_locs(values)
        return [self(v, i) for i, v in enumerate(values)]

    def __call__(self, x, pos=None):
        locs = self._ticks or [x]
        top = max(abs(v) for v in locs)
        scale, suffix = (1_000_000, "M") if top >= 1_000_000 else (
            (1_000, "K") if top >= 1_000 else (1, ""))
        steps = [abs(b - a) for a, b in zip(locs, locs[1:]) if b != a]
        if steps:
            # Fewest decimals that show the step exactly (0.25 needs 2, not 1).
            step = min(steps) / scale
            decimals = next((d for d in range(4)
                             if abs(step * 10**d - round(step * 10**d)) < 1e-6 * max(1, step * 10**d)), 3)
        else:
            decimals = 0 if top >= 100 else 1
        if x == 0:
            return "0"
        return f"{x / scale:.{decimals}f}{suffix}"


def _axis_formatter():
    return _AxisValueFormatter()


def _pad_category_axis(ax, n_categories: int):
    """Keep bars a sensible width when there are only one or two categories.

    Matplotlib spreads categories across the full axis, so a single-period
    composition chart renders as one bar stretched across the whole figure,
    which reads as a filled background rather than as a bar.
    """
    if n_categories <= 1:
        ax.set_xlim(-1.6, 1.6)
    elif n_categories == 2:
        ax.set_xlim(-1.0, 2.0)
    elif n_categories == 3:
        ax.set_xlim(-0.7, 2.7)


def build_chart(spec: dict, out_path: Path) -> Path:
    ctype = spec["type"]
    fig, ax = plt.subplots(figsize=(6.4, 3.1))

    if ctype == "trend":
        labels = spec["labels"]
        for i, s in enumerate(spec["series"]):
            ax.plot(labels, s["values"], marker="o", linewidth=2,
                    color=CHART_PALETTE[i % len(CHART_PALETTE)], label=s["name"])
        # Shade any period with no data so a gap reads as "not supplied" rather than
        # as zero or as an unremarkable flat stretch.
        missing = spec.get("missing_labels") or []
        for lbl in missing:
            if lbl in labels:
                idx = labels.index(lbl)
                ax.axvspan(idx - 0.5, idx + 0.5, color="#E2E8F0", alpha=0.75, zorder=0)
        if len(spec["series"]) > 1:
            # "best" keeps the legend off the lines; a fixed corner sat on top
            # of a series that started high.
            ax.legend(frameon=False, loc="best", fontsize=8)
        # One point, or a flat series, autoscales to a sliver around the value
        # and every tick reads the same; give it a real range instead.
        values = [v for s in spec["series"] for v in s["values"]
                  if isinstance(v, (int, float)) and not math.isnan(v)]
        if values and max(values) == min(values):
            top = max(values)
            ax.set_ylim(0, top * 1.2 if top > 0 else 1)
        elif values and min(values) > 0:
            # Autoscale stretches any change to fill the plot, so +0.13pt on a
            # 1.9% rate or -9% on views reads as a spike or a crash. Keep the
            # range at least 30% of the top value, centred on the data, so the
            # slope reflects the size of the change.
            lo, hi = min(values), max(values)
            min_span = 0.30 * hi
            if hi - lo < min_span:
                bottom = (hi + lo) / 2 - min_span / 2
                if bottom <= 0:
                    ax.set_ylim(0, hi * 1.1)
                else:
                    ax.set_ylim(bottom, bottom + min_span)
        ax.yaxis.set_major_formatter(_axis_formatter())
        # Notes sit above the plot, where they cannot cover a data point.
        notes = []
        if missing:
            notes.append("Shaded = data not supplied")
        y_bottom = ax.get_ylim()[0]
        if y_bottom > 0:
            notes.append(f"Axis starts at {_fmt_value(y_bottom)}, not zero")
        if notes:
            ax.text(1.0, 1.02, "   ·   ".join(notes), transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=7.5, color="#64748B")
        if len(labels) > 12:
            # One tick per day overlaps illegibly; show ~10 evenly spaced
            # ticks (always including the last), angled if the labels are long.
            step = max(1, len(labels) // 10)
            idx = list(range(0, len(labels), step))
            if idx[-1] != len(labels) - 1:
                idx.append(len(labels) - 1)
            angled = max(len(str(lbl)) for lbl in labels) > 3
            ax.set_xticks(idx)
            ax.set_xticklabels([labels[i] for i in idx], rotation=45 if angled else 0,
                               ha="right" if angled else "center", fontsize=8)
        elif len(labels) > 6:
            plt.xticks(fontsize=8)

    elif ctype == "composition":
        labels = spec["labels"]
        bottom = [0] * len(labels)
        for i, s in enumerate(spec["series"]):
            ax.bar(labels, s["values"], bottom=bottom,
                   color=CHART_PALETTE[i % len(CHART_PALETTE)], label=s["name"], width=0.55)
            bottom = [b + v for b, v in zip(bottom, s["values"])]
        _pad_category_axis(ax, len(labels))
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12),
                   ncol=min(len(spec["series"]), 4), fontsize=8)
        ax.yaxis.set_major_formatter(_axis_formatter())

    elif ctype == "waterfall":
        cats = spec["categories"]
        vals = spec["values"]
        cum = 0
        for i, (c, v) in enumerate(zip(cats, vals)):
            color = POSITIVE_HEX if v >= 0 else NEGATIVE_HEX
            bottom = cum if v >= 0 else cum + v
            height = abs(v)
            ax.bar(c, height, bottom=bottom, color=color, width=0.6)
            cum += v
        ax.axhline(0, color="#334155", linewidth=0.8)
        ax.yaxis.set_major_formatter(_axis_formatter())
        plt.xticks(rotation=20, ha="right")

    elif ctype == "benchmark":
        cats = ["This account", "Benchmark"]
        vals = [spec["account_value"], spec["benchmark_value"]]
        acc_basis = (spec.get("account_basis") or "").strip()
        bench_basis = (spec.get("benchmark_basis") or "").strip()
        if acc_basis and bench_basis:
            cats = [f"This account\n(per {acc_basis})", f"Benchmark\n(per {bench_basis})"]
        # A reach- or view-based rate runs many times a follower-based one, so
        # side-by-side bars on different denominators show methodology, not
        # performance. Draw the benchmark hollow and say so above the plot.
        mismatch = bool(acc_basis and bench_basis
                        and acc_basis.lower() != bench_basis.lower())
        bars = ax.bar(cats, vals, color=[CHART_PALETTE[0], MUTED_HEX], width=0.45)
        if mismatch:
            bars[1].set_facecolor("none")
            bars[1].set_edgecolor(MUTED_HEX)
            bars[1].set_hatch("///")
            ax.text(1.0, 1.02, "Different denominators: not a like-for-like comparison",
                    transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5,
                    color="#B45309")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:g}%", ha="center",
                    va="bottom", fontsize=9, color="#334155")
        _pad_category_axis(ax, len(cats))
        ax.yaxis.set_major_formatter(_axis_formatter())

    else:
        raise ValueError(f"Unknown chart type: {ctype}")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


POSITIVE_HEX = "#15803D"
NEGATIVE_HEX = "#B91C1C"
MUTED_HEX = "#94A3B8"


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

def _column_widths(spec: dict, total_width: float, cell_font_size: float,
                   header_font_size: float) -> list:
    """Size columns from measured text width rather than an estimate.

    Equal-width columns force long values like "Unavailable" to break mid-word
    in narrow columns while leaving short numeric columns half empty. Measuring
    the widest unbreakable token per column guarantees each column can hold its
    own content, then any leftover space is shared out by overall content length.
    """
    pad = 12  # matches LEFTPADDING + RIGHTPADDING in the table style
    n_cols = len(spec["columns"])

    min_widths, weights = [], []
    for i, col in enumerate(spec["columns"]):
        cells = []
        for r in spec["rows"]:
            if i >= len(r):
                continue
            c = r[i]
            if isinstance(c, dict):
                text = str(c.get("value", ""))
                # Reserve room for the marker (" ▼ -12.3%") so it doesn't get
                # squeezed against the value once change_marker() is appended.
                if "change_pct" in c or "change_pt" in c:
                    text += " \u25bc -100.0%"
                cells.append(text)
            else:
                cells.append(str(c))
        # Widest single word that cannot be broken across lines.
        header_tokens = [
            pdfmetrics.stringWidth(w, FONT_BOLD, header_font_size)
            for w in str(col).split()
        ] or [0]
        cell_tokens = [
            pdfmetrics.stringWidth(w, FONT, cell_font_size)
            for c in cells for w in c.split()
        ] or [0]
        min_widths.append(max(max(header_tokens), max(cell_tokens)) + pad)
        # Full-string widths drive how leftover space is shared.
        full = [pdfmetrics.stringWidth(c, FONT, cell_font_size) for c in cells] or [0]
        weights.append(max(max(full), pdfmetrics.stringWidth(str(col), FONT_BOLD,
                                                             header_font_size)) + pad)

    required = sum(min_widths)
    if required >= total_width:
        # Content genuinely doesn't fit; fall back to proportional and let
        # the smaller font handle it rather than overflowing the page.
        scale = total_width / required
        return [w * scale for w in min_widths]

    spare = total_width - required
    weight_total = sum(weights)
    return [m + spare * (w / weight_total) for m, w in zip(min_widths, weights)]


def build_data_table(spec: dict) -> list:
    """Returns [Bookmark, Paragraph(title), Table] for a performance/segment table."""
    flow = [Bookmark(spec["id"]), Paragraph(spec["title"], STYLES["H2"])]

    n_cols = len(spec["columns"])
    compact = n_cols > 6
    header_style = STYLES["TableHeaderSmall"] if compact else STYLES["TableHeader"]
    cell_style = STYLES["TableCellSmall"] if compact else STYLES["TableCell"]
    muted_style = STYLES["TableCellMutedSmall"] if compact else STYLES["TableCellMuted"]
    cell_size = 7.3 if compact else 8.5
    header_size = 7.3 if compact else 8.5

    header = [Paragraph(c, header_style) for c in spec["columns"]]
    rows = [header]
    total_row_idx = None
    for r_i, row in enumerate(spec["rows"]):
        cells = []
        for cell in row:
            if isinstance(cell, dict):
                val = str(cell.get("value", ""))
                if val.strip().lower() == "unavailable":
                    cells.append(Paragraph("Unavailable", muted_style))
                    continue
                change = cell.get("change_pct", cell.get("change_pt"))
                unit = "pt" if "change_pt" in cell else "%"
                marker = change_marker(change, unit=unit) if "change_pct" in cell or "change_pt" in cell else ""
                cells.append(Paragraph(val + marker, cell_style))
            elif str(cell).strip().lower() == "unavailable":
                cells.append(Paragraph("Unavailable", muted_style))
            else:
                cells.append(Paragraph(str(cell), cell_style))
        # A row whose first cell reads like a total gets emphasised, so a
        # summary line isn't visually identical to the rows it sums.
        if any(k in str(row[0]).lower() for k in ("total", "all months", "combined")):
            total_row_idx = r_i + 1
        rows.append(cells)

    col_widths = _column_widths(spec, 6.6 * inch, cell_size, header_size)
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, SLATE_MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if total_row_idx is not None:
        style_cmds += [
            ("BACKGROUND", (0, total_row_idx), (-1, total_row_idx), colors.HexColor("#E2E8F0")),
            ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1.0, NAVY),
        ]
    t.setStyle(TableStyle(style_cmds))
    flow.append(t)
    flow.append(Spacer(1, 10))
    return flow


def build_kpi_row(kpis: list) -> Table:
    cells = []
    for k in kpis:
        block = [Paragraph(k["name"].upper(), STYLES["KPILabel"])]
        if k.get("unavailable"):
            block.append(Paragraph("Unavailable", STYLES["KPIValue"]))
        else:
            block.append(Paragraph(k["value_display"], STYLES["KPIValue"]))
            change = k.get("change_pct", k.get("change_pt"))
            if change is not None:
                unit = "pt" if "change_pt" in k else k.get("change_unit", "%")
                marker = change_marker(change, unit=unit, on_dark=True)
                label = k.get("change_label", "")
                block.append(Paragraph(f"{marker} {label}".strip(), STYLES["KPIChange"]))
            if k.get("per_day_display"):
                block.append(Paragraph(f"{k['per_day_display']} / day", STYLES["KPIChange"]))
        cells.append(block)

    n = len(cells)
    col_width = (6.6 * inch) / n
    t = Table([cells], colWidths=[col_width] * n)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, KPI_DIVIDER),
    ]))
    return t


def build_recommendation(rec: dict) -> list:
    return [
        Paragraph(rec["priority"].upper(), STYLES["RecPriority"]),
        Paragraph(rec["title"], STYLES["RecTitle"]),
        Paragraph(linkify(rec["body"]), STYLES["Body"]),
        Spacer(1, 6),
    ]


# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------

def make_page_decorator(meta: dict):
    def _decorate(canv, doc):
        canv.saveState()
        canv.setFillColor(SLATE)
        canv.setFont(FONT, 8)
        header_text = f"{meta['account_name']}  ·  {meta['platform']} performance"
        canv.drawString(0.75 * inch, LETTER[1] - 0.55 * inch, header_text)
        canv.drawRightString(LETTER[0] - 0.75 * inch, LETTER[1] - 0.55 * inch,
                              meta["period_label"])
        canv.setStrokeColor(ACCENT)
        canv.setLineWidth(1.3)
        canv.line(0.75 * inch, LETTER[1] - 0.62 * inch, LETTER[0] - 0.75 * inch,
                  LETTER[1] - 0.62 * inch)
        canv.setFont(FONT, 8)
        canv.setFillColor(MUTED)
        canv.drawString(0.75 * inch, 0.5 * inch,
                         f"Performance report · {meta['account_name']}")
        canv.drawRightString(LETTER[0] - 0.75 * inch, 0.5 * inch, str(canv.getPageNumber()))
        canv.restoreState()
    return _decorate


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_report(data: dict, output_path: Path, tmp_dir: Path):
    meta = dict(data["meta"])
    # Print known platforms under their own spelling, whatever case the data
    # used: "facebook" titled a report "facebook performance report".
    theme = PLATFORM_THEMES.get((meta.get("platform") or "").strip().lower())
    if theme:
        meta["platform"] = theme["name"]
    apply_platform_theme(meta.get("platform", ""))
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER,
                             topMargin=0.9 * inch, bottomMargin=0.75 * inch,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                             title=f"{meta['account_name']} — {meta['platform']} performance report")
    story = []

    # --- Header block ---
    story.append(Paragraph(f"{meta['platform']} performance report", STYLES["Title"]))
    subtitle = (f"{meta['account_name']} &nbsp;·&nbsp; {meta['period_label']}, compared "
                f"against {', '.join(meta['comparison_labels'])}")
    story.append(Paragraph(subtitle, STYLES["Subtitle"]))

    meta_rows = [
        ["Data source", ", ".join(meta["data_sources"])],
        ["Currency", meta["currency"]],
        ["Prepared", meta["prepared_date"]],
    ]
    mt = Table([[Paragraph(f"<b>{k}</b>", STYLES["TableCell"]), Paragraph(v, STYLES["TableCell"])]
                for k, v in meta_rows], colWidths=[1.3 * inch, 5.3 * inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SLATE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, SLATE_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 14))

    # --- Executive summary ---
    story.append(Paragraph("Executive summary", STYLES["H1"]))
    story.append(build_kpi_row(data["kpis"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Key findings", STYLES["H2"]))
    for f in data["findings"]:
        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{linkify(f)}", STYLES["Bullet"]))
    story.append(PageBreak())

    # --- Performance table ---
    story.extend(build_data_table(data["performance_table"]))

    # --- Segment table ---
    if data.get("segment_table"):
        story.extend(build_data_table(data["segment_table"]))

    story.append(PageBreak())

    # --- Charts ---
    story.append(Paragraph("Visual analysis", STYLES["H1"]))
    for i, chart in enumerate(data["charts"]):
        png_path = tmp_dir / f"chart_{i}.png"
        build_chart(chart, png_path)
        block = [
            Bookmark(chart["id"]),
            Paragraph(f"Exhibit {i+1} — {chart['title']}", STYLES["H2"]),
            Image(str(png_path), width=6.6 * inch, height=3.2 * inch),
            Paragraph(linkify(chart["takeaway"]), STYLES["Caption"]),
            Spacer(1, 8),
        ]
        story.append(KeepTogether(block))

    # Analysis and the glossary start on a new page only when the current one
    # is mostly used; a hard break left pages holding one chart or one
    # recommendation. The glossary is still the last section.
    story.append(CondPageBreak(3.5 * inch))

    # --- Analysis ---
    story.append(Paragraph("Analysis", STYLES["H1"]))
    for p in data["analysis_paragraphs"]:
        story.append(Paragraph(linkify(p), STYLES["Body"]))

    story.append(Spacer(1, 8))

    # --- Recommendations ---
    story.append(Paragraph("Recommendations", STYLES["H1"]))
    for rec in data["recommendations"]:
        story.append(KeepTogether(build_recommendation(rec)))

    story.append(CondPageBreak(3.5 * inch))

    # --- Glossary ---
    g = data["glossary"]
    story.append(Paragraph("Glossary", STYLES["H1"]))

    story.append(Paragraph("Definitions", STYLES["H2"]))
    for d in g["definitions"]:
        story.append(Paragraph(d["term"], STYLES["GlossaryTerm"]))
        story.append(Paragraph(d["meaning"], STYLES["Body"]))

    story.append(Paragraph("Derived measures", STYLES["H2"]))
    rows = [[Paragraph("Measure", STYLES["TableHeader"]), Paragraph("Formula", STYLES["TableHeader"])]]
    for f in g["formulas"]:
        rows.append([Paragraph(f["measure"], STYLES["TableCell"]),
                     Paragraph(f["formula"], STYLES["TableCell"])])
    ft = Table(rows, colWidths=[2.3 * inch, 4.3 * inch], repeatRows=1)
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, SLATE_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ft)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Benchmark sources", STYLES["H2"]))
    for b in g["benchmark_sources"]:
        story.append(Paragraph(
            f"<b>{b['platform']} {b['metric']}:</b> {b['value']} — {b['source']}",
            STYLES["Body"]))

    story.append(Paragraph("Data notes", STYLES["H2"]))
    for n in g["data_notes"]:
        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{n}", STYLES["Bullet"]))

    decorator = make_page_decorator(meta)
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate_report.py <input_data.json> <output.pdf>")
        sys.exit(1)
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    tmp_dir = output_path.parent / ".chart_tmp"
    tmp_dir.mkdir(exist_ok=True, parents=True)

    data = json.loads(input_path.read_text())
    build_report(data, output_path, tmp_dir)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
