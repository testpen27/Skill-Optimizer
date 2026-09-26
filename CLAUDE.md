# Skill-Optimizer: rules for this repo

`main` is the toolkit, not a workspace. It holds exactly two things:

- `skill-creator/`: Anthropic's skill-creator, vendored unchanged.
- The description optimizer: `scripts/trigger_probe.py` and
  `scripts/run_loop_resilient.py`, plus this file, `README.md` and
  `.gitignore`.

## Where skill work goes

Every skill you create or optimize gets its own branch, never `main`.
Skills, eval sets, results, reports and packaged `dist/` files all
live on that branch.

- Branch from `main`. Name it after the skill, e.g. `skill/<skill-name>`,
  unless the session already assigns a branch name.
- Lay it out as `skills/<name>/`, `evals/`, `results/`, `reports/` and `dist/`.
- Don't merge skill branches back into `main`, and don't open PRs
  from them into `main`.

## Changing `main`

Only change `main` to fix or improve skill-creator or the optimizer
scripts. Keep `skill-creator/` byte-identical to upstream. Put fixes in
`scripts/` (as `trigger_probe.py` does) instead of editing the vendored
copy. If a change to `main` isn't one of those, it belongs on a skill
branch.
