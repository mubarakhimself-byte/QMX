"""The `script` node, and the host-tier process the script family shares (AD-24).

A trusted script runs as `python -I` in a subprocess, from the run's hash-checked `code/` copy.
Its cwd is the attempt's overlay (AD-51), its inputs arrive as JSON on stdin, and its stdout,
parsed as JSON, is its output on `main`; a first line starting `[QMX_FAILURE]` fails it instead,
with that line's reason, whatever the exit code.
Its environment is built from an allow-list with `qma.boot`'s banned fragments, so no provider
key, no `CLAUDE_CONFIG_DIR`, no plan path and no home path reaches it, plus the run context
(`QMX_RUN_ID`, `QMX_MODE`, `QMX_FAKE`, `QMX_NOW`, `QMX_WORK`, `QMX_WORK_SHARED`, `QMX_CODE` and the
rest) and the value of each `qmx/tool/<name>` key the node declares, registered with the redactor
first (AD-37).

The process joins the engine's Job object, so it dies with the engine, and its tree is killed on
cancel. A node script has no run timeout (AD-40): the stuck detector reads its process through
`look` and stops it only after `timeout.script.idle` with no CPU and no IO, so a long backtest
runs on. A trigger's own check script keeps a timeout.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import keyring
from pydantic import JsonValue
from qmx_home import Layout

from qmx_engine.definition.lint import TOOL_KEY
from qmx_engine.ledger.redact import redact, register
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import EffectState, Failed, Look, NodeJob, NodeResult, Ok
from qmx_engine.workers.effects import idempotency_key
from qmx_engine.workers.local import contain, forget, kill_tree, record
from qmx_engine.workers.zones import RunZone, digest

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
TOOL_ENV: Final = re.compile(r"[A-Z][A-Z0-9_]*")
MESSAGE_LIMIT: Final = 300
FAILURE: Final = "[QMX_FAILURE]"
"""A first stdout line starting with this declares the script failed, with the rest as why."""

type Resolve = Callable[[str], str | None]


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
    that points at or under one of `banned_values` (the home and the plan login's folder), plus
    the idempotency key. Paths are compared in one spelling, so a forward-slash or
    doubled-separator form of a banned path is caught too."""
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


def model_caches(zone: RunZone) -> dict[str, str]:
    """Where a script's downloads go when its zone sits in a QMX folder's `cache/zones/`: the
    folder's `cache/models/` (design 62 A3), so Docling, torch and pip stop landing in his
    profile. None for a zone elsewhere, such as a remote worker's."""
    parents = zone.root.resolve().parents
    layout = Layout(parents[2]) if len(parents) > 2 else None
    if layout is None or not layout.label.is_file():
        return {}
    models = layout.cache / "models"
    return {
        "HF_HOME": str(models / "huggingface"),
        "TORCH_HOME": str(models / "torch"),
        "XDG_CACHE_HOME": str(models / "xdg"),
        "PIP_CACHE_DIR": str(models / "pip"),
    }


def keyring_secret(ref: str) -> str | None:
    return keyring.get_password(ref, ref.removeprefix("qmx/"))


@dataclass(frozen=True, slots=True)
class Done:
    code: int | None
    """None when the timeout killed it."""
    stdout: bytes
    stderr: bytes


async def run_process(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdin: bytes,
    timeout: float | None,
    started: Callable[[int], None] | None = None,
) -> Done:
    """Run to exit, or kill the whole tree at `timeout` or when the awaiting task is cancelled.
    The process joins the engine's Job object, then `started` is told its id."""
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
    contain(process.pid)
    if started is not None:
        started(process.pid)
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
    """Redacted before it is cut to its tail, so a cut never leaves half a key no shape matches."""
    message = redact(message)[-MESSAGE_LIMIT:]
    return Failed(code, message, signature(code, message), retryable, effect_state)


