# Model routing

Each step runs on a planned model. Steps marked **helper** go to a subagent
through the `Agent` tool with the `model` (and, where the harness accepts it,
`effort`) set as below. The session, on whatever model the user chose,
coordinates, talks to the user, runs the scripts and checks every helper's
output before anything is saved or shown as final.

The rule behind the plan: **scripts do everything that has one right answer**
(citations, quartiles, retractions, quote matching, counts, the workbook);
cheap models fetch; a careful model reads; **a different, stronger model checks
the reading**; the strongest judgment goes where one short answer spans many
papers.

## The plan

| Step | Runs on | Effort | Why this model |
|---|---|---|---|
| Intake, choosing the matrix, agreeing themes or concepts with the user | Session | — | A dialogue with the user |
| Fetching what the scripts cannot reach (full texts, Crossref records, Scimago pages) and saving it **unedited** to files | Helpers, `haiku`, about 10 items each, in parallel | low | Mechanical. The helper only saves; scripts parse, so a weak summary can never reach the matrix |
| Crossref check, retraction notices, Scimago quartile, quote and number checks, building the workbook | Scripts | — | Deterministic; no model |
| Reading each paper: collecting verbatim quotes per column, checking the abstract against the body, then drafting the cells from those quotes only (`reading-and-writing.md`) | Helpers, `sonnet`, 3 papers each, in parallel | high | Accuracy over long full texts at a fraction of Opus's cost. Quotes are machine-checked against the saved text |
| Verifying every drafted cell against its quotes (the ABC check) | Helper, `opus`, about 10 papers each | high | Entailment judgment (hedges, scope, causal wording, added detail) is subtle. A different model from the drafter does not share its blind spots. Input is short (quotes + cells), so it stays cheap |
| Synthesis paragraph; proposing themes (synthesis matrix) or concepts (concept matrix) | Helper, `opus` | high | Cross-paper judgment; short output; where quality shows most |
| Synthesis-matrix cells and concept-matrix marks | Helpers, `sonnet`, 3 papers each | high | Same reading discipline: every cell or X carries a quote |
| Verifying synthesis cells / concept marks | Helper, `opus` | high | Same ABC check as the LRM |
| Looking at the built workbook, final report to the user | Session | — | The session owns what the user sees |

Relative price per million tokens (input/output, Anthropic list prices noted
2026-11): Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20,
Fable 5.2 $8/$40. Reading is the bulk of the tokens, which is why it runs on
Sonnet; verification and synthesis are short, which is why Opus is affordable
there. No step uses Fable by default: Opus at high effort is enough for a
review matrix, and Fable costs twice as much.

## The plan is fixed

Follow the table on every run, so results stay consistent and costs
predictable. If the user asks to change a step's model or to stop using
helpers, say so briefly and carry on with the plan; the table changes by
editing this file, not during a run.

**The one exception is moving a step up, and only after asking.** Ask when a
helper's output is clearly not good enough and a stronger model is the likely
fix: a reader whose quotes keep failing `check_evidence.py`, a reader that
returns cells without the paper's numbers, a verifier that passes a cell the
script then flags. Say which step, what went wrong and which model you
propose (`haiku` to `sonnet`, `sonnet` to `opus`, or `opus` to `fable` for
synthesis only), and wait for a yes. Never move a step down, never switch
without asking.

## Handing work to a helper

A helper cannot see the conversation. Give it everything in its prompt:
- the user's field, title and the matrix being built;
- the exact input: file paths of the saved paper texts (never "the paper we
  discussed"), or the quotes and cells to verify;
- the rules for its step, copied from `reading-and-writing.md` (readers get
  "Reading" and "Writing"; verifiers get "Verifying");
- the exact shape to return: for readers, one JSON object per paper with
  `evidence` (quotes with locations, per column), the drafted cells, `type`
  and `source_basis`; for verifiers, one verdict per sentence.

Never pass a reader's draft to the verifier together with the reader's
reasoning; pass only the quotes and the cells, so the check is independent.
Run independent batches in parallel. When a helper fails or returns nothing,
retry once on the same model, then do that batch in the session and say so.

## Small jobs: 3 papers or fewer

Every helper has a fixed start-up cost: it must be handed its instructions,
the rules for its step and its files before it reads anything. With 3 papers
or fewer, read them in the session instead of starting reading helpers. Keep
the separate verification (an `opus` helper, or a separate pass where there
are no helpers), because the independent check is the point, not the cost.
From 4 papers up, use the reading helpers as in the table. The line at 3 is
an estimate, not a measurement; change it here if a measured run shows
otherwise.

## Check for helpers first, and tell the user if there are none

Before the first step, look at the tools this session has. Helpers need the
`Agent` tool (the tool that starts a subagent). If it is not there, or a first
helper call fails because helpers are unavailable, say this once, in one line,
before starting:

> This chat can't start helper agents, so every step runs on the model you
> picked for this chat, and the per-step models in this skill don't apply.
> The checks still run, as separate passes.

Then run every step in the session, in the same order: fetch and save,
collect quotes, draft, run `check_evidence.py`, then verify each cell against
its quotes as a **separate pass after all cells are drafted**, reading the
quotes again rather than recalling the paper.

Where helpers are known to work (Claude Code documentation, and tested in a
cloud session): Claude Code in a terminal, and Claude Code cloud sessions on
claude.ai/code, including one started or followed from the Claude mobile app.
The desktop app's Code area shows helpers too. For ordinary claude.ai chat (in
a browser or the mobile apps' chat) and for Cowork, the documentation does not
say, which is why the skill checks its tools instead of guessing from the app.
