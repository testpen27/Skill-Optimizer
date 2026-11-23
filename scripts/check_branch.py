#!/usr/bin/env python3
"""Check the current checkout against the branch rules in CLAUDE.md.

    python3 scripts/check_branch.py [--branch NAME] [--base REF]

The branch name picks the rules:

- `main` (and a session branch with no `skills/`): the toolkit only, with
  skill-creator byte-identical to the pinned upstream copy.
- `skill/<name>`: exactly one skill, `skills/<name>/`, in the standard
  layout; toolkit files identical to main's; main fully merged in; and
  `dist/<name>.skill`, if present, matching the skill source.
- a session-assigned branch (`claude/*`, `ccr-*`) carrying `skills/`: the
  skill rules, plus a reminder that the work has to end up on `skill/<name>`.

Prints ERROR and WARN lines and exits 1 if there is any ERROR. It runs in
CI on every push and at the start of every Claude Code session.

    python3 scripts/check_branch.py --branches

instead reports on every branch on origin (run `git fetch origin` first):
which session branches still hold skill work missing from its
`skill/<name>` branch, which are fully merged and safe to delete, and which
skill branches have not merged the latest main. Exits 0; it only informs.
"""

import argparse
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Git tree hash of the vendored skill-creator/. Change it only when
# deliberately re-vendoring a newer upstream copy, in its own commit.
SKILL_CREATOR_TREE = "f569eadb0bff083d10f2bd19a0e4eede0ec4e7dd"

# Everything main may contain. Skill branches must carry these unchanged.
TOOLKIT_FILES = {
    ".gitignore",
    "CLAUDE.md",
    "README.md",
    ".claude/settings.json",
    ".github/workflows/branch-rules.yml",
    "scripts/check_branch.py",
    "scripts/run_loop_resilient.py",
    "scripts/trigger_probe.py",
}
TOOLKIT_DIRS = ("skill-creator/",)

# Top-level folders a skill branch may add. scripts/ may gain new files
# (a skill's own harness) but not changed toolkit ones.
SKILL_DIRS = ("skills/", "evals/", "results/", "reports/", "dist/", "scripts/")

JUNK = re.compile(r"(^|/)(__pycache__/|\.DS_Store$|node_modules/)|\.pyc$")
SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def git(*args, check=True):
    out = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True
    )
    if check and out.returncode:
        raise RuntimeError(out.stderr.strip())
    return out


def current_branch():
    # CI checks out a detached HEAD; GitHub names the branch here.
    if os.environ.get("GITHUB_REF_NAME") and os.environ.get("GITHUB_REF_TYPE") == "branch":
        return os.environ["GITHUB_REF_NAME"]
    return git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def find_base(explicit):
    for ref in [explicit] if explicit else ["origin/main", "main"]:
        if git("rev-parse", "--verify", "--quiet", ref + "^{commit}", check=False).returncode == 0:
            return ref
    return None


def tracked():
    return git("ls-files").stdout.splitlines()


def is_toolkit(path):
    return path in TOOLKIT_FILES or path.startswith(TOOLKIT_DIRS)


def check_common(files, r):
    for f in files:
        if JUNK.search(f):
            r.error(f"junk file committed: {f}")
    tree = git("rev-parse", "HEAD:skill-creator", check=False).stdout.strip()
    if tree != SKILL_CREATOR_TREE:
        r.error(
            "skill-creator/ differs from the pinned upstream copy; revert it "
            "and put the fix in scripts/ instead"
        )


def check_main(files, r):
    for f in files:
        if not is_toolkit(f):
            r.error(f"not toolkit, move it to a skill/<name> branch: {f}")
    for f in TOOLKIT_FILES:
        if f not in files:
            r.error(f"toolkit file missing: {f}")


