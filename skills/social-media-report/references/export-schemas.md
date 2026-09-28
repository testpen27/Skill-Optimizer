# Expected Export Schemas (Best-Effort Defaults)

These schemas are built from each platform's standard, publicly documented export
format. **They have not yet been validated against a real export file from this user.**
The first time a real file doesn't match, update this document rather than special-casing
it inline in SKILL.md — that keeps the parsing logic generalizable instead of overfit to
one export.

General approach: read the file, match columns against the aliases below (case-insensitive,
ignore punctuation/whitespace differences), and if a column can't be confidently matched,
ask the user what it represents rather than guessing. Never silently drop a column that
doesn't match — surface it.

## Facebook (Meta Business Suite Page exports)

Typically arrives as multiple files for the same period, not one:

| Canonical field | Common column names / aliases |
|---|---|
| Date | `Date`, `Day` |
| Views | `Views`, `Post Views`, `Page Views` |
| Unique viewers | `Viewers`, `Unique Viewers`, `Reach` |
| Interactions | `Interactions`, `Engagements`, `Post Engagements`, `Reactions, Comments and Shares` |
| Gross follows | `Follows`, `New Follows`, `Page Likes` |
| Unfollows | `Unfollows`, `Page Unlikes` |
| Visits | `Visits`, `Page Visits` |
| Link clicks | `Link Clicks` |
| Impressions | `Impressions` |

Separate files to expect: a **Top content formats** breakdown (by Photo/Video/Reel/Text/
Story/Live), and a **monetization/earnings** file (revenue by segment, in-stream ads,
Stars, bonus payments). Treat these as separate inputs to reconcile against the daily
totals, not as the primary source.

## Instagram (Meta Business Suite / Instagram Insights)

| Canonical field | Common column names / aliases |
|---|---|
| Date | `Date`, `Day` |
| Reach | `Reach`, `Accounts Reached` |
| Impressions | `Impressions` |
| Profile visits | `Profile Visits` |
| Follows | `Follows`, `Followers`, `Follows and Unfollows` |
| Interactions | `Interactions`, `Engagement`, `Likes + Comments + Shares + Saves` |

Segment breakdowns typically arrive by content type: Feed post, Reel, Story, Carousel.

## TikTok (TikTok Analytics export)

| Canonical field | Common column names / aliases |
|---|---|
| Date | `Date` |
| Video views | `Video Views`, `Views`, `Vid Plays` |
| Profile views | `Profile Views` |
| Likes | `Likes`, `Hearts` |
| Comments | `Comments` |
| Shares | `Shares` |
| Reposts | `Reposts`, `Repost Count` — a distinct feature from Shares (a repost appears on the reposter's own profile; a share doesn't), not an alias for it |
| Gross follows | `Follows`, `New Follows`, `Gross Follows` |
| Net followers | `Net Followers`, `Follower Growth` |
| Average watch time | `Average Watch Time`, `Avg. Watch Time` |
| Completion rate | `Video Completion Rate`, `Completion Rate`, `Avg Watch %` |

**Reposts vs. Shares — confirmed distinct, not just a naming difference.** When an
export includes both, include Reposts in the interactions total alongside Likes,
Comments, and Shares, and disclose the composition in the data notes (e.g.
"Interactions = Likes + Comments + Shares + Reposts") so a reader comparing this
report's engagement rate against another month or another account knows what's
folded in. When only Reposts is present with no separate Shares column, don't
assume the account simply doesn't have shares — ask, the way this case was
resolved, rather than reporting a zero that might just be an unexported field.

**Gross vs. net follows.** A column named "New Follows" or "Follows" without a
paired unfollows figure is almost always a gross count, matching how Facebook and
Instagram export the same concept (see above) — don't assume it's already net of
unfollows unless the export or its documentation says so explicitly.

## YouTube (YouTube Studio "Advanced mode" export)

| Canonical field | Common column names / aliases |
|---|---|
| Date | `Date` |
| Views | `Views` |
| Watch time (hours) | `Watch time (hours)` |
| Average view duration | `Average view duration` |
| Impressions | `Impressions` |
| Impressions CTR | `Impressions click-through rate (%)`, `Impressions CTR` |
| Subscribers gained/lost | `Subscribers gained`, `Subscribers lost` |
| Likes / Comments / Shares | `Likes`, `Comments`, `Shares` |
| Estimated revenue | `Estimated revenue (USD)` (only present on monetized channels) |

## When a file doesn't match any of the above

This will happen — export formats change, users export from different report views,
or a platform updates its dashboard. When it does:
1. Try the alias match first.
2. **Use domain judgment before asking.** An unfamiliar column name isn't
   automatically a reason to stop and ask — "Vid Plays" for video views or "Hearts"
   for likes are confident inferences a competent analyst would make without
   checking. Reserve questions for cases where two different canonical fields are
   both plausible, or where guessing wrong would misrepresent a genuinely distinct
   feature rather than just use an unfamiliar name for the same one (see the
   Reposts-vs-Shares note under TikTok above — that's a "which feature is this"
   question, not a "what do you call this" one). Asking about every renamed column
   indiscriminately is its own failure mode: it trains the person to ignore your
   questions.
3. If a genuinely ambiguous case involves a metric central to the report (views,
   interactions, revenue), ask which column it corresponds to rather than guessing.
4. If it's a minor/incidental column that doesn't map to anything this skill
   computes, note it as "not used in this report" rather than silently ignoring it —
   the person should know their data wasn't lost, just unused.
5. Once resolved, add the new alias to this file so it's recognized next time.
