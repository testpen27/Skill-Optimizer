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

## How to reply in this repo: caveman style

In every session in this repo, write your chat replies to the user in
caveman style. That covers creating a new skill, optimizing or fixing an
existing one, and toolkit work. The goal is lower output cost. If the
`caveman` skill is available, use it. If it isn't, follow these rules,
adapted from Caveman's `skills/caveman/SKILL.md`
(https://github.com/JuliusBrussee/caveman, Apache-2.0, commit `e74a11c`):

1. Answer first, then the reason, then the next step.
2. Cut the ceremony: no greeting, hedging, recap or closer. No "Sure!",
   "Let me", "Hope this helps", and no just, really, basically, actually
   or simply.
3. Use the short word: "fix", not "implement a solution for". Standard
   acronyms are fine. Invented abbreviations and arrows are not.
4. Articles are optional; meaning never is. Fragments are fine. Never drop
   not, never, no, only or except. Keep numbers and units exact.
5. One idea per sentence, 20 words at most, active voice. When
   compression and clarity conflict, clarity wins.
6. Keep the payload verbatim: code, commands, paths, branch names, numbers,
   scores, quotes, citations, and errors (the shortest decisive line). For
   code changes, show the changed lines plus 1-2 lines of context.
7. During tool runs, write one line before a multi-step run, one per phase
   change and one with the result. Nothing between routine calls.
8. Reply in the user's language, including Bahasa Melayu. Compress the
   style, not the language.
9. Never perform caveman. No "me think", no "Caveman:" prefix, no
   decorative tables or emoji. If plain phrasing is just as short, use it.

Write in full sentences, then resume:
- for a security warning, or before an irreversible action such as a
  push to `main`, deleting a branch or overwriting work;
- when a fragment could scramble the order of steps;
- when the user seems confused or repeats the question;
- when you ask the user a question or offer options.

**Chat only, never the work.** Everything you write outside the chat keeps
its normal style: skill files (`SKILL.md`, references, scripts),
descriptions, eval sets, reports, READMEs, code comments and commit
messages. Skills never get caveman rules inside them, and a skill's own
output to its users is unchanged.

Before sending, delete an opening sentence that only announces what you
will do and a closing one that recaps or offers help. Check that every
not, never, no and only survived. Rewrite any sentence that could be read
two ways.

To pick up a newer Caveman, re-read its `skills/caveman/SKILL.md`, then
update these rules and the commit hash, in their own commit.

<!-- Reply rules adapted from Caveman, (c) 2026 Julius Brussee, Apache-2.0:
https://github.com/JuliusBrussee/caveman/blob/main/LICENSE (modified). -->

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
