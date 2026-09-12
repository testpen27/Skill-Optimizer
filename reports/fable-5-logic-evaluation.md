# Evaluation: `fable-5-logic`

Run with the `skill-creator` description optimizer on 2026-09-11/12.
Model under test: `claude-opus-5`. Eval sets in `evals/`, harness fixes in `scripts/`.

## Headline

The skill never triggers. Across 60 measured runs (20 queries x 3), on a probe
validated against a known-good control, it was invoked **zero times** — and
four differently-worded descriptions produced the same zero.

That is not a wording problem, and no amount of description optimization will
fix it. It is a delivery-mechanism mismatch: skills are *pull*-based (the model
decides it needs one and reaches for it), and this skill asks to be *pushed*
into every response. Those are different mechanisms.

## What was measured

Two eval sets over the same 20 realistic queries, differing only in labels:

| Set | Labels | Question it asks |
|---|---|---|
| `trigger-eval-mixed.json` | 13 should-trigger / 7 near-miss negatives | Does it fire where it matters and stay out of mechanical work? |
| `trigger-eval-alwayson.json` | all 20 should-trigger | Taking "load on every response" at face value, does it? |

Positives span the contexts the description names: factual claims needing a
citation, version/upgrade calls, pushback on a risky decision, questions about
Claude's own model and cutoff, grief, small talk, brainstorming, "be honest",
judgments about a person, a contested position, a wrong premise. Negatives are
near-misses — mechanical file, code, and data work where the deliverable is an
artifact rather than an assertion.

### Result (mixed set, corrected probe, iteration 1)

```
Train: 15/39 correct   precision=100%  recall=0%   accuracy=38%
Test :  6/21 correct   precision=100%  recall=0%   accuracy=29%
```

Every positive scored 0/3. Every negative scored 0/3 — they "pass" only because
the skill fires for nothing at all. Precision of 100% is an artifact of never
firing, not a sign of good targeting.

The always-on set is the same runs relabeled: 0/60, accuracy 0%.

## Why the number is trustworthy (and where it isn't)

The first three attempts produced the same 0% through a **broken harness**, so
the result needed a control before it could be believed. Two upstream bugs, both
of which report a healthy skill as 0%:

1. **The skill under test was registered as a slash command**, in
   `.claude/commands/`. A command never reaches the `available_skills` list the
   model actually picks from, so there was nothing to invoke.
2. **The detector accepted the skill only as the very first tool call** of the
   turn. Any other tool first — a `Bash ls` to find the file the user
   mentioned — and it returned "did not trigger" immediately. In a real session
   Claude routinely looks around first and invokes the skill a beat later.

Control, an `xlsx`-style description against spreadsheet queries:

| Probe | Control result |
|---|---|
| upstream | 0/2 queries triggered — a description known to work scored zero |
| corrected (`scripts/trigger_probe.py`) | 1/2 queries triggered |

So the corrected probe can detect a trigger, and `fable-5-logic` still scores
zero on it.

**Caveat.** The run ended when the org hit its monthly spend limit, and a
refused subprocess is indistinguishable from a non-trigger. Iteration 1 is
almost certainly clean — its 60 runs took 366s (~48s per wave of 8, the pace of
real turns), where the first post-limit iteration collapsed to 64s of instant
failures. The 0% is also corroborated by three independent runs and has a
mechanistic explanation. Still, treat the per-query rates as one clean
iteration, not a repeated measurement.

## Why it does not trigger

Claude consults a skill when it has a task it cannot readily do alone — produce
a .docx, parse a PDF, follow an unfamiliar deploy procedure. A tone-and-epistemics
overlay is not that. Asked "should we jump to node 22", Claude simply answers;
there is no moment where it stops and thinks "I need a skill for this". The
skill's own framing makes this worse: "load this on every response" is a
statement about frequency, not a description of a task, so the classifier gets
nothing to discriminate on.

## The other finding: "costs nothing on light messages" is not true

The body is ~2,200 words and loads in full whenever the skill triggers. The
stakes-gating inside gates *behavior*, not *loading* — a "hey, just shipped my
app" message that triggered this skill would still pull in the whole citation,
staleness, and hard-conversation apparatus. Progressive disclosure is the fix:
keep the always-relevant register rules in the body and move the stakes-gated
rigor into `references/`.

## Other observations on the file

- The prose is genuinely good and follows skill-writing guidance well — it
  explains *why* rather than piling on capitalized MUSTs.
- The description is 134 words and reads as a manifesto. Even setting the
  mechanism aside, it spends its length on what the skill believes rather than
  on when to use it.
- The body hardcodes "Reliable knowledge ends around mid-2026". That is a
  remembered fact stated as current, which is the exact failure the skill spends
  a section warning against, and it goes stale on its own.
- The name encodes a model (`fable-5`) while the content is model-agnostic, and
  the description never mentions it — so the name helps neither triggering nor
  the reader.

## Recommendations

**1. Change the delivery mechanism.** This content belongs where it applies
unconditionally, not behind a trigger decision: `CLAUDE.md` for a repo, an
output style, or `--append-system-prompt` for API and harness use. That gets
100% of what the skill is asking for, which no description can.

**2. If it stays a skill, rewrite the description as a trigger condition.** The
optimizer's strongest proposal, kept for reference:

> Use this whenever you are answering a person rather than mechanically
> executing a task — any reply where wording, confidence level, or the honesty
> of a claim is part of the deliverable. Load it before responding to: facts,
> statistics, citations, sources, laws, or specs the user will quote or act on;
> version numbers, release dates, and "should we upgrade / switch approach"
> judgment calls; questions about Claude itself (model, context window, cutoff,
> limits); judgments about a specific person from thin evidence — a hiring call,
> a profile, someone's motives; emotionally heavy or personal messages, grief,
> hard news; casual sharing, small talk, wins; opinions, contested positions, or
> pushback on a plan. Skip it for purely mechanical execution — editing files,
> running commands, writing a function, converting or extracting data — where no
> claim about the world is being made.

This is untested: it was proposed from iteration 1's failures and the spend
limit stopped the run before it could be scored. Expect it to beat 0% on
judgment-heavy queries and still miss the trivial ones, because "answer the
person" messages rarely feel to the model like they need a skill.

**3. Split the body** into an always-relevant register section and a
`references/rigor.md` for the stakes-gated epistemics, so triggering does not
cost 2,200 words every time.

**4. Drop the hardcoded cutoff date** from the body, or phrase it as "check the
current date against your own cutoff" rather than naming a month.

## Reproducing

```bash
export SKILL_CREATOR=<path to skill-creator>
python3 scripts/run_loop_resilient.py \
  --eval-set evals/trigger-eval-mixed.json \
  --skill-path skills/fable-5-logic \
  --model claude-opus-5 --max-iterations 5 --runs-per-query 3 \
  --num-workers 8 --timeout 90 --holdout 0.4 --verbose \
  --report /tmp/report.html --results-dir /tmp/results
```

`scripts/run_loop_resilient.py` wraps the upstream loop with the corrected probe
plus retry on the proposal call, which otherwise aborts the whole run — and
throws away every eval result in it — on a single transient failure.