def frontmatter_name(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None, False
    fm = m.group(1)
    name = re.search(r"^name:\s*(\S+)\s*$", fm, re.M)
    return (name.group(1).strip("'\"") if name else None), bool(
        re.search(r"^description:", fm, re.M)
    )


def check_package(name, files, r):
    pkg = ROOT / "dist" / f"{name}.skill"
    others = [f for f in files if f.startswith("dist/") and f != f"dist/{name}.skill"]
    for f in others:
        r.error(f"dist/ holds only dist/{name}.skill, found {f}")
    if f"dist/{name}.skill" not in files:
        r.warn(f"no dist/{name}.skill yet; package it when the skill is done")
        return
    sys.path.insert(0, str(ROOT / "skill-creator"))
    try:
        from scripts.package_skill import should_exclude  # noqa: E402
    except ImportError as e:  # package_skill needs PyYAML
        r.warn(f"cannot check dist/{name}.skill against its source ({e})")
        return

    want = {}
    for f in files:
        if f.startswith(f"skills/{name}/"):
            arc = f[len("skills/"):]
            if not should_exclude(Path(arc)):
                want[arc] = (ROOT / f).read_bytes()
    with zipfile.ZipFile(pkg) as z:
        got = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    stale = sorted(
        [f"missing {a}" for a in want.keys() - got.keys()]
        + [f"extra {a}" for a in got.keys() - want.keys()]
        + [f"differs {a}" for a in want.keys() & got.keys() if want[a] != got[a]]
    )
    if stale:
        r.error(
            f"dist/{name}.skill is stale vs skills/{name}/ ({'; '.join(stale[:5])}); "
            f"repackage with skill-creator's scripts/package_skill.py"
        )


def check_skill(name, files, base, r):
    if not SKILL_NAME.match(name):
        r.error(f"skill name '{name}' must be lowercase-hyphenated")
    skills = sorted({f.split("/")[1] for f in files if f.startswith("skills/") and f.count("/") >= 2})
    if skills != [name]:
        r.error(f"skills/ must hold exactly skills/{name}/, found {skills or 'nothing'}")
    skill_md = ROOT / "skills" / name / "SKILL.md"
    if skill_md.exists():
        fm_name, has_desc = frontmatter_name(skill_md)
        if fm_name != name:
            r.error(f"skills/{name}/SKILL.md frontmatter name is '{fm_name}', expected '{name}'")
        if not has_desc:
            r.error(f"skills/{name}/SKILL.md has no description in its frontmatter")
    else:
        r.error(f"missing skills/{name}/SKILL.md")

    for f in files:
        if not (is_toolkit(f) or f.startswith(SKILL_DIRS)):
            r.error(f"outside the skill-branch layout: {f}")
        elif f.endswith(".skill") and not f.startswith("dist/"):
            r.error(f"packaged skill outside dist/: {f}; keep only dist/{name}.skill")
    if not any(f.startswith("evals/") for f in files):
        r.warn("no evals/ yet; add the trigger eval set")
    if not any(f.startswith("reports/") for f in files):
        r.warn("no reports/ yet; write up the evaluation")
    check_package(name, files, r)

    if base is None:
        r.warn("no main ref to compare with; run `git fetch origin main`")
        return
    if git("merge-base", "--is-ancestor", base, "HEAD", check=False).returncode:
        r.error(f"{base} is not merged in; run `git merge {base}` (never rebase)")
    changed = git("diff", "--name-only", base, "HEAD", "--", *TOOLKIT_FILES, *TOOLKIT_DIRS).stdout.split()
    for f in changed:
        r.error(
            f"toolkit file differs from {base}: {f}; make the fix on main "
            f"first, then merge main into this branch"
        )


def skills_on(ref):
    out = git("ls-tree", "--name-only", f"{ref}:skills", check=False)
    return out.stdout.split() if out.returncode == 0 else []


def count(range_, path=None):
    return int(git("rev-list", "--count", range_, *(["--", path] if path else [])).stdout.strip())


def report_branches(quiet):
    """Summarise every branch on origin: what needs migrating or merging."""
    refs = git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").stdout.split()
    refs = [r for r in refs if r not in ("origin", "origin/HEAD")]
    names = {r[len("origin/"):] for r in refs}
    has_main = "main" in names
    attention, info = [], []
    for ref in sorted(refs):
        b = ref[len("origin/"):]
        if b == "main":
            continue
        if b.startswith("skill/"):
            if has_main and count(f"{ref}..origin/main"):
                attention.append(f"{b}: main not merged in; run `git merge origin/main` there")
            else:
                info.append(f"{b}: up to date with main")
            continue
        # A session branch: is everything on it already somewhere permanent?
        homes = [f"skill/{s}" for s in skills_on(ref)] or ["main"]
        missing = [h for h in homes if h not in names]
        if missing:
            attention.append(
                f"{b}: holds work with no {', '.join(missing)} branch yet; "
                f"move it there (ask the user first)"
            )
            continue
        # Only commits touching that skill count against its branch.
        ahead = {
            h: count(f"origin/{h}..{ref}", f"skills/{h[len('skill/'):]}" if h != "main" else None)
            for h in homes
        }
        if any(ahead.values()):
            behind = [h for h, n in ahead.items() if n]
            what = ", ".join(f"{ahead[h]} commit(s) on skills/ not on {h}" for h in behind)
            attention.append(f"{b}: {what}; merge it into {' and '.join(behind)} before deleting")
        else:
            info.append(f"{b}: fully contained in {', '.join(homes)}; safe to delete")
    if attention or not quiet:
        print("Branches on origin:")
        for line in attention:
            print(f"  ATTENTION: {line}")
        if not quiet:
            for line in info:
                print(f"  ok: {line}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--branch", help="branch name to check as (default: current)")
    ap.add_argument("--base", help="ref for main (default: origin/main, then main)")
    ap.add_argument("--branches", action="store_true", help="report on every branch on origin")
    ap.add_argument("--quiet", action="store_true", help="with --branches: print only what needs attention")
    args = ap.parse_args()

    if args.branches:
        return report_branches(args.quiet)

    branch = args.branch or current_branch()
    files = tracked()
    r = Report()
    check_common(files, r)

    if branch == "main":
        kind = "main"
        check_main(files, r)
    elif branch.startswith("skill/"):
        kind = "skill branch"
        check_skill(branch[len("skill/"):], files, find_base(args.base), r)
    else:
        found = sorted({f.split("/")[1] for f in files if f.startswith("skills/") and f.count("/") >= 2})
        if found:
            kind = "session branch with skill work"
            r.warn(
                f"'{branch}' is not a skill/<name> branch; this work must end up "
                f"on skill/{found[0]} (ask the user before pushing there)"
            )
            check_skill(found[0], files, find_base(args.base), r)
        else:
            kind = "toolkit branch"
            check_main(files, r)

    print(f"Branch rules: {branch} ({kind})")
    for w in r.warnings:
        print(f"  WARN:  {w}")
    for e in r.errors:
        print(f"  ERROR: {e}")
    if not r.errors:
        print("  OK: follows the rules in CLAUDE.md")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main())
