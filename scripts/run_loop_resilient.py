#!/usr/bin/env python3
"""Wrapper around skill-creator's description-optimization loop.

The loop calls `claude -p` once per iteration to propose a new description.
That call is a single point of failure: a transient non-zero exit (overload,
a dropped connection) aborts the whole run and throws away every eval result
collected so far, which is expensive -- one iteration is 60 `claude -p`
invocations. This wrapper retries that one call with backoff so a blip
costs a minute instead of the run.

Usage is identical to `python -m scripts.run_loop`. It uses the skill-creator
vendored at the repo root; set SKILL_CREATOR to point at a different copy.
"""

import os
import sys
import time
from pathlib import Path

SKILL_CREATOR = os.environ.get("SKILL_CREATOR") or str(
    Path(__file__).resolve().parent.parent / "skill-creator"
)
if not (Path(SKILL_CREATOR) / "scripts" / "run_loop.py").exists():
    sys.exit(f"No skill-creator found at {SKILL_CREATOR}; set SKILL_CREATOR")
sys.path.insert(0, SKILL_CREATOR)

import scripts.improve_description as imp  # noqa: E402
import scripts.run_eval as run_eval_mod  # noqa: E402

# Swap in the corrected trigger detector BEFORE run_loop is imported, so
# the name run_eval binds at import time is already the fixed one.
sys.path.insert(0, str(Path(__file__).parent))
from trigger_probe import run_single_query as _fixed_probe  # noqa: E402

run_eval_mod.run_single_query = _fixed_probe

from scripts.run_loop import main  # noqa: E402

DEBUG_DIR = Path(os.environ.get("IMPROVE_DEBUG_DIR", "."))


def _call_with_retry(prompt: str, model, timeout: int = 300, attempts: int = 6) -> str:
    """Run the proposal call, retrying with backoff on any failure.

    Reimplemented rather than wrapped because the upstream version reports only
    stderr, and these failures come back with stderr empty -- the diagnostic
    text lands on stdout. On every failed attempt the prompt and both streams
    are dumped so a repeat failure can actually be debugged instead of guessed
    at.
    """
    import subprocess

    cmd = ["claude", "-p", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    delay = 20
    for attempt in range(1, attempts + 1):
        try:
            result = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True,
                env=env, timeout=timeout,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            reason = f"exit={result.returncode} stdout={result.stdout[:400]!r} stderr={result.stderr[:400]!r}"
        except subprocess.TimeoutExpired:
            reason = f"timed out after {timeout}s"

        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        (DEBUG_DIR / f"improve_fail_{int(time.time())}_{attempt}.txt").write_text(
            f"{reason}\n\n===PROMPT===\n{prompt}"
        )
        if attempt == attempts:
            raise RuntimeError(f"improve call failed after {attempts} attempts: {reason}")
        print(
            f"  improve call failed (attempt {attempt}/{attempts}): {reason[:200]}; "
            f"retrying in {delay}s",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(delay)
        delay = min(delay * 2, 180)
    raise AssertionError("unreachable")


imp._call_claude = _call_with_retry

if __name__ == "__main__":
    main()
