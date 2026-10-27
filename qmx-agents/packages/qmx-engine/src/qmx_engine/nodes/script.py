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

A script never opens the Library: the host holds its single writer lock. `Served` is the one way
in. Before the child starts, the reads its node declares (`parameters.library_reads`) are answered
through the host's `LibraryPort` onto its stdin under `library`. When it finishes, the writes its
output lists under `library` are made through the same port, on the run's own ref and as the run,
whatever the write claims, and the output keeps only their receipts.
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
from typing import Final, cast

import keyring
from pydantic import JsonValue
from qmx_home import Layout

from qmx_engine.definition.lint import TOOL_KEY
from qmx_engine.ledger.redact import redact, register
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import EffectState, Failed, Look, NodeJob, NodeResult, Ok
from qmx_engine.ports.library import MAIN, EdgeName, JsonObject, LibraryPort, LibraryRefused
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

READS: Final = frozenset({"moved_to_main_after", "find_by_intent", "last_seq", "published"})
"""What a script node may ask the runner to read for it, by `parameters.library_reads`."""
ENGINE_EDGES: Final = frozenset({"produced-by", "run-of", "tested-by"})
"""Edges only the engine writes: a script that wrote one could pass its own object off as a passed
run's, and every other run's duplicate check would then serve it."""
STORE_FAILURES: Final = frozenset({"disk_full", "read_only_replica", "storage_failure"})
"""Refusals that mean the store took no write at all, so the node fails rather than reporting."""
BODIES: Final = "library"
"""The overlay folder a write's body file sits in."""

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


def slot_of(job: NodeJob) -> str:
    """`run:node:iteration:partition`: the attempt's key without the attempt, so a retry of the
    same slot finds what an earlier attempt wrote."""
    partition = "" if job.partition is None else str(job.partition)
    return f"{job.run_id}:{job.node_id}:{job.iteration}:{partition}"


def pick(value: JsonValue, part: str) -> JsonValue:
    if isinstance(value, dict):
        return value.get(part)
    if isinstance(value, list):
        return [pick(entry, part) for entry in value]
    return None


def argument(inputs: JsonValue, path: str) -> JsonValue:
    """The value at the dotted `path` in the node's `in` input, read from the first input row that
    holds its first name. A list on the way is read row by row, so `clippings.intent_key` is every
    clipping's key."""
    given = inputs.get("in") if isinstance(inputs, dict) else None
    rows = [given] if isinstance(given, dict) else given if isinstance(given, list) else []
    parts = path.split(".")
    value: JsonValue = next((r for r in rows if isinstance(r, dict) and parts[0] in r), None)
    for part in parts:
        value = pick(value, part)
    return value


def handle_of(value: JsonValue, handles: dict[str, str]) -> str | None:
    """The object a `$handle` names, or None when `value` is no handle of this step."""
    if isinstance(value, str) and value.startswith("$"):
        return handles.get(value[1:])
    return None


def refused_write(index: int, message: str) -> Failed:
    return failed("library_write_refused", f"write {index}: {message}", retryable=False)


