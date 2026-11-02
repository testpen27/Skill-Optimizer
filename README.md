# Skill-Optimizer

Tooling for measuring and optimizing when a Claude skill triggers, built on
Anthropic's `skill-creator` description-optimization loop.

- `skill-creator/` -- the `skill-creator` skill, vendored unchanged (Apache 2.0,
  see its `LICENSE.txt`). Its `scripts/run_loop.py` is the optimization loop.
- `scripts/trigger_probe.py` -- a replacement for skill-creator's per-query
  trigger detector. The upstream one reports healthy skills as 0% and, once
  that is fixed, can inflate results instead; the module docstring lists the
  five bugs and the evidence for each.
- `scripts/run_loop_resilient.py` -- runs the upstream loop with the corrected
  probe, and retries the per-iteration proposal call, which otherwise aborts
  the whole run on one transient failure.

## Branch layout

`main` holds only the toolkit above. Each skill that gets created or
optimized with it lives on its own `skill/<name>` branch, which carries the
skill, its eval sets, results, reports and packaged build. See `CLAUDE.md`
for the rules. `scripts/check_branch.py` enforces them in CI on every push
and at the start of every Claude Code session. Run it before pushing:

```bash
python3 scripts/check_branch.py
```

## Running

```bash
python3 scripts/run_loop_resilient.py \
  --eval-set path/to/trigger-eval.json \
  --skill-path path/to/your-skill \
  --model <probe-model-id> --improve-model <rewrite-model-id> \
  --runs-per-query 10 --num-workers 4 --timeout 240 --verbose
```

`--model` and `--improve-model` point at two different jobs, and the right
model for one is usually wrong for the other:

- `--model` drives the trigger probe -- dozens of cheap `claude -p` calls
  that stand in for a real user's session. Set it to whatever model you
  actually ship behind the skill, or the trigger rate you measure isn't the
  one that will happen in production.
- `--improve-model` (optional) drives the per-iteration description
  rewrite -- a handful of calls per run where getting the wording right
  matters more than the cost. Point it at your strongest available model.
  Omit it to fall back to `--model` for both, matching upstream.

The eval set is a JSON list of `{"query": ..., "should_trigger": true|false}`.
Two things learned the hard way:

- **Run a control first.** Point the harness at a description that should
  obviously fire on its queries. If that scores zero, the harness is broken,
  not the skill.
- **Use 10 runs per query, not 3.** On borderline queries triggering is close
  to a coin flip, and three runs cannot tell signal from noise.

- **Keep older copies of the skill out of the runs.** Skills synced from the
  account are visible to every run, and an older version of the skill under
  test takes its triggers. Set `PROBE_SETTING_SOURCES=project` to drop
  user-level skills, and `PROBE_COMPETITORS=<dir>` to copy a chosen set of
  competing skill folders into each run instead.

A run that fails (spend limit, crash) is retried, then stops the pass; it is
never recorded as "did not trigger".

Needs the `claude` CLI on PATH, since each run is a real `claude -p` turn.
