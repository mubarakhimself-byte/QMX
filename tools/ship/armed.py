"""ARMED.md: every change preflight makes to the machine, each with its exact undo, and teardown.

Each change kind knows how to apply itself, undo itself, tell whether it is still in effect, and tell
whether it is gone. The human-readable part of ARMED.md is for him; the JSON block at its end is what
teardown reads. Teardown undoes in reverse order, checks each is gone, and keeps in ARMED.md only
what is still there, so running it again finishes the job.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ship.gitx import git, git_rc
from ship.layout import Program
from ship.proc import pid_alive
from ship.settings import Settings

MARK_OPEN = "<!-- ship-armed"
MARK_CLOSE = "-->"
KEEP_AWAKE = Path(__file__).resolve().parent / "keep_awake.py"


@dataclasses.dataclass
class Change:
    kind: str
    target: str  # repo path for git-config, folder for created-dir, flag file for keep-awake
    key: str = ""
    value: str = ""
    previous: str | None = None
    pid: int = 0


def _git_get(repo: str, key: str) -> str | None:
    done = subprocess.run(["git", "-C", repo, "config", "--local", "--get", key], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else None


class GitConfig:
    @staticmethod
    def describe(c: Change) -> tuple[str, str, str]:
        was = "unset" if c.previous is None else c.previous
        undo = (f'git -C "{c.target}" config --local --unset {c.key}' if c.previous is None
                else f'git -C "{c.target}" config --local {c.key} {c.previous}')
        return (f"git config {c.key}={c.value} in {c.target} (was {was})", undo,
                f'git -C "{c.target}" config --local --get {c.key} prints {was}')

    @staticmethod
    def apply(c: Change, settings: Settings) -> None:
        git(Path(c.target), "config", "--local", c.key, c.value, timeout=settings.git_timeout_s)

    @staticmethod
    def in_effect(c: Change) -> bool:
        return _git_get(c.target, c.key) == c.value

    @staticmethod
    def undo(c: Change, settings: Settings) -> None:
        if c.previous is None:
            git_rc(Path(c.target), "config", "--local", "--unset", c.key, timeout=settings.git_timeout_s)
        else:
            git(Path(c.target), "config", "--local", c.key, c.previous, timeout=settings.git_timeout_s)

    @staticmethod
    def gone(c: Change, settings: Settings) -> bool:
        return _git_get(c.target, c.key) == c.previous


class CreatedDir:
    @staticmethod
    def describe(c: Change) -> tuple[str, str, str]:
        return (f"created folder {c.target} for test temp and data folders",
                f'remove the folder "{c.target}" and everything in it', f'"{c.target}" does not exist')

    @staticmethod
    def apply(c: Change, settings: Settings) -> None:
        Path(c.target).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def in_effect(c: Change) -> bool:
        return Path(c.target).is_dir()

    @staticmethod
    def undo(c: Change, settings: Settings) -> None:
        shutil.rmtree(c.target, ignore_errors=True)

    @staticmethod
    def gone(c: Change, settings: Settings) -> bool:
        return not Path(c.target).exists()


class KeepAwake:
    @staticmethod
    def describe(c: Change) -> tuple[str, str, str]:
        return (f"keep-awake helper pid {c.pid}, alive while {c.target} exists",
                f'delete "{c.target}"; the helper exits within its poll time',
                f"process {c.pid} has exited")

    @staticmethod
    def apply(c: Change, settings: Settings) -> None:
        flag = Path(c.target)
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text("delete this file to let the machine sleep\n", "utf-8")
        argv = [sys.executable, str(KEEP_AWAKE), str(flag), str(settings.keep_awake_poll_s)]
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            child = subprocess.Popen(argv, creationflags=flags, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            if shutil.which("systemd-inhibit"):
                argv = ["systemd-inhibit", "--what=sleep:idle", "--why=ship run", *argv]
            child = subprocess.Popen(argv, start_new_session=True, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        c.pid = child.pid

    @staticmethod
    def in_effect(c: Change) -> bool:
        return Path(c.target).exists() and pid_alive(c.pid)

    @staticmethod
    def undo(c: Change, settings: Settings) -> None:
        Path(c.target).unlink(missing_ok=True)
        deadline = time.monotonic() + settings.teardown_wait_s
        while pid_alive(c.pid) and time.monotonic() < deadline:
            time.sleep(0.5)

    @staticmethod
    def gone(c: Change, settings: Settings) -> bool:
        return not Path(c.target).exists() and not pid_alive(c.pid)


KINDS = {"git-config": GitConfig, "created-dir": CreatedDir, "keep-awake": KeepAwake}


def read(program: Program) -> list[Change]:
    if not program.armed.exists():
        return []
    text = program.armed.read_text("utf-8")
    start = text.index(MARK_OPEN) + len(MARK_OPEN)
    return [Change(**item) for item in json.loads(text[start : text.index(MARK_CLOSE, start)])]


def write(program: Program, changes: list[Change], title: str = "ARMED") -> None:
    out = [f"# {title}", "",
           f"Written {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')} by `ship preflight`. "
           "Each change has its exact undo. `ship teardown` reverses them all and checks each is gone.", ""]
    for i, c in enumerate(changes, 1):
        what, undo, gone = KINDS[c.kind].describe(c)
        out += [f"## {i}. {c.kind}", "", f"- change: {what}", f"- undo: `{undo}`", f"- gone when: {gone}", ""]
    if not changes:
        out += ["Nothing is armed.", ""]
    out += [MARK_OPEN, json.dumps([dataclasses.asdict(c) for c in changes], indent=1), MARK_CLOSE, ""]
    program.armed.write_text("\n".join(out), "utf-8", newline="\n")


def arm(program: Program, wanted: list[Change], settings: Settings) -> list[str]:
    """Apply each wanted change not already in effect, recording it in ARMED.md before moving on.
    A change already recorded keeps its original `previous` value."""
    recorded = read(program)
    lines = []
    for want in wanted:
        known = next((c for c in recorded if (c.kind, c.target, c.key) == (want.kind, want.target, want.key)), None)
        kind = KINDS[want.kind]
        if known and kind.in_effect(known):
            lines.append(f"KEPT {want.kind} {want.key or want.target}")
            continue
        if not known and want.kind == "git-config" and _git_get(want.target, want.key) == want.value:
            lines.append(f"ALREADY {want.kind} {want.key} is {want.value}; nothing to undo")
            continue
        if not known and want.kind == "created-dir" and Path(want.target).exists():
            lines.append(f"ALREADY {want.target} exists; not ours to remove")
            continue
        change = known or want
        if want.kind == "git-config" and not known:
            change.previous = _git_get(want.target, want.key)
        kind.apply(change, settings)
        if not known:
            recorded.append(change)
        write(program, recorded)
        lines.append(f"ARMED {change.kind} {change.key or change.target}")
    write(program, recorded)
    return lines


def teardown(program: Program, settings: Settings) -> tuple[bool, list[str]]:
    changes = read(program)
    left: list[Change] = []
    lines = []
    for c in reversed(changes):
        kind = KINDS[c.kind]
        kind.undo(c, settings)
        if kind.gone(c, settings):
            lines.append(f"GONE {c.kind} {c.key or c.target}")
        else:
            lines.append(f"STILL {c.kind} {c.key or c.target}")
            left.insert(0, c)
    write(program, left, "ARMED" if left else "ARMED (torn down)")
    if not changes:
        lines.append("NOTHING armed")
    return not left, lines
