# Report Content Specification

This defines what goes in every report and the rules for computing it. The visual
template (fonts, colors, layout) is locked in `scripts/generate_report.py` and is not
something to redesign per report — only the data going into it changes.

## Comparison window (default, overridable)

Default: show the current period against the **trailing two prior periods** as a
3-point comparison (e.g. an August report shows August, July, and June side by side),
not just a single prior-period comparison. Use this default unless the user explicitly
asks for something else in their request (e.g. "compare to last year" or "just show
month-over-month").

For yearly reports, show the full span of months available, explicitly marking any
month that wasn't supplied as unavailable in the trend rather than skipping it silently
or interpolating a value. A trend line or bar chart with a gap is honest; a smoothed
line across missing months is not.

## Day-count normalization

Months are not the same length (28–31 days), and most of these metrics are daily
exports summed into a monthly total. A 31-day month will show higher raw totals than
a 28-day month even at an identical daily rate — that's an artifact of the calendar,
not a real change in performance.

Rule: for every metric that comes from daily-granularity data, compute and display
**both** the raw period total and the per-day average (metric ÷ days in period).
When judging whether a metric is trending up or down, or when writing a recommendation
based on a comparison, base the judgment on the **per-day rate**, not the raw total,
whenever the compared periods have different day counts. State this explicitly when it
changes the conclusion (e.g. "raw views were flat, but June's 30 days vs. August's 31
means the per-day rate actually fell").

## Change markers

Show change as a colored arrow next to the value it describes (▲ green for an
increase, ▼ red for a decrease), not as a separate table column. A reader scanning
a row should see the number and its direction in one glance rather than tracking
across to a different column to find out whether "12,401,581" was good or bad.

This applies to the primary value in each performance-table row and to every KPI
card. It does not apply to the comparison-only columns (last month, two months
back) — those are reference points being compared *against*, not the thing being
judged, so they stay plain numbers. `scripts/generate_report.py` renders the
marker automatically from a `change_pct` or `change_pt` value attached to the
cell or KPI; don't pre-format the arrow into the text yourself; feed the number
and let the template draw it, the same way color and font are handled everywhere
else in this skill.

A missing marker (dash, no color) still needs to mean something specific: either
there's genuinely no prior-period value to compare against, or the small-base
suppression rule below applies. Don't omit the marker just because the change is
small — a ▲ +0.8% is still informative.

## Small-base suppression

If the prior period's value for a metric is under 50 (count) or the underlying base is
otherwise too small to produce a stable percentage (e.g. a monetization line that was
$0 one month), do not show a percentage change — show a dash and state the raw values
instead. A percentage swing from 2 to 6 is "+200%" and is meaningless noise.

## Missing/unavailable data

If an expected metric isn't present in the supplied export(s) for a period, mark it
"Unavailable" in every table where it would otherwise appear — never estimate it,
interpolate it, or omit the row silently. State in a data notes section which exports
were and weren't supplied, matching the level of transparency in the reference report
this skill was modeled on.

## Report structure (in order)

1. **Header block** — account name, platform, reporting period, comparison period(s),
   data source(s) supplied, currency, date prepared. One compact info box, not a
   multi-page front matter.
2. **Executive summary** — a short lead paragraph, then 3–5 KPI cards (period total +
   per-day rate + change vs. comparison window), then 3–5 bullet key findings, each
   citing the section/exhibit it comes from.
3. **Performance table** — full metric-by-metric comparison table across the period and
   its comparison window, with per-day rates shown alongside raw totals. Show the
   direction and size of change as an inline colored marker (▲ green / ▼ red) on
   the value itself, not as a separate "Change vs X" column — see Change markers
   below.
4. **Segment/content-type breakdown** — if the export supports it (e.g. Facebook's
   Photo/Reel/Text/Story/Live, Instagram's Feed/Reel/Story/Carousel), a table showing
   each segment's share of views/interactions/revenue and how that share is shifting.
5. **Visual analysis** — 3–6 charts (see Chart Library below), each with a one-line
   takeaway underneath, not just a caption. Every chart references the table it draws
   from and is clickable back to it.
6. **Analysis** — narrative explanation of what's driving the biggest changes,
   including an attribution breakdown (which segment/component contributed how much of
   the total change, ranked). Every claim in this section links back to the table or
   exhibit that supports it.
7. **Recommendations** — 3–6 actions, each in priority order, each explicitly citing the
   finding that motivates it, each accounting for day-count differences if relevant to
   the recommendation's reasoning.
8. **Glossary** — metric definitions, the formulas used for every derived measure,
   the benchmark sources and dates used, and any data notes (what was supplied, what
   wasn't, any reconciliation checks performed). Always the last page(s).

## Chart library

Pick from these based on what the data supports — not every report needs all of them:

- **Trend chart** (line or bar): the primary metric (views, revenue) across the
  comparison window, per-day rate as a second line if raw and per-day tell different
  stories.
- **Composition chart** (stacked bar or 100% stacked bar): share of views/interactions/
  revenue by segment, across the comparison window.
- **Attribution waterfall**: change in a headline metric (usually revenue) broken down
  by which segment/component drove how much of it.
- **Benchmark comparison** (bar): this account's rate vs. the built-in or user-supplied
  benchmark, for engagement rate / CTR.
- **Distribution** (bar or scatter): daily values across the period, useful for
  identifying single-day spikes that explain a monthly total.

## Derived measure formulas

| Measure | Formula |
|---|---|
| Engagement rate (%) | interactions ÷ views (or ÷ followers, ÷ reach — state which) × 100 |
| CTR (%) | link clicks (or impressions-CTR) ÷ impressions × 100 |
| Per-day rate | period total ÷ days in period |
| Share of period total (%) | segment value ÷ period total for that metric × 100 |
| Share of change (%) | component's change ÷ total change × 100 |
| Change vs. comparison period (%) | (current − prior) ÷ prior × 100, suppressed if prior < 50 |
| Change, already-percentage metrics | current − prior, stated in percentage points (pt), never as a % of a % |

## Internal cross-references

Every claim in the Analysis and Recommendations sections should link back to its
source table or exhibit as a clickable in-PDF link (not just a text label like
"(Section 2.3)" — an actual jump-to link). `scripts/generate_report.py` implements
this via named PDF bookmarks; when assembling report data, give each table/exhibit a
short stable id (e.g. `perf-table`, `exhibit-3`) and reference that id wherever the
content links to it.

## Chart selection notes (learned from test runs)

- **Single-period composition.** When segment data exists for only one period, a
  one-column stacked bar is still valid but conveys less than the segment table
  beside it. Prefer it only when the share split is the point being made; otherwise
  the table alone is enough.
- **Two measures on different scales.** When plotting views against impressions or
  revenue against a rate, scale one series and say so explicitly in both the chart
  label and the data notes (e.g. "Impressions/day (÷20)"). An unlabelled scaled axis
  invites the reader to compare magnitudes that aren't comparable.
- **Rate charts need decimal axes.** CTR and engagement rate live between roughly 0.1
  and 6. A number formatter tuned for view counts rounds all of those to the same
  integer and produces an axis reading "5, 5, 5, 4, 4". `_fmt_value` in
  `generate_report.py` handles this; don't replace it with a plain integer format.
- **Trend charts with gaps.** Pass `missing_labels` alongside `None` values so absent
  periods are shaded and annotated. `None` alone breaks the line correctly but leaves
  the reader unable to distinguish "no data" from "zero".
- **Platform brand color is not a sentiment color.** Each platform's chart lines and
  bars use its brand accent (`PLATFORM_THEMES` in `generate_report.py`) regardless of
  whether the trend they're drawing is good or bad news — a YouTube chart is red
  whether the metric is rising or falling. Only the small ▲/▼ change markers next to
  numbers carry positive/negative meaning. Don't "fix" a rising line that happens to
  render in red; that's the brand color working correctly, not a sentiment bug.
