---
name: social-media-report
description: Builds a professional, corporate-style PDF performance report for one social platform (Facebook, Instagram, TikTok, or YouTube) from uploaded analytics exports — computing engagement rate, CTR, follower growth, and revenue, benchmarking against industry defaults, and rendering through a locked template so every month's report looks identical. Use this whenever the user asks to build, generate, or update a social media report for a platform and time period ("build a Facebook report for August," "generate the 2026 yearly Instagram report"), or shares platform analytics exports (Facebook or Instagram Insights, TikTok, YouTube Studio) and asks any question about the numbers — comparing periods, checking whether a change is real, or finding what drove it — even if they don't say the word "report" and want a quick answer rather than a PDF.
---

# Social Media Performance Report

## Overview

This skill turns a raw platform analytics export into a polished, client-ready PDF
report. It has two locked pieces that should not be improvised around:

1. **The visual template** (`scripts/generate_report.py`) — fonts, colors, chart
   style, and layout are fixed in code. Every report is produced by feeding this
   script structured data; never hand-build a PDF a different way, or the "looks the
   same every month" guarantee breaks.
2. **The report logic** (this file + `references/`) — how to parse exports, which
   comparison window to use, how to normalize for day-count differences, and how to
   handle missing data. This is where judgment happens; the template just renders
   whatever this logic decides.

One platform per run. If the request or upload doesn't make the platform and period
obvious, ask before proceeding — guessing wrong here means redoing the whole report.

## Step 1 — Identify platform, period, and inputs

Determine from the request: which platform (Facebook, Instagram, TikTok, or YouTube),
whether it's a monthly or yearly report, and the specific period. Then check what's
been supplied: a raw CSV/XLSX export, a prior month's own PDF report (re-extract data
from it — see Step 2), or some mix. For yearly reports, the source data may arrive as
12 monthly files, a handful of staggered files with gaps, or a single annual export —
handle whatever's actually there rather than assuming a complete set.

## Step 2 — Extract and normalize the data

Read the file(s) with pandas (CSV/XLSX) or pdfplumber (PDF — see `/mnt/skills/public/pdf/SKILL.md`
for extraction techniques). Match columns against `references/export-schemas.md`,
which lists the expected fields and common aliases per platform. That file is a
best-effort default, not a guarantee — if a column central to the report (views,
interactions, revenue) can't be confidently matched, ask the user what it is rather
than guessing. If it's a minor column that doesn't match anything, say so in the data
notes rather than silently dropping it.

If a platform provides the same period's data across multiple files (e.g. Facebook's
daily export plus a separate monetization export), reconcile them and note the
reconciliation in the glossary's data notes, the way a careful analyst would flag it.

## Step 3 — Set the comparison window

Default: compare the current period against the **trailing two prior periods**,
shown together as a 3-point comparison (e.g. an August report shows Aug/Jul/Jun).
Override this only if the user's request explicitly asks for something else (a
specific different period, a year-over-year comparison, "just last month"). Full
rules and the reasoning are in `references/report-spec.md`.

### Yearly reports

Yearly reports are the messy case, because the source data rarely arrives complete.
Expect any mix of: 12 monthly raw exports, a handful of staggered months, prior
monthly PDF reports this skill produced earlier, or a single annual export. Handle
what's actually there:

- **Build a month-by-month inventory first**, before computing anything. For each
  month in the year, record whether it's present and what its source was (raw export
  vs. extracted from a prior PDF). Show this inventory to the user and confirm it
  matches their expectation before proceeding — it's much cheaper to catch a missing
  or misattributed month here than after the report is rendered.
- **Mark every absent month "Unavailable"** in tables and leave a visible gap in trend
  charts. Never interpolate across a gap or quietly compress the axis to hide it: a
  chart that silently connects March to July implies six months of smooth data that
  doesn't exist.
- **Don't compute annual totals from a partial year** without labeling them as such.
  A "2026 total" built from seven months is a seven-month total; call it that, and
  state which months it covers.
- **Figures extracted from a prior PDF report carry that report's caveats.** If March
  was reported with a metric marked Unavailable, it's still Unavailable in the yearly
  rollup — don't let a number's absence get lost when it's re-aggregated.
- **Per-day normalization matters more here, not less**, since a 12-month span mixes
  28-, 30-, and 31-day months. Year-over-year and month-to-month comparisons within
  the rollup should lead with per-day rates.

## Step 4 — Compute the metrics

Use the formulas in `references/report-spec.md` (engagement rate, CTR, per-day rate,
share of total, share of change, etc.). Two rules matter enough to repeat here:

- **Day-count normalization.** Months run 28–31 days, and most of these metrics come
  from daily data summed into a monthly total. Always compute and show the **per-day
  rate alongside the raw total** for daily-granularity metrics, and base any trend
  judgment or recommendation on the per-day rate whenever the compared periods have
  different day counts — a 31-day month will out-total a 28-day month even at an
  identical daily pace, and that's a calendar artifact, not a performance signal.
