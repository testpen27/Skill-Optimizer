#!/usr/bin/env python3
"""Run run_loop_resilient.py with sample files in every probe's project root.

    PROBE_FIXTURES=evals/trigger-fixtures python3 scripts/run_loop_with_fixtures.py <run_loop args>

Most social-media-report requests say "I've attached the export". The stock
probe runs each query in an empty directory, so the model looks for the
file, finds nothing, and asks the user to re-attach it instead of loading
the skill. That scores as "did not trigger" and measures the harness, not
the description. This wrapper copies PROBE_FIXTURES into each run's
project root (under uploads/) so those turns see what a real user would
have supplied.

With real files present, a triggered turn goes on to do the whole analysis,
which can run past any sane timeout and cost several times a normal probe.
So once the transcript shows this run's skill being invoked -- judged by
trigger_probe's own _invoked_this_skill, unchanged -- the turn is stopped
and a synthetic success result is appended. A turn that never invokes the
skill still runs to completion and is judged exactly as before.

The toolkit files are not modified; only names on the trigger_probe module
are patched.
"""

import json
import os
import queue
import runpy
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = os.environ.get("PROBE_FIXTURES")
if not FIXTURES or not Path(FIXTURES).is_dir():
    sys.exit("set PROBE_FIXTURES to a directory of files to place in each probe run")
FIXTURES = str(Path(FIXTURES).resolve())

sys.path.insert(0, str(HERE))
import trigger_probe  # noqa: E402


def _mkdtemp_with_fixtures(*args, **kwargs):
    root = tempfile.mkdtemp(*args, **kwargs)
    shutil.copytree(FIXTURES, Path(root) / "uploads")
    return root


def _run_until_invoked(cmd, stdin=None, capture_output=True, cwd=None, env=None, timeout=None):
    probes = list((Path(cwd) / ".claude" / "skills").glob("*-probe-*"))
    clean_name = probes[0].name if len(probes) == 1 else None

    proc = subprocess.Popen(
        cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env
    )
    lines: queue.Queue = queue.Queue()

    def pump():
        for raw in proc.stdout:
            lines.put(raw)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    deadline = time.monotonic() + timeout if timeout else None
    out = []
    early = False
    while True:
        wait = None if deadline is None else deadline - time.monotonic()
        if wait is not None and wait <= 0:
            proc.kill()
            proc.wait()
            raise subprocess.TimeoutExpired(cmd, timeout)
        try:
            raw = lines.get(timeout=wait)
        except queue.Empty:
            continue
        if raw is None:
            break
        out.append(raw)
        if clean_name and b'"tool_use"' in raw and trigger_probe._invoked_this_skill(
            raw.decode("utf-8", errors="replace"), clean_name
        ):
            early = True
            proc.kill()
            break
    proc.wait()
    stderr = proc.stderr.read() if proc.stderr else b""
    if early:
        out.append(
            json.dumps(
                {"type": "result", "subtype": "success", "is_error": False,
                 "total_cost_usd": 1e-9, "stopped_early": "skill invoked"}
            ).encode() + b"\n"
        )
    return subprocess.CompletedProcess(cmd, proc.returncode, b"".join(out), stderr)


trigger_probe.tempfile = types.SimpleNamespace(mkdtemp=_mkdtemp_with_fixtures)
trigger_probe.subprocess = types.SimpleNamespace(
    run=_run_until_invoked,
    DEVNULL=subprocess.DEVNULL,
    TimeoutExpired=subprocess.TimeoutExpired,
)

if __name__ == "__main__":
    sys.argv[0] = str(HERE / "run_loop_resilient.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
