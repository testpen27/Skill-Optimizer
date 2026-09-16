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

A third bug showed up once those were fixed: every concurrent run wrote its
skill into the *same* project `.claude/skills/`, so a run with N workers put N
near-identical skills in front of each model turn. The turn would often invoke
a sibling's copy, whose name does not match this run's, and the probe scored it
as "did not trigger" -- parallel passes under-reported badly against serial
ones (0/3 vs 2/2 on the same query). Each run now gets its own project root.

So: run the turn to completion, capture everything, then decide. Slower per
run, but a measurement that disagrees with itself is worth nothing.
"""

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path


class ProbeFailure(RuntimeError):
    """The run never produced a model turn, so it says nothing about triggering."""


def run_single_query(
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
        skill_dir.mkdir(parents=True, exist_ok=True)
        indented = "\n  ".join(skill_description.split("\n"))
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {clean_name}\ndescription: |\n  {indented}\n---\n\n"
            f"# {skill_name}\n\nFollow the guidance for: {skill_name}.\n"
        )

        cmd = ["claude", "-p", query, "--output-format", "stream-json", "--verbose"]
        if model:
            cmd.extend(["--model", model])

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
        if '"type":"assistant"' not in text:
            raise ProbeFailure(
                f"no model turn (rc={proc.returncode}): "
                f"{proc.stderr.decode('utf-8', errors='replace')[:200] or text[:200]}"
            )

        # The skill name appears in the tool input either way; matching on the
        # raw JSON avoids depending on what the input key is called.
        return clean_name in text and (
            '"name":"Skill"' in text or '"name":"Read"' in text
        )
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


run_single_query.__module__ = "scripts.run_eval"
run_single_query.__qualname__ = "run_single_query"
