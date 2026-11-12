"""The timed wrapper every test, lint and types command runs through.

Each run gets its own temp folder and data folders, a fake keyring, the credential guard, no git
prompt and no stdin. While it runs, the wrapper touches the slice's heartbeat file, which is the
liveness signal a long but healthy test gives. On timeout it stops the whole process tree.
"""

from __future__ import annotations

import dataclasses
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ship.gitx import env_no_prompt
from ship.proc import kill_tree, popen_group_kwargs
from ship.settings import Settings

GUARD_DIR = Path(__file__).resolve().parent / "guard"
TIMEOUT_RC = 124


@dataclasses.dataclass(frozen=True)
class RunResult:
    rc: int
    timed_out: bool
    seconds: float
    log: Path


def test_env(run_dir: Path, settings: Settings) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items()
           if not any(k.upper().startswith(p) for p in settings.strip_env_prefixes)}
    env = env_no_prompt(env)
    tmp = run_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for name in ("TMP", "TEMP", "TMPDIR"):
        env[name] = str(tmp)
    for name in settings.data_env_vars:
        folder = run_dir / "data" / name.lower()
        folder.mkdir(parents=True, exist_ok=True)
        env[name] = str(folder)
    env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.fail.Keyring"
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(GUARD_DIR), env.get("PYTHONPATH", "")) if p)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["SHIP_RUN_DIR"] = str(run_dir)
    return env


def touch(path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def run_timed(argv: list[str], cwd: Path, log: Path, timeout_s: float, settings: Settings,
              tmp_root: Path, heartbeat: Path | None = None,
              extra_env: dict[str, str] | None = None) -> RunResult:
    log.parent.mkdir(parents=True, exist_ok=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=tmp_root))
    env = test_env(run_dir, settings)
    env.update(extra_env or {})
    started = time.monotonic()
    timed_out = False
    with open(log, "w", encoding="utf-8", newline="\n") as out:
        out.write(f"$ {' '.join(argv)}\n# cwd {cwd}\n")
        out.flush()
        try:
            child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=out,
                                     stderr=subprocess.STDOUT, **popen_group_kwargs())
        except OSError as exc:
            out.write(f"could not start: {exc}\nEXIT rc=127\n")
            shutil.rmtree(run_dir, ignore_errors=True)
            return RunResult(127, False, 0.0, log)
        while True:
            touch(heartbeat)
            left = timeout_s - (time.monotonic() - started)
            if left <= 0:
                timed_out = True
                kill_tree(child.pid)
                child.wait()
                break
            try:
                child.wait(timeout=min(settings.heartbeat_interval_s, left))
                break
            except subprocess.TimeoutExpired:
                continue
        seconds = time.monotonic() - started
        rc = TIMEOUT_RC if timed_out else child.returncode
    with open(log, "a", encoding="utf-8", newline="\n") as out:
        note = f" timeout after {timeout_s:.0f}s" if timed_out else ""
        out.write(f"\nEXIT rc={rc} seconds={seconds:.0f}{note}\n")
    touch(heartbeat)
    shutil.rmtree(run_dir, ignore_errors=True)
    return RunResult(rc, timed_out, seconds, log)