@dataclass(frozen=True, slots=True)
class Served:
    """The Library reads and writes of one run's script nodes, through the host's port.

    Every write is an artifact or a link on `refs/runs/<run_id>` as `run:<run_id>`, so a script
    cannot write as another principal, onto another ref or for another run. Each artifact carries
    `metadata.write_key = <slot>:<index>`, and a write whose key is already on the run's ref is
    skipped, so a retried attempt writes nothing twice. Intent keys are the workflow item's own
    (`<workflow_item>|<key>`), so one workflow never shadows another's duplicate check.
    """

    library: LibraryPort
    run_id: str
    workflow_item: str

    def intent(self, key: str) -> str:
        return f"{self.workflow_item}|{key}"

    def reads(self, job: NodeJob) -> JsonObject | Failed:
        parameters = job.node_definition.get("parameters")
        declared = parameters.get("library_reads") if isinstance(parameters, dict) else None
        if declared is None:
            return {}
        if not isinstance(declared, dict):
            return failed("library_read_refused", "library_reads is not an object", retryable=False)
        answers: JsonObject = {}
        for name, ask in declared.items():
            if not isinstance(ask, dict) or len(ask) != 1:
                return failed(
                    "library_read_refused", f"read {name} names not one verb", retryable=False
                )
            [(verb, path)] = ask.items()
            if verb not in READS or not isinstance(path, str):
                return failed(
                    "library_read_refused", f"read {name}: {verb} is not a read", retryable=False
                )
            try:
                answers[name] = self.read(verb, argument(job.inputs, path) if path else None)
            except LibraryRefused as refused:
                return failed(refused.code, f"read {name}: {refused}", retryable=True)
        return answers

    def read(self, verb: str, given: JsonValue) -> JsonValue:
        match verb:
            case "moved_to_main_after":
                after = given if isinstance(given, int) and not isinstance(given, bool) else 0
                return [
                    {"seq": e.seq, "name": e.name, "object_id": e.object_id, "ref": e.ref}
                    for e in self.library.moved_to_main(after)
                ]
            case "last_seq":
                return self.library.last_seq()
            case "find_by_intent":
                keys = given if isinstance(given, list) else [given]
                return {key: self.held(key) for key in keys if isinstance(key, str)}
            case _:
                return self.published(given)

    def held(self, key: str) -> list[JsonValue]:
        """What holds `key` for this workflow, made by a passed live run on real models only: a
        test, fake or failed run's objects never answer another run's duplicate check."""
        return [
            object_id
            for object_id in self.library.find_by_intent(self.intent(key))
            if any(
                fields.get("status") == "passed"
                and fields.get("mode") == "live"
                and fields.get("fake") is not True
                for fields in (
                    self.library.get(edge.to_id).fields
                    for edge in self.library.edges(object_id, "produced-by")
                )
            )
        ]

    def published(self, item: JsonValue) -> JsonValue:
        if not isinstance(item, str) or not item:
            return None
        versions = self.library.objects(item, "workflow", MAIN)
        if not versions:
            return None
        newest = versions[-1]
        return {
            "item": item,
            "object_id": newest.object_id,
            "content_hash": newest.fields.get("content_hash"),
            "semver": self.library.annotation(newest.object_id, "semver"),
        }

    def writes(self, job: NodeJob, output: JsonValue, overlay: Path) -> JsonValue | Failed:
        """`output` with its `library` writes made and replaced by `library_written` receipts."""
        if not isinstance(output, dict) or "library" not in output:
            return output
        asked = output["library"]
        if not isinstance(asked, list):
            return refused_write(0, "library is not a list of writes")
        slot, handles = slot_of(job), dict[str, str]()
        receipts: list[JsonValue] = []
        for index, write in enumerate(asked):
            op = write.get("op") if isinstance(write, dict) else None
            if not isinstance(write, dict) or op not in ("put_artifact", "link"):
                return refused_write(index, "a write is put_artifact or link")
            made = (
                self.put(write, f"{slot}:{index}", index, overlay, handles)
                if op == "put_artifact"
                else self.link(write, index, handles)
            )
            if isinstance(made, Failed):
                return made
            receipts.append(made)
        kept: JsonObject = {key: value for key, value in output.items() if key != "library"}
        kept["library_written"] = receipts
        return kept

    def put(
        self,
        write: dict[str, JsonValue],
        write_key: str,
        index: int,
        overlay: Path,
        handles: dict[str, str],
    ) -> JsonObject | Failed:
        type_, body, metadata = write.get("type"), write.get("body"), write.get("metadata", {})
        handle, intent = write.get("as"), write.get("intent_key")
        if not isinstance(type_, str) or not type_ or not isinstance(metadata, dict):
            return refused_write(index, "an artifact names its type and its metadata object")
        if not isinstance(handle, str | None) or not isinstance(intent, str | None):
            return refused_write(index, "as and intent_key are text")
        root = (overlay / BODIES).resolve()
        path = (overlay / body).resolve() if isinstance(body, str) else root
        if not path.is_relative_to(root) or not path.is_file():
            return failed(
                "library_body_missing",
                f"write {index}: the body is not a file under {BODIES}/ in the overlay",
                retryable=False,
            )
        try:
            object_id = self.library.find_by_write_key(self.run_id, write_key)
            if object_id is None:
                object_id = self.library.put_artifact(
                    path.read_bytes(),
                    type_,
                    metadata | {"write_key": write_key},
                    run_id=self.run_id,
                    principal=f"run:{self.run_id}",
                    intent_key=None if intent is None else self.intent(intent),
                ).object_id
        except LibraryRefused as refused:
            state: EffectState = "after" if index else "before"
            message = f"write {index}: {refused}"
            return failed(refused.code, message, retryable=False, effect_state=state)
        if handle is not None:
            handles[handle] = object_id
        return {"op": "put_artifact", "handle": handle, "object_id": object_id, "refused": None}

    def link(
        self, write: dict[str, JsonValue], index: int, handles: dict[str, str]
    ) -> JsonObject | Failed:
        edge, source, target = write.get("edge"), write.get("from"), write.get("to")
        receipt: JsonObject = {"op": "link", "handle": None, "object_id": None, "edge": edge}
        receipt["to"] = target
        own = handle_of(source, handles)
        if own is None:
            return receipt | {"refused": "from is not a write of this step"}
        if not isinstance(edge, str) or edge in ENGINE_EDGES:
            return receipt | {"refused": f"{edge} is not an edge a script writes"}
        to = handle_of(target, handles) or target
        if not isinstance(to, str):
            return receipt | {"refused": "to names no object"}
        try:
            self.library.get(to)
            self.library.link(own, cast(EdgeName, edge), to, principal=f"run:{self.run_id}")
        except LibraryRefused as refused:
            if refused.code in STORE_FAILURES:
                message = f"write {index}: {refused}"
                return failed(refused.code, message, retryable=False, effect_state="after")
            return receipt | {"object_id": own, "to": to, "refused": refused.code}
        return receipt | {"object_id": own, "to": to, "refused": None}


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
    served: Served | None = None
    """The run's Library reads and writes; None when the engine has no Library."""

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

    async def run(
        self, job: NodeJob, parameter: str, library: JsonObject | None = None
    ) -> JsonValue | Failed:
        """The script's stdout as JSON, or why it failed. `library` holds the served reads, given
        on stdin beside the inputs."""
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
                stdin=json.dumps(given(job.inputs, library)).encode(),
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


