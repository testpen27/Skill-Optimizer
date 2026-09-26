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
optimized with it lives on its own branch, which carries the skill, its
eval sets, results and reports. See `CLAUDE.md` for the rules.

## Running

```bash
python3 scripts/run_loop_resilient.py \
  --eval-set path/to/trigger-eval.json \
  --skill-path path/to/your-skill \
  --model <model-id> --runs-per-query 10 \
  --num-workers 4 --timeout 240 --verbose
```

The eval set is a JSON list of `{"query": ..., "should_trigger": true|false}`.
Two things learned the hard way:

- **Run a control first.** Point the harness at a description that should
  obviously fire on its queries. If that scores zero, the harness is broken,
  not the skill.
- **Use 10 runs per query, not 3.** On borderline queries triggering is close
  to a coin flip, and three runs cannot tell signal from noise.

Needs the `claude` CLI on PATH, since each run is a real `claude -p` turn.
