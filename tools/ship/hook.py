"""Claude Code PreToolUse hook: refuse Write, Edit, MultiEdit, NotebookEdit and `git commit` outside an
agent's own worktree and evidence folder.

Allowed: each held slice's worktree and its current evidence folder, and the program's review/ and
notes/ folders (reviewers and the coordinator write there). Everything else, the main checkout
included, is refused with exit code 2 and the reason on stderr, which Claude Code shows the agent.

The hook input does not say which agent is calling, so the allowed set is the union over held
slices: it stops writes to the main checkout and to anything outside the run, not one builder
writing into another held builder's worktree.

For Bash, a command is checked when it runs `git commit`; the folder is taken from `git -C <dir>`,
else from the last `cd`/`Set-Location`/`Push-Location` before it, else the hook's cwd.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

from ship import state as st
from ship.layout import Program
from ship.state import Status

FILE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
SPLIT = re.compile(r"&&|\|\||;|\||\n")
CD_WORDS = {"cd", "set-location", "push-location", "pushd", "sl"}


def _norm(path: str) -> str:
    if sys.platform == "win32":
        drive = re.match(r"^/([a-zA-Z])(/|$)", path)  # Git Bash /d/x -> D:/x
        if drive:
            path = f"{drive.group(1)}:/{path[3:]}"
    return os.path.normcase(os.path.abspath(path))


def inside(path: str, root: str) -> bool:
    p, r = _norm(path), _norm(root)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def allowed_roots(program: Program) -> tuple[list[str], list[str]]:
    """(worktrees, every writable root)."""
    state = st.load(program)
    worktrees = [str(state.worktree(s.id)) for s in state.slices.values() if s.status == Status.HELD]
    evidence = [str(program.evidence(s.id, s.attempts)) for s in state.slices.values() if s.status == Status.HELD]
    return worktrees, worktrees + evidence + [str(program.review_dir), str(program.notes_dir)]


def _unquote(token: str) -> str:
    return token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "'\"" else token


def commit_dirs(command: str, cwd: str) -> list[str]:
    """The folder each `git commit` in a shell command runs in."""
    here, found = cwd, []
    for segment in SPLIT.split(command):
        try:
            tokens = [_unquote(t) for t in shlex.split(segment, posix=False)]
        except ValueError:
            tokens = segment.split()
        if not tokens:
            continue
        if tokens[0].lower() in CD_WORDS and len(tokens) > 1:
            here = os.path.join(here, tokens[-1])
            continue
        names = [Path(t).name.lower() for t in tokens]
        if "git" not in names and "git.exe" not in names:
            continue
        i = max(names.index(n) for n in ("git", "git.exe") if n in names) + 1
        where = here
        while i < len(tokens) and tokens[i].startswith("-"):
            if tokens[i] in ("-C", "-c") and i + 1 < len(tokens):
                if tokens[i] == "-C":
                    where = os.path.join(where, tokens[i + 1])
                i += 2
            else:
                i += 1
        if i < len(tokens) and tokens[i] == "commit":
            found.append(where)
    return found


def decide(program: Program, event: dict) -> str | None:
    """None to allow, else the reason to refuse."""
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()
    if tool not in FILE_TOOLS and tool != "Bash":
        return None
    try:
        worktrees, roots = allowed_roots(program)
    except (OSError, ValueError, st.StateError) as exc:
        return f"ship hook: cannot read state.json ({exc}); refusing writes until it can"
    if tool in FILE_TOOLS:
        target = os.path.join(cwd, data.get(FILE_TOOLS[tool], ""))
        if any(inside(target, r) for r in roots):
            return None
        return f"ship hook: {tool} to {target} refused; write only in your worktree or evidence folder"
    for where in commit_dirs(data.get("command", ""), cwd):
        if not any(inside(where, w) for w in worktrees):
            return f"ship hook: git commit in {where} refused; commit only in your own slice worktree"
    return None


def main(program: Program, raw: str) -> int:
    try:
        event = json.loads(raw or "{}")
    except json.JSONDecodeError:
        print("ship hook: unreadable hook input; refusing", file=sys.stderr)
        return 2
    reason = decide(program, event)
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0
