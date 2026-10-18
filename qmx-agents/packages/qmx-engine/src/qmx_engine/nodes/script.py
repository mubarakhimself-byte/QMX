"""The `script` node, and the host-tier process the script family shares (AD-24).

A trusted script from the workflow folder runs as `python -I` in a subprocess. Its environment is
built from an allow-list with `qma.boot`'s banned fragments, so no provider key, no
`CLAUDE_CONFIG_DIR` and no plan path reaches it. Its cwd is the run's write zone, its inputs
arrive as JSON on stdin, and its stdout, parsed as JSON, is its output on `main`. The process tree
is killed on timeout and on cancel. A node that declares credentials is refused: resolving a
`qmx/*` ref into a host script is not built yet.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import signal
import subprocess
import sys
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import JsonValue

from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import EffectState, Failed, NodeJob, NodeResult, Ok
from qmx_engine.workers.effects import idempotency_key

BANNED_FRAGMENTS: Final = ("PROXY", "ANTHROPIC", "OPENAI", "AWS", "NODE_", "SSL_", "CLAUDE")
"""`qma.boot.BANNED_FRAGMENTS`; `tests/test_script.py` holds the two equal."""
KEEP_NAMES: Final = frozenset(
    {
        "PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "USER", "LOGNAME", "HOME",
        "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT",
        "USERPROFILE", "USERNAME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
        "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "OS",
        "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS",
    }
)  # fmt: skip
IDEMPOTENCY_ENV: Final = "QMX_IDEMPOTENCY_KEY"
MESSAGE_LIMIT: Final = 300


def canonical(path: str) -> str:
    return os.path.normcase(os.path.normpath(path.strip())).rstrip("\\/")


def points_under(value: str, banned: str) -> bool:
    """True when one `os.pathsep` entry of `value` is `banned` or sits under it, or when the whole
    value, with its separators collapsed, holds it (a path inside an option, say)."""
    for entry in value.split(os.pathsep):
        if entry.strip():
            path = canonical(entry)
            if path == banned or path.startswith(banned + os.sep):
                return True
    collapsed = os.path.normcase(re.sub(r"[\\/]+", lambda _: os.sep, value))
    return banned in collapsed


def script_env(
    environ: Mapping[str, str], banned_values: Collection[str], key: str | None = None
) -> dict[str, str]:
    """The allow-listed names from `environ`, minus any name with a banned fragment and any value
    that points at or under one of `banned_values` (the plan login's folder), plus the
    idempotency key. Paths are compared in one spelling, so a forward-slash or doubled-separator
    form of a banned path is caught too."""
    banned = [canonical(path) for path in banned_values if path.strip()]
    env: dict[str, str] = {}
    for name, value in environ.items():
        upper = name.upper()
        if upper not in KEEP_NAMES or any(f in upper for f in BANNED_FRAGMENTS):
            continue
        if any(points_under(value, path) for path in banned):
            continue
        env[name] = value
    if key is not None:
        env[IDEMPOTENCY_ENV] = key
    return env


def kill_tree(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],  # noqa: S607
            capture_output=True,
            check=False,
        )
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(pid, signal.SIGKILL)


@dataclass(frozen=True, slots=True)
class Done:
    code: int | None
    """None when the timeout killed it."""
    stdout: bytes
    stderr: bytes


async def run_process(
    argv: list[str], *, cwd: Path, env: dict[str, str], stdin: bytes, timeout: float
) -> Done:
    """Run to exit, or kill the whole tree at `timeout` or when the awaiting task is cancelled."""
    windows = sys.platform == "win32"
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if windows else 0,
        start_new_session=not windows,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(stdin), timeout)
    except TimeoutError:
        kill_tree(process.pid)
        await process.wait()
        return Done(None, b"", b"")
    except asyncio.CancelledError:
        kill_tree(process.pid)
        await asyncio.shield(process.wait())
        raise
    return Done(process.returncode, stdout, stderr)


def failed(
    code: str, message: str, *, retryable: bool, effect_state: EffectState = "before"
) -> Failed:
    message = message[-MESSAGE_LIMIT:]
    return Failed(code, message, signature(code, message), retryable, effect_state)


@dataclass(frozen=True, slots=True)
class HostScript:
    """What every script-family executor of one run shares: the workflow folder its scripts come
    from, the default timeout and the values no script may see."""

    folder: Path
    timeout_seconds: float
    banned_values: tuple[str, ...]

    def path(self, job: NodeJob, parameter: str) -> Path | Failed:
        parameters = job.node_definition.get("parameters")
        ref = parameters.get(parameter) if isinstance(parameters, dict) else None
        if not isinstance(ref, str):
            return failed(
                "script_missing", f"parameters.{parameter} is not a path", retryable=False
            )
        root = self.folder.resolve()
        path = (root / ref).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            return failed(
                "script_missing", "the script is not a file in the folder", retryable=False
            )
        return path

    async def run(self, job: NodeJob, parameter: str) -> JsonValue | Failed:
        """The script's stdout as JSON, or why it failed."""
        if job.node_definition.get("credentials"):
            return failed(
                "credentials_unsupported", "a host script gets no credentials yet", retryable=False
            )
        path = self.path(job, parameter)
        if isinstance(path, Failed):
            return path
        if job.workspace is None:
            return failed("no_workspace", "the job names no write zone", retryable=False)
        timeouts = job.timeouts or {}
        limit = timeouts.get("run_seconds")
        seconds = float(limit) if isinstance(limit, int | float) else self.timeout_seconds
        done = await run_process(
            [sys.executable, "-I", str(path)],
            cwd=Path(job.workspace),
            env=script_env(os.environ, self.banned_values, idempotency_key(job)),
            stdin=json.dumps(job.inputs).encode(),
            timeout=seconds,
        )
        if done.code is None:
            return failed(
                "timeout",
                f"the script ran past its {seconds:g} s timeout",
                retryable=True,
                effect_state="unknown",
            )
        if done.code != 0:
            tail = done.stderr.decode("utf-8", "replace").strip()
            return failed("script_exit", f"exit {done.code}: {tail}", retryable=True)
        text = done.stdout.decode("utf-8", "replace").strip()
        try:
            return json.loads(text) if text else None
        except json.JSONDecodeError:
            return failed("script_output", "stdout is not JSON", retryable=False)


class Script:
    """`parameters.artifacts` may list files the script leaves in the zone; they are returned as
    the attempt's artifacts, and a missing one fails it. An entry ending in `/` names a folder:
    every file under it is an artifact, so a script can leave one file per card."""

    def __init__(self, host: HostScript) -> None:
        self.host = host

    async def run(self, job: NodeJob) -> NodeResult:
        found = await self.host.run(job, "script")
        if isinstance(found, Failed):
            return found
        parameters = job.node_definition.get("parameters")
        listed = parameters.get("artifacts") if isinstance(parameters, dict) else None
        artifacts = (
            tuple(a for a in listed if isinstance(a, str)) if isinstance(listed, list) else ()
        )
        zone = Path(job.workspace or ".").resolve()
        files: list[str] = []
        for artifact in artifacts:
            path = (zone / artifact).resolve()
            inside = path.is_relative_to(zone)
            if inside and artifact.endswith("/") and path.is_dir():
                under = sorted(p for p in path.rglob("*") if p.is_file())
                files += [p.relative_to(zone).as_posix() for p in under]
            elif inside and path.is_file():
                files.append(artifact)
            else:
                return failed(
                    "artifact_missing", "a listed artifact is not in the zone", retryable=False
                )
        return Ok({"main": found}, tuple(files))
