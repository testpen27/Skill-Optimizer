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

At session start the hook also runs `check_branch.py --branches --quiet`.
That lists every ATTENTION item on origin: session branches holding skill
work their `skill/<name>` branch lacks, and skill branches behind `main`.
Read those lines before starting. Run it without `--quiet` for the full
picture, including branches that are safe to delete.

## Before working on a skill

1. **Find what already exists.** Run `git fetch origin`, then
   `python3 scripts/check_branch.py --branches`. If the skill has a
   `skill/<name>` branch, that's where the work continues. If a `claude/*`
   or `ccr-*` branch holds newer commits for it, merge that branch into
   `skill/<name>` first (ask the user). Never start the skill over from an
   older copy.
2. **The repo is the source of truth, not the installed copy.** The skill
   Claude has installed may be older than `skill/<name>`. When the two
   disagree, ask the user which is current. Don't overwrite the branch
   with the installed copy.
3. **One skill per branch, always.** Don't copy another skill into a skill
   branch, even as a reference. Link to its `skill/<name>` branch instead.

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
    No `.skill` file goes anywhere else.
  - `scripts/`: optional. Only new, skill-specific scripts go here.

  Nothing else goes at the top level.
- **Keep the package current.** Whenever `skills/<name>/` changes,
  rebuild `dist/<name>.skill` with skill-creator's
  `scripts/package_skill.py`. The checker fails on a stale package. Then
  tell the user to upload the new `dist/<name>.skill` to Claude, or Claude
  keeps using the old version.
- **Nothing flows back into `main`.** Don't merge skill branches into
  `main`, and don't open PRs from them into `main`.
- **Stay current with `main`.** When `main` changes, merge it into the skill
  branch with `git merge origin/main`. Never rebase or force-push a skill
  branch.

## Chat-reply style for new skills

Every **new** skill gets a caveman-style chat section, so its chat replies
are short without the user asking each time. Put this block in the new
skill's `SKILL.md`, right after the frontmatter, unchanged:

```markdown
## Chat replies: caveman style

While this skill is in use, write chat replies in caveman style:
- Drop filler, pleasantries, hedging and restating the question. Articles
  are optional. Fragments are fine: "Done. 3 files changed. Test pass."
- Lead with the result, then only what the user needs to act on.
- Keep exact: code, commands, file paths, numbers, error text, names,
  quotes and citations.
- Reply in the user's language. The same rules apply in Bahasa Melayu.

This covers chat replies only, never the work itself. Files, documents,
reports, embeds, spreadsheets and any text written for readers keep the
full style and language this skill specifies.

Switch to full sentences for warnings, anything risky or irreversible,
questions where a misread would cost the user, or when the user asks for
an explanation.
```

- **New skills only.** Don't add it to existing skills unless the user
  asks for that skill.
- **Skip it, and ask the user, when the skill's job is the voice itself.**
  Examples are a skill that sets how Claude talks, such as fable-5-logic,
  or one that makes writing sound human, such as ai-audit.
- **It doesn't count against the description.** The block lives in the
  SKILL.md body, so it doesn't change triggering or the optimizer's
  description work.

## Session-assigned branches

A cloud session is often assigned a `claude/<random>` or `ccr-<random>`
branch and may push only there. If the session's work is a skill:

1. Do the work in the skill-branch layout above on the assigned branch.
2. When it's done, ask the user for permission to push it to
   `skill/<name>`. If `skill/<name>` already exists, merge it in first
   instead of overwriting it.
3. Tell the user that the session branch can be deleted. Sessions can't
   delete branches, so the user has to do it.
4. **Once the user deletes a session branch, don't push to it again.** An
   old session that keeps pushing to its deleted branch recreates it. Stray
   work then piles up where `skill/<name>` never sees it.

Don't leave finished skill work only on a session branch.

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