- **Small-base suppression.** If a prior-period value is under ~50, don't show a
  percentage change (a jump from 2 to 6 is "+200%" and is noise) — show a dash and
  state the raw values instead.

Skip ROI/cost-per-X metrics entirely unless ad spend data is actually present in what
was supplied. Don't ask for it and don't compute it from an assumed number.

## Step 5 — Apply benchmarks

Look up the platform's default benchmarks in `references/benchmarks.md`. If the user
supplies their own benchmark figures (an internal target, a specific report they want
used), use those instead and note the substitution in the glossary. Always cite the
benchmark's source and date in the report — these figures vary enormously by
methodology and go stale within a year.

## Step 6 — Assemble the report data

Build a single JSON object matching the schema documented at the top of
`scripts/generate_report.py` (meta, kpis, performance_table, segment_table, charts,
findings, analysis_paragraphs, recommendations, glossary). A few things that make the
output good rather than just correct:

- Every finding, analysis paragraph, and recommendation should read like a specific
  claim about this account's data, not a generic template sentence — cite the actual
  numbers.
- Any claim that references a table or chart should use `[[link text|ref_id]]`
  markup so it renders as an actual clickable jump-to link in the PDF, not just a
  text label like "(see Section 2)".
- Recommendations should be prioritized, each tied explicitly to the finding behind
  it, and should account for day-count differences when that's relevant to the
  reasoning (e.g. don't recommend a September target based on August's raw total
  without adjusting for the day-count difference).
- Pick 3–6 charts from the library in `references/report-spec.md` based on what the
  data actually supports — don't force all chart types into every report.

## Step 7 — Render

Run:
```
python3 scripts/generate_report.py <data.json> <output.pdf>
```
This is the only way reports get built. If the template itself needs a visual change
(not this report's data, but the actual look), edit `generate_report.py` directly —
don't work around it by generating a differently-styled PDF for one report.

## Step 8 — Verify before delivering

A PDF that renders without an error can still be wrong in ways the script can't
catch, so inspect the output rather than assuming success. Convert a few pages to
images and look at them:

```python
from pdf2image import convert_from_path
pages = convert_from_path("report.pdf", dpi=120)
for i, p in enumerate(pages):
    p.save(f"page_{i+1}.png")
```

Check for the failure modes that actually happen: a table running off the page edge,
a chart with unreadable or overlapping labels, a heading stranded at the bottom of a
page away from its chart, an "Unavailable" that should have been a real number (or a
number that should have been Unavailable), and totals that don't reconcile against
the source export. Fix and re-render before handing it over — the user seeing a
broken chart costs far more trust than the extra minute of checking.

Two checks worth running programmatically rather than by eye:

- **Axis labels on rate charts.** Percentages like CTR sit between 4 and 6, so a
  formatter tuned for view counts can collapse every tick to the same label. Confirm
  ticks on any percentage axis show distinct values.
- **Internal links resolve.** A link that renders blue but points nowhere looks fine
  in an image. Walk the PDF's link annotations and confirm each destination maps to a
  real page.

Name the output `<account>_<platform>_<period>_report.pdf` (e.g.
`northbridge_facebook_2026-08_report.pdf`) and present it to the user.

## Edge cases

- **Ambiguous or missing platform/period in the request** — ask; don't guess and
  build the wrong report.
- **Export columns that don't match any known alias** — ask if it's a metric central
  to the report; note it and move on if it's incidental.
- **Multiple files covering the same period** — reconcile and disclose, don't just
  pick one and ignore the rest.
- **Gaps in a yearly rollup** — mark unavailable, never interpolate or estimate.
- **Currency changes between periods** — flag it explicitly rather than silently
  converting or mixing currencies in one table.
- **No ad spend data present** — skip ROI/cost-per metrics silently; this isn't a
  gap to apologize for, it's the expected case per how this skill was scoped.

## Maintaining this skill

`references/export-schemas.md` is a living document — the first time a real export
doesn't match what's documented there, update the aliases rather than special-casing
the mismatch inline in this file. That keeps the parsing logic generalizable instead
of overfit to one export you happened to see once.

Each platform renders in its own brand color (`PLATFORM_THEMES` in
`generate_report.py`) rather than one generic color for every report — that's what
makes five reports on a desk visually sortable by platform at a glance. Adding a
fifth platform means adding a theme entry there (a dark tone for headers/KPI cards
plus a bright accent for chart lines); anything not in the dict falls back to
`DEFAULT_THEME` rather than failing.

`evals/evals.json` holds the test prompts this skill was validated against, and
`evals/fixtures/` holds synthetic exports to run them with. Whenever
`generate_report.py` changes, re-run at least one fixture through the full pipeline
and inspect the rendered pages before trusting the template on a real report — a
template bug silently affects every future report, not just the one in front of you.
