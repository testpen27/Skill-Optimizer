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
| Reading each paper: verbatim quotes per column, the cells written from them, and the exhaustive `abstract_claims` and `caveats` lists (`reading-and-writing.md`) | Helpers, `haiku`, 3 papers each, in parallel; helpers write `helper_out/<id>.json` | medium | The bulk of the tokens at the lowest price. Measured: $0.026 per paper (20,000-token papers); in a test on four papers its cells had no added, strengthened or wrong claims. Quotes and numbers are machine-checked against the saved text |
| Pairing overclaims: each abstract claim matched to a body quote that shows the paper reports less or something different, and the cell sentence to colour (`overclaim-pairing.md`) | Helpers, `sonnet`, 3 papers each; they see only the quotes and the cells, never the paper; helpers write `pairing_out/<id>.json` | high | Judgment on short input. Measured: $0.045 per paper. Found all 5 real overclaims in the four-paper test, against 2 clean matches when Haiku paired them itself |
| Placing the flags and checking their quotes | Script `apply_overclaims.py` | — | A pair whose quote is not in the paper is dropped |
| Verifying every drafted cell and every overclaim pair against the quotes (the ABC check) | Helper, `opus`, about 10 papers each | high | Entailment judgment (hedges, scope, causal wording, added detail) is subtle. A different model from the drafter does not share its blind spots. Input is short (quotes + cells), so it stays cheap. It also removes doubtful overclaim flags |
| Optional strict mode: a second Opus helper argues with the first verifier's verdicts, or only the "keep" verdicts on sentences with statistics or sweeping words ("all", "every", "only", "across") | Helper, `opus` | high | Caught one real error the first verifier missed (a sub-result stretched to a whole), at +$0.115 per paper. Off by default; offer it for a thesis chapter or when the user asks for the strictest check |
| Synthesis paragraph; proposing themes (synthesis matrix) or concepts (concept matrix) | Helper, `opus` | high | Cross-paper judgment; short output; where quality shows most |
| Synthesis-matrix cells and concept-matrix marks | Helpers, `sonnet`, 3 papers each | high | Same reading discipline: every cell or X carries a quote |
| Verifying synthesis cells / concept marks | Helper, `opus` | high | Same ABC check as the LRM |
| Looking at the built workbook, final report to the user | Session | — | The session owns what the user sees |

Relative price per million tokens (input/output, Anthropic list prices noted
2026-11): Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20,
Fable 5.2 $8/$40. Reading is the bulk of the tokens, which is why it runs on
Haiku; matching, verification and synthesis are short, which is why Sonnet and
Opus are affordable there. No step uses Fable by default: Opus at high effort is enough for a
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
- the exact shape of the output: for readers, one JSON file per paper in
  `helper_out/<id>.json` (with `evidence`, the drafted cells, `overclaims`,
  `type` and `source_basis`), and a one-line status as the reply; for
  verifiers, one verdict per sentence, written to a file the same way.

Never pass a reader's draft to the verifier together with the reader's
reasoning; pass only the quotes and the cells, so the check is independent.
Run independent batches in parallel. When a helper fails or returns nothing,
retry once on the same model, then do that batch in the session and say so.

## When reading helpers are worth it

"Just the model" and "a helper with a model set" are different things. If the
user sets their chat to Haiku, everything runs on Haiku: the conversation, the
reading, and the checking by the same model. A helper is a separate agent the
chat starts for one job, with its own model, its own clean workspace and no
effect on the chat's model or context: a chat on Sonnet, Opus or Fable can
start a Haiku helper to read, so the reading is cheap and the conversation and
coordination stay on a stronger model, and the paper text never fills the chat.

Cost of the reading-and-pairing pipeline above against the chat reading the
papers itself (20,000-token papers; Opus verification and synthesis in both;
start-up of each helper billed in full, the cautious case; measured runs and a
model calibrated to them, `scripts/helper_cost_model.py`):

| Papers | Chat on Sonnet reads | Haiku and Sonnet helpers | Saving |
|---|---|---|---|
| 1 | $0.60 | $0.59 | none (a tie) |
| 2 | $0.79 | $0.68 | 14 percent |
| 4 | $1.20 | $0.96 | 20 percent |
| 8 | $2.06 | $1.43 | 31 percent |
| 20 | $5.31 | $3.06 | 42 percent |

A chat on Opus or Fable saves more (a chat on Opus reading 8 papers costs
$3.50). So:

| Papers | What runs |
|---|---|
| 1 | The chat reads the paper itself and checks the overclaims in the same pass (a tie on cost, and two helper waits are avoided). The `opus` verification still runs as a helper |
| 2 or more | Reading helpers on `haiku`, pairing helpers on `sonnet`, then the `opus` verification helper (and synthesis) |

Verification never depends on the paper count: it always runs separately from
the reader, as a helper where there are helpers and as a separate pass where
there are none. A chat set to Haiku is cheapest in raw dollars up to about 9
papers (its context grows past 100,000 tokens, where Haiku's price rises
fivefold), but then Haiku also runs the whole conversation and follows this
skill's instructions, which has not been tested; recommend Sonnet or Opus for
the chat. Whichever the chat runs on, helpers start-up is cheaper when several
run in one session (the shared start-up is cached), so the table is the
cautious case.

Helpers write their output themselves: each reading helper saves one JSON file
per paper into `helper_out/` and returns only a one-line status. The session
merges them with `python3 scripts/merge_papers.py lrm.json --from helper_out/`
and never re-types a helper's cells (that costs output tokens and is a chance
to change a word).

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