@dataclass(frozen=True, slots=True)
class HostScript:
    """What every script-family executor of one run shares: the folder its scripts come from
    (the run's `code/` copy, hashed in `manifest`), its timeout (None for a node's script), the
    values no script's environment may point at, whether the run is fake, and how a tool key
    is read from the keyring."""

    folder: Path
    timeout_seconds: float | None
    banned_values: tuple[str, ...]
    fake: bool = False
    manifest: Mapping[str, str] | None = None
    resolve: Resolve = keyring_secret
    processes: dict[str, int] = field(default_factory=dict[str, int])
    """The running script's process id, by attempt idempotency key."""

    def look(self, key: str) -> Look:
        pid = self.processes.get(key)
        return Look(0, pid=pid) if pid is not None else Look(0, waiting=True)

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
        if self.manifest is not None:
            relative = path.relative_to(root).as_posix()
            if self.manifest.get(relative) != digest(path):
                return failed(
                    "code_changed", "the script no longer matches the run's copy", retryable=False
                )
        return path

    def tool_keys(self, job: NodeJob) -> dict[str, str] | Failed:
        """Each declared `qmx/tool/<name>` key under the name the node gives it, registered
        with the redactor before the script can print it."""
        declared = job.node_definition.get("credentials")
        found: dict[str, str] = {}
        for name, ref in declared.items() if isinstance(declared, dict) else ():
            if (
                not isinstance(ref, str)
                or not TOOL_KEY.fullmatch(ref)
                or not TOOL_ENV.fullmatch(name)
                or name.startswith("QMX_")
                or any(f in name for f in BANNED_FRAGMENTS)
            ):
                return failed(
                    "credential_refused",
                    f"{name} is not a tool key a script may hold",
                    retryable=False,
                )
            value = self.resolve(ref)
            if not value:
                return failed("credential_missing", f"{ref} is not in the keyring", retryable=False)
            try:
                register(ref, value)
            except ValueError:
                return failed("credential_short", f"{ref} is too short to redact", retryable=False)
            found[name] = value
        return found

    def context(self, job: NodeJob, zone: RunZone) -> dict[str, str]:
        return model_caches(zone) | {
            "QMX_RUN_ID": job.run_id,
            "QMX_NODE_ID": job.node_id,
            "QMX_ATTEMPT": str(job.attempt),
            "QMX_MODE": job.mode,
            "QMX_FAKE": "1" if self.fake else "0",
            "QMX_NOW": job.now or "",
            "QMX_WORK": str(zone.overlay(job)),
            "QMX_WORK_SHARED": str(zone.work),
            "QMX_CODE": str(self.folder),
        }

    async def run(self, job: NodeJob, parameter: str) -> JsonValue | Failed:
        """The script's stdout as JSON, or why it failed."""
        path = self.path(job, parameter)
        if isinstance(path, Failed):
            return path
        if job.workspace is None:
            return failed("no_workspace", "the job names no write zone", retryable=False)
        keys = self.tool_keys(job)
        if isinstance(keys, Failed):
            return keys
        zone = RunZone(Path(job.workspace))
        cwd = zone.overlay(job)
        cwd.mkdir(parents=True, exist_ok=True)
        env = script_env(os.environ, self.banned_values, idempotency_key(job))
        key = job.idempotency_key

        def started(pid: int) -> None:
            self.processes[key] = pid
            record(zone, job, pid)

        try:
            done = await run_process(
                [sys.executable, "-I", str(path)],
                cwd=cwd,
                env=env | self.context(job, zone) | keys,
                stdin=json.dumps(job.inputs).encode(),
                timeout=self.timeout_seconds,
                started=started,
            )
        finally:
            self.processes.pop(key, None)
            forget(zone, job)
        if done.code is None:
            return failed(
                "timeout",
                f"the script ran past its {self.timeout_seconds:g} s timeout",
                retryable=True,
                effect_state="unknown",
            )
        text = done.stdout.decode("utf-8", "replace").strip()
        if text.startswith(FAILURE):
            why = text.partition("\n")[0].removeprefix(FAILURE).strip()
            return failed("qmx_failure", why or "the script declared failure", retryable=False)
        if done.code != 0:
            tail = done.stderr.decode("utf-8", "replace").strip()
            return failed("script_exit", f"exit {done.code}: {tail}", retryable=True)
        try:
            return json.loads(text) if text else None
        except json.JSONDecodeError:
            return failed("script_output", "stdout is not JSON", retryable=False)


class Script:
    """`parameters.artifacts` may list files the script leaves in its overlay; they are
    returned as the attempt's artifacts and committed to `work/` with its declared outputs, and a
    missing one fails it. An entry ending in `/` names a folder: every file under it is an
    artifact, so a script can leave one file per card."""

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
        overlay = RunZone(Path(job.workspace or ".")).overlay(job).resolve()
        files: list[str] = []
        for artifact in artifacts:
            path = (overlay / artifact).resolve()
            inside = path.is_relative_to(overlay)
            if inside and artifact.endswith("/") and path.is_dir():
                under = sorted(p for p in path.rglob("*") if p.is_file())
                files += [p.relative_to(overlay).as_posix() for p in under]
            elif inside and path.is_file():
                files.append(artifact)
            else:
                return failed(
                    "artifact_missing", "a listed artifact is not in the zone", retryable=False
                )
        return Ok({"main": found}, tuple(files))
