"""Trigger detection for the skill-creator description optimizer.

Replaces the upstream `run_eval.run_single_query`, which has two bugs that both
report a healthy skill as 0%:

1. It registers the skill under test as a slash command in `.claude/commands/`.
   A command never reaches the `available_skills` list the model picks from, so
   there is nothing to invoke.
2. Its detector accepts the skill only if it is the *very first* tool call of
   the turn. In a real session Claude routinely looks around first -- a Bash
   `ls` to find the file the user named -- and invokes the skill a beat later.

An earlier version of this file fixed both but streamed the output with
`--include-partial-messages` and early-returned on the first match, and it
produced false negatives: queries it scored 0/3 scored 2/2 when the same turn
was captured in full. Two causes, and the fix for each:

- stdin was inherited from the parent. `claude` waits on it, warns, and can
  exit before doing any work, which the probe cannot distinguish from "answered
  without the skill". stdin is now DEVNULL.
- the full-message path looked for the skill name under the input key `skill`.
  Reading the raw JSON instead does not depend on the tool's parameter naming.

A fifth, and the nastiest because it inflates rather than zeroes: matching the
skill name anywhere in the transcript counts the *listing* of available skills
in the init event as a hit, so any Skill call at all -- to `dataviz`, to
`artifact-design` -- scored as our skill triggering. The subprocess inherits the
user-level skills too, so there is always something else for it to pick. The
name must be matched inside a Skill/Read tool_use input, nowhere else.

A fourth: a run can come back in two seconds having done nothing real, and an
earlier validity check ("did any assistant message appear?") passed it, so a
whole 60-run pass returned all-zero in 29s where a genuine one takes ten
minutes. A real turn ends with a `result` event carrying subtype "success",
is_error false, and a nonzero cost; anything else is now a ProbeFailure rather
than a silent zero. Zeros are the failure mode that looks like data, so they
have to be the hardest outcome to record by accident.

A third bug showed up once those were fixed: every concurrent run wrote its
skill into the *same* project `.claude/skills/`, so a run with N workers put N
near-identical skills in front of each model turn. The turn would often invoke
a sibling's copy, whose name does not match this run's, and the probe scored it
as "did not trigger" -- parallel passes under-reported badly against serial
ones (0/3 vs 2/2 on the same query). Each run now gets its own project root.

So: run the turn to completion, capture everything, then decide. Slower per
run, but a measurement that disagrees with itself is worth nothing.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


class ProbeFailure(RuntimeError):
    """The run never produced a model turn, so it says nothing about triggering."""


class ProbeAbort(BaseException):
    """Probe runs keep failing; stop the whole pass rather than record zeros.

    A BaseException on purpose: upstream run_eval catches Exception from each
    run and appends False, which turned a spend-limit outage into a pass where
    every should-trigger query scored 0/10. This one gets past that handler.
    """


PROBE_ATTEMPTS = 3

# Isolating the skill under test from skills the account syncs in.
# PROBE_SETTING_SOURCES (e.g. "project") is passed to --setting-sources, which
# stops user-level skills loading; an older copy of the same skill there would
# otherwise take its triggers. PROBE_COMPETITORS names a directory of skill
# folders copied into every run's project, so the model still has realistic
# alternatives to choose between.
SETTING_SOURCES = os.environ.get("PROBE_SETTING_SOURCES")
COMPETITORS = os.environ.get("PROBE_COMPETITORS")


def _invoked_this_skill(text: str, clean_name: str) -> bool:
    """True only if a Skill/Read tool call names *this* skill.

    Scanning the whole transcript is wrong: the init event lists every
    available skill, so the name is present whether or not it was used, and any
    Skill call to something else scored as a hit.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        for item in event.get("message", {}).get("content", []):
            if item.get("type") != "tool_use":
                continue
            name = item.get("name", "")
            tool_input = item.get("input", {}) or {}
            if name == "Skill":
                # The parameter has been called "skill" and "command"; check the
                # values rather than betting on the key.
                if any(clean_name in str(v) for v in tool_input.values()):
                    return True
            elif name == "Read":
                if clean_name in str(tool_input.get("file_path", "")):
                    return True
    return False


def _require_real_turn(text: str, proc) -> None:
    """Raise unless the transcript shows a turn that actually ran.

    Checked against captured transcripts of known-good runs: those end with a
    result event of subtype "success", is_error false, and a real cost. A run
    that fails any of these tells us nothing about triggering, and must not be
    recorded as "did not trigger".
    """
    result = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event

    if result is None:
        stderr = proc.stderr.decode("utf-8", errors="replace")[:200]
        raise ProbeFailure(f"no result event (rc={proc.returncode}): {stderr or text[:200]}")
    if result.get("subtype") != "success" or result.get("is_error"):
        raise ProbeFailure(
            f"result subtype={result.get('subtype')!r} is_error={result.get('is_error')!r}: "
            f"{str(result.get('result'))[:200]}"
        )
    if not result.get("total_cost_usd"):
        raise ProbeFailure("result reported no cost -- the turn did no work")


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Retry a failed probe run; abort the pass if it never succeeds."""
    for attempt in range(1, PROBE_ATTEMPTS + 1):
        try:
            return _run_once(query, skill_name, skill_description, timeout, project_root, model)
        except ProbeFailure as e:
            if attempt == PROBE_ATTEMPTS or "spend limit" in str(e):
                raise ProbeAbort(f"probe failed {attempt}x, aborting pass: {e}") from e
            time.sleep(10 * attempt)
    raise AssertionError("unreachable")


def _run_once(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Return whether `claude -p` invoked the skill anywhere in the turn.

    Raises ProbeFailure when the run produced no assistant turn at all -- a
    crash, a spend limit, a timeout. Counting those as "did not trigger" is how
    the earlier version manufactured zeros.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-probe-{unique_id}"
    # Private project root per run: concurrent runs must not see each other's
    # skills, or the turn can invoke a sibling's identical copy.
    run_root = Path(tempfile.mkdtemp(prefix=f"probe-{unique_id}-"))
    skill_dir = run_root / ".claude" / "skills" / clean_name

    try:
        if COMPETITORS:
            for src in Path(COMPETITORS).iterdir():
                if (src / "SKILL.md").exists():
                    shutil.copytree(src, run_root / ".claude" / "skills" / src.name)
        skill_dir.mkdir(parents=True, exist_ok=True)
        indented = "\n  ".join(skill_description.split("\n"))
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {clean_name}\ndescription: |\n  {indented}\n---\n\n"
            f"# {skill_name}\n\nFollow the guidance for: {skill_name}.\n"
        )

        cmd = ["claude", "-p", query, "--output-format", "stream-json", "--verbose"]
        if model:
            cmd.extend(["--model", model])
        if SETTING_SOURCES:
            cmd.extend(["--setting-sources", SETTING_SOURCES])

        # CLAUDECODE guards against interactive nesting; a subprocess is safe.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        try:
            proc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                cwd=str(run_root),
                env=env,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise ProbeFailure(f"timed out after {timeout}s")

        text = proc.stdout.decode("utf-8", errors="replace")
        _require_real_turn(text, proc)

        return _invoked_this_skill(text, clean_name)
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


run_single_query.__module__ = "scripts.run_eval"
run_single_query.__qualname__ = "run_single_query"