def given(inputs: JsonValue, library: JsonObject | None) -> JsonValue:
    if not library:
        return inputs
    return {**inputs, "library": library} if isinstance(inputs, dict) else {"library": library}


def unserved() -> Failed:
    return failed(
        "library_unserved",
        "the script reads or writes the Library and this engine has none",
        retryable=False,
    )


class Script:
    """`parameters.artifacts` may list files the script leaves in its overlay; they are
    returned as the attempt's artifacts and committed to `work/` with its declared outputs, and a
    missing one fails it. An entry ending in `/` names a folder: every file under it is an
    artifact, so a script can leave one file per card."""

    def __init__(self, host: HostScript) -> None:
        self.host = host

    async def run(self, job: NodeJob) -> NodeResult:
        served = self.host.served
        parameters = job.node_definition.get("parameters")
        if served is None and isinstance(parameters, dict) and "library_reads" in parameters:
            return unserved()
        reads = {} if served is None else served.reads(job)
        if isinstance(reads, Failed):
            return reads
        found = await self.host.run(job, "script", reads or None)
        if isinstance(found, Failed):
            return found
        if isinstance(found, dict) and "library" in found:
            if served is None:
                return unserved()
            found = served.writes(job, found, RunZone(Path(job.workspace or ".")).overlay(job))
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
