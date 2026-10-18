"""Shared pieces of the EP1 probes: a scrubbed process env, a throwaway HOME, the lane lock and
the evidence log. Standard library only, so the task tests import nothing from the SDK.

The probes drive a raw `claude_agent_sdk` client from a throwaway venv on D:, never the
harness. Build it once with
`uv venv D:/QMX-worktrees/qma-ship/engine/homes/ep1-venv --python 3.14` and
`uv pip install --python <venv>/Scripts/python.exe claude-agent-sdk==0.2.166` (the version in
`qmx-agents/uv.lock`), then run `<venv>/Scripts/python.exe scripts/probes/engine/p_model_ids.py`.
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import Final, TextIO

ENGINE_STORE: Final = Path("D:/QMX-worktrees/qma-ship/engine")
EVIDENCE: Final = ENGINE_STORE / "evidence" / "ep1"
HOMES: Final = ENGINE_STORE / "homes"
PLAN_CONFIG_DIR: Final = Path("D:/QMX-worktrees/qma-ship/home/claude")
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
LOCK_WAIT_S: Final = 3600.0
LOCK_POLL_S: Final = 20.0
LOG_PREFIX: Final = os.environ.get("EP1_LOG_PREFIX", "")
"""Read at import, before `scrub_process_env` removes the name."""
TRIAGE_PLAN_MODEL: Final = "haiku"
"""Appendix H: `triage` lists kimi/k3 then claude/haiku; haiku is its first plan-profile row."""

KEEP: Final = frozenset(
    {
        "PATH", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "USERNAME",
        "USERDOMAIN", "COMPUTERNAME", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)",
        "PROGRAMW6432", "COMMONPROGRAMFILES", "OS", "PROCESSOR_ARCHITECTURE",
        "NUMBER_OF_PROCESSORS", "LANG", "TZ", "TERM", "TMP", "TEMP",
    }
)  # fmt: skip


def scrub_process_env(environ: MutableMapping[str, str]) -> tuple[str, ...]:
    """Cut `environ` to `KEEP` in place and return the removed names. The SDK starts the CLI
    with `os.environ` and `options.env` merged, so the probe scrubs its own process first:
    this shell sets `ANTHROPIC_BASE_URL` and other names a plan client must not see."""
    removed = sorted(name for name in environ if name.upper() not in KEEP)
    for name in removed:
        del environ[name]
    return tuple(removed)


def home_env(home: Path, config_dir: Path) -> dict[str, str]:
    """HOME and the app data folders on a throwaway folder, so the CLI never reads the
    operator's own profile or `~/.claude`, and `CLAUDE_CONFIG_DIR` on `config_dir`."""
    roaming, local, tmp = home / "AppData" / "Roaming", home / "AppData" / "Local", home / "tmp"
    for folder in (roaming, local, tmp, config_dir):
        folder.mkdir(parents=True, exist_ok=True)
    return {
        "CLAUDE_CONFIG_DIR": str(config_dir),
        "HOME": str(home),
        "USERPROFILE": str(home),
        "APPDATA": str(roaming),
        "LOCALAPPDATA": str(local),
        "TMP": str(tmp),
        "TEMP": str(tmp),
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }


@contextmanager
def lane_lock(log: Log) -> Iterator[None]:
    """Hold `D:/QMX-worktrees/.engine-lane-lock` while the ship home's plan login is in use.
    Another lane on the same login would share its rate window and its CLI trees."""
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            LANE_LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SystemExit(f"lane lock still held after {LOCK_WAIT_S:.0f} s") from None
            log(f"lane lock held by another lane; retrying in {LOCK_POLL_S:.0f} s")
            time.sleep(LOCK_POLL_S)
    try:
        yield
    finally:
        LANE_LOCK.rmdir()


class Log:
    """Writes `<EVIDENCE>/<EP1_LOG_PREFIX><slug>.log`; the owner's runs use the prefix
    `owner-`, the checker's its own."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{LOG_PREFIX}{slug}.log"
        self._file: TextIO = self.path.open("w", encoding="utf-8")
        self.passed = True
        self(f"=== {slug} {time.strftime('%Y-%m-%dT%H:%M:%S%z')} python {sys.version.split()[0]}")

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        self._file.write(stamped + "\n")
        self._file.flush()

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        self._file.close()
        return 0 if self.passed else 1
