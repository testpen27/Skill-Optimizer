"""Corrected trigger detection for the skill-creator description optimizer.

Two bugs in the upstream `run_eval.run_single_query` make its numbers
unusable in a sandbox, and both of them report a healthy skill as 0%:

1. It registers the skill under test as a slash command in
   `.claude/commands/`. A command is not a skill: it never reaches the
   `available_skills` list the model actually picks from, so the model has
   nothing to invoke and the run always scores as "did not trigger". Writing
   a real `.claude/skills/<name>/SKILL.md` is what puts it in front of the
   model.

2. Its detector accepts the skill only if it is the *very first* tool call
   of the turn -- any other tool first and it returns False immediately. In
   a real session Claude routinely looks around first (a Bash `ls` to locate
   the file the user mentioned, a Grep to find the module) and invokes the
   skill a beat later. That is a normal trigger, and the strict reading
   throws it away.

This version registers a real skill and counts an invocation anywhere in the
turn, which is the thing anyone actually cares about: did the skill get used.
"""

import json
import os
import select
import subprocess
import time
import uuid
from pathlib import Path


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Return whether `claude -p` invoked the skill anywhere in the turn."""
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-probe-{unique_id}"
    skill_dir = Path(project_root) / ".claude" / "skills" / clean_name
    skill_file = skill_dir / "SKILL.md"

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        # Block scalar keeps quotes and colons in the description from
        # breaking the frontmatter.
        indented = "\n  ".join(skill_description.split("\n"))
        skill_file.write_text(
            f"---\nname: {clean_name}\ndescription: |\n  {indented}\n---\n\n"
            f"# {skill_name}\n\nFollow the guidance for: {skill_name}.\n"
        )

        cmd = [
            "claude", "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # CLAUDECODE is a guard against interactive nesting; a subprocess
        # call is safe, so drop it. Same reasoning as upstream.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=project_root, env=env,
        )

        start = time.time()
        buffer = ""
        pending_tool = None
        accumulated = ""

        try:
            while time.time() - start < timeout:
                if process.poll() is not None:
                    rest = process.stdout.read()
                    if rest:
                        buffer += rest.decode("utf-8", errors="replace")
                    break

                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                if not ready:
                    continue
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Stream events let us stop the run the moment the skill
                    # is invoked, rather than paying for the whole turn.
                    if event.get("type") == "stream_event":
                        se = event.get("event", {})
                        se_type = se.get("type", "")
                        if se_type == "content_block_start":
                            cb = se.get("content_block", {})
                            if cb.get("type") == "tool_use":
                                pending_tool = cb.get("name", "")
                                accumulated = ""
                        elif se_type == "content_block_delta" and pending_tool in ("Skill", "Read"):
                            delta = se.get("delta", {})
                            if delta.get("type") == "input_json_delta":
                                accumulated += delta.get("partial_json", "")
                                if clean_name in accumulated:
                                    return True
                        elif se_type == "content_block_stop":
                            # A non-matching tool call is not a verdict --
                            # the skill can still be invoked later in the
                            # turn, so just reset and keep reading.
                            pending_tool = None
                            accumulated = ""

                    elif event.get("type") == "assistant":
                        for item in event.get("message", {}).get("content", []):
                            if item.get("type") != "tool_use":
                                continue
                            name = item.get("name", "")
                            tool_input = item.get("input", {})
                            if name == "Skill" and clean_name in str(tool_input.get("skill", "")):
                                return True
                            if name == "Read" and clean_name in str(tool_input.get("file_path", "")):
                                return True

                    elif event.get("type") == "result":
                        return False
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

        return False
    finally:
        if skill_file.exists():
            skill_file.unlink()
        if skill_dir.exists():
            skill_dir.rmdir()


# Pickled by qualified name when the pool forks workers, so it has to look
# like it lives in the module it replaces.
run_single_query.__module__ = "scripts.run_eval"
run_single_query.__qualname__ = "run_single_query"
