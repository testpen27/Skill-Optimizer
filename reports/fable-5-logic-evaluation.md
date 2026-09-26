# Evaluation: `fable-5-logic`

Optimized and validated with the `skill-creator` description optimizer against
`claude-opus-5`. Eval sets in `evals/`, corrected harness in `scripts/`, raw
numbers in `results/`.

## Result

The rewritten description is better on both axes. 10 runs per query, zero
unusable runs, corrected detector.

| Query | Should fire? | Original | Rewritten |
|---|---|---|---|
| grant statistic needing a citation | yes | 10/10 | 10/10 |
| risky foreign-key shortcut | yes | 6/10 | **10/10** |
| grief, hard personal news | yes | 5/10 | **10/10** |
| rename a variable across `src/` | no | 2/10 | **0/10** |
| build a bar chart | no | 7/10 | **0/10** |
| add a ruff pre-commit hook | no | 0/10 | 3/10 |

| | Original | Rewritten |
|---|---|---|
| **Recall** | 21/30 (70%) | **30/30 (100%)** |
| **False fires** | 9/30 (30%) | **3/30 (10%)** |

The original's weakest spot was the one that mattered most: 5/10 on the grief
message, where the skill's wording guidance is the whole point. That is now
10/10. It also fired on 7/10 chart requests, which is pure context cost; that is
now 0/10. The one regression is the pre-commit hook query, 0/10 to 3/10.

## What changed in the skill

- **Description rewritten** to promise its contents — the verification
  checklist, the calibration ladder, the answer-shape patterns — and to name
  concrete trigger conditions, with an explicit carve-out for mechanical
  execution. The numbers above are for this description.
- **Progressive disclosure.** The body was ~2,200 words loading in full on every
  trigger. The stakes-gated epistemics moved to `references/rigor.md`; SKILL.md
  keeps the register rules that always apply. The old claim that the skill
  "costs nothing on light messages" was false — the gating governed behavior,
  not loading — and is gone.
- **Removed the hardcoded cutoff.** The body asserted "reliable knowledge ends
  around mid-2026," a remembered fact stated as current, which is the exact
  failure the skill spends a section warning against. It now says to check the
  current date against your own cutoff.

## Why the measurement took five tries

Every bug below produced plausible numbers rather than visible errors, which is
why each one survived until something contradicted it. Worth reading before
trusting this harness or the upstream one.

1. **Skill registered as a slash command** in `.claude/commands/`. Commands
   never reach the `available_skills` list the model picks from, so nothing was
   invocable. Everything scored 0%.
2. **Only the first tool call counted.** Claude routinely looks around first — a
   `Bash ls` to find the file named — and invokes the skill a beat later. Those
   were scored as misses.
3. **Concurrent runs shared one `.claude/skills/`.** With N workers each turn saw
   N near-identical copies and often invoked a sibling's, whose name did not
   match the one being watched. Parallel passes read 0/3 where serial read 2/2.
4. **Crashed runs scored as "did not trigger."** A throttled pass returned
   all-zero in 29s where a real one takes ~20 minutes, and the weak validity
   check ("did any assistant message appear?") passed it. A run is now valid
   only if it ends in a `result` event with subtype success, `is_error` false and
   a nonzero cost — otherwise it raises `ProbeFailure` and is excluded. Zeros are
   the failure mode that looks like data, so they must be the hardest outcome to
   record by accident.
5. **Matching the name anywhere in the transcript inflated results.** The init
   event lists every available skill, so the name is present whether or not it
   was used, and any `Skill` call at all scored as a hit. On the chart query the
   model invoked `dataviz` in 5 of 5 runs while the probe recorded 5/5 for
   `fable-5-logic`. The name is now matched only inside a `Skill`/`Read` tool
   input, verified against captured transcripts of known-good runs.

Two further lessons about method, not code:

- **Run a control first.** Bugs 1 and 2 were caught only by pointing the harness
  at an `xlsx`-style description that should obviously fire and seeing it score
  0/2. That control should have run before the first number was reported.
- **Three runs per query is under-powered.** On borderline queries triggering is
  near a coin flip; n=3 lands 2/2 one way and 0/2 the other by chance. Ten runs
  per query is the minimum that separated signal from noise, about 20 minutes
  per description on this box.

Throttling is episodic and unrelated to concurrency (4/4 real turns at 1, 2 and
4 workers once a window clears). Two negative cells were 10/10 unusable in one
pass and clean on re-run.

## Remaining

- The pre-commit regression (0/10 to 3/10) is the one place the rewrite is
  worse, and the likeliest thing to tighten in the "skip it for mechanical
  execution" clause.
- Absolute false-fire rates are probably pessimistic: the probe registers one
  skill in a bare project, where a real session has many competing. The
  comparison between descriptions holds because both were measured identically.
- Only six queries were measured at full power, chosen to span the skill's
  claimed range. The 20-query sets in `evals/` are the natural next widening.

## Standing recommendation, unchanged

None of this removes the design argument: content meant to apply to *every*
response belongs where it is always in context — `CLAUDE.md`, an output style,
or `--append-system-prompt` — not behind a trigger decision. 100% recall on six
queries is not the same as always. As a skill, this is now about as well-targeted
as a skill can be; the mechanism is still pull-based by construction.

## Reproducing

```bash
export SKILL_CREATOR=<path to skill-creator>
python3 scripts/run_loop_resilient.py \
  --eval-set evals/trigger-eval-mixed.json \
  --skill-path skills/fable-5-logic \
  --model claude-opus-5 --runs-per-query 10 \
  --num-workers 4 --timeout 240 --verbose
```

`scripts/trigger_probe.py` carries the five fixes; `scripts/run_loop_resilient.py`
wires it into the upstream loop and retries the proposal call, which otherwise
aborts a whole run on one transient failure.
