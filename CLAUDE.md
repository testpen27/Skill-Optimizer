# Skill-Optimizer: rules for this repo

`main` is the toolkit, not a workspace. It holds exactly:

- `skill-creator/`: Anthropic's skill-creator, vendored unchanged.
- The description optimizer: `scripts/trigger_probe.py` and
  `scripts/run_loop_resilient.py`.
- The rule enforcement: `scripts/check_branch.py`,
  `.github/workflows/branch-rules.yml` and `.claude/settings.json`.
- This file, `README.md` and `.gitignore`.

`scripts/check_branch.py` enforces the rules below. It runs at the start of
every Claude Code session, through the SessionStart hook in
`.claude/settings.json`, and in CI on every push. Run it yourself before
every push: `python3 scripts/check_branch.py`. Fix every ERROR it reports
before pushing.

## Where skill work goes

Every skill you create or optimize gets its own branch, never `main`.

- **One skill per branch.** Name it `skill/<skill-name>`, lowercase with
  hyphens. `<skill-name>` must match the `name:` in the skill's
  `SKILL.md` frontmatter.
- **Branch from `main`.** Lay it out as follows:
  - `skills/<name>/`: the skill itself. Nothing else goes in `skills/`.
  - `evals/`: trigger eval sets and the original description.
  - `results/`: raw run output, logs and `results.json`.
  - `reports/`: the write-up of what was tested and what changed.
  - `dist/<name>.skill`: the packaged skill, and nothing else in `dist/`.
  - `scripts/`: optional. Only new, skill-specific scripts go here.

  Nothing else goes at the top level.
- **Keep the package current.** Whenever `skills/<name>/` changes,
  rebuild `dist/<name>.skill` with skill-creator's
  `scripts/package_skill.py`. The checker fails on a stale package.
- **Nothing flows back into `main`.** Don't merge skill branches into
  `main`, and don't open PRs from them into `main`.
- **Stay current with `main`.** When `main` changes, merge it into the skill
  branch with `git merge origin/main`. Never rebase or force-push a skill
  branch.

## Session-assigned branches

A cloud session is often assigned a `claude/<random>` branch and may push
only there. If the session's work is a skill:

1. Do the work in the skill-branch layout above on the assigned branch.
2. When it's done, ask the user for permission to push it to
   `skill/<name>`. If `skill/<name>` already exists, merge it in first
   instead of overwriting it.
3. Tell the user that the `claude/*` branch can be deleted. Sessions can't
   delete branches, so the user has to do it.

Don't leave finished skill work only on a `claude/*` branch.

## Changing `main`

Only change `main` to fix or improve skill-creator, the optimizer scripts or
the rule enforcement.

- **Toolkit fixes found during skill work go to `main` first.** If a skill
  run exposes a bug in `trigger_probe.py` or `run_loop_resilient.py`, commit
  the fix to `main`, then merge `main` into the skill branch. Never leave a
  modified toolkit file on a skill branch. The checker fails on any toolkit
  file that differs from `main`.
- **`skill-creator/` stays byte-identical to upstream.** The checker pins its
  git tree hash. Put fixes in `scripts/`, as `trigger_probe.py` does,
  instead of editing the vendored copy. Update the pin in `check_branch.py`
  only when re-vendoring a newer upstream copy, and do that in its own
  commit.
- **Anything else belongs on a skill branch.** If a change to `main` isn't
  one of the above, move it there.
