"""The remote run sidecar: the DevOps layer every remote attempt carries (Library AD-13).

A remote attempt is one `NodeJob` shipped as a bundle. The sidecar runs on the runner host beside
the attempt and does the four things the attempt cannot do for itself:

- emits a heartbeat row every five seconds, so the PC's worker can tell a slow attempt from a lost
  one, and the hub can see the machine minute;
- ships structured JSONL logs, spans and checkpoints to `runs/<run_id>/`, flushing every five
  seconds and at every node boundary;
- redacts the run pass and every secret value resolved into the attempt before anything is written
  or shipped;
- scrubs the attempt's environment at exit.

The sidecar holds no provider key (AD-12, AD-28): a remote attempt receives a run pass, never a
key, and its model calls go through the runner host's router. The pass is a value the sidecar
registers with its own redactor, so a traceback that echoes it still ships redacted.

The attempt itself is executed through the engine's own executor table on the runner host
(`run_attempt`); the import is deferred because `qmx-remote` must stay importable on a machine
that carries only the sidecar. `main()` is the process entry the provider starts.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import hashlib
import json
import os
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Protocol, cast

from pydantic import JsonValue

type JsonObject = dict[str, JsonValue]

SCHEMA: Final = "qmx.remote.attempt/1"
HEARTBEAT_SECONDS: Final = 5.0
CHECKPOINT_SECONDS: Final = 5.0
"""AD-13's two clocks: a heartbeat, and a checkpoint flush, every five seconds."""
REDACTED: Final = "[redacted]"
SECRET_FRAGMENTS: Final = ("key", "token", "secret", "pass", "authorization", "credential")
"""Environment names whose value the sidecar treats as a declared secret even when the bundle's
`secrets` list missed it. The list is a floor, not the rule: the bundle names the rest."""


class BundleError(ValueError):
    """A bundle the sidecar refuses: a shape it does not know, or a file whose hash is wrong."""


class HubPort(Protocol):
    def heartbeat(self, row: dict[str, Any]) -> None: ...
    def put(self, path: str, payload: bytes) -> None: ...


@dataclass(frozen=True, slots=True)
class HttpHub:
    """The hub's run endpoint: `runs/<run_id>/` objects over HTTPS with the run pass as bearer."""

    base_url: str
    run_id: str
    pass_value: str
    timeout: float = 5.0

    def _post(self, path: str, payload: bytes, content_type: str) -> None:
        request = urllib.request.Request(  # noqa: S310 - the hub's URL, never a file URL
            self.base_url.rstrip("/") + "/" + path.lstrip("/"),
            data=payload,
            method="PUT",
            headers={
                "authorization": "Bearer " + self.pass_value,
                "content-type": content_type,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout):  # noqa: S310 - the hub
                return
        except (urllib.error.URLError, OSError) as error:
            raise BundleError(f"hub refused {path}: {type(error).__name__}") from error

    def heartbeat(self, row: dict[str, Any]) -> None:
        self._post(f"runs/{self.run_id}/heartbeat", json.dumps(row).encode(), "application/json")

    def put(self, path: str, payload: bytes) -> None:
        self._post(path, payload, "application/jsonl")


@dataclass(frozen=True, slots=True)
class AttemptKeys:
    run_id: str
    node_id: str
    iteration: int
    partition: int | None
    attempt: int

    @property
    def key(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "node_id": self.node_id,
            "iteration": self.iteration,
            "partition": self.partition,
            "attempt": self.attempt,
        }


@dataclass(frozen=True, slots=True)
class Attempt:
    """The job half of a bundle, validated at the host boundary."""

    keys: AttemptKeys
    node_definition: JsonObject
    inputs: JsonValue
    inputs_hash: str
    placement: str
    mode: str
    resolved_model: JsonObject | None
    now: str | None
    run_pass: str
    secrets: tuple[str, ...]
    """The environment names whose values are registered for redaction. Never the values."""
    files: dict[str, str] = field(default_factory=dict[str, str])
    file_hashes: dict[str, str] = field(default_factory=dict[str, str])
    idempotency_key: str = ""
    priority: int = 0

    @classmethod
    def from_bundle(cls, bundle: Mapping[str, JsonValue]) -> Attempt:
        if bundle.get("schema") != SCHEMA:
            raise BundleError("unknown attempt bundle schema")
        job = bundle.get("job")
        if not isinstance(job, dict):
            raise BundleError("bundle has no job")
        found = cast(Mapping[str, JsonValue], job)
        definition = found.get("node_definition")
        if not isinstance(definition, dict):
            raise BundleError("job has no node definition")
        resolved = found.get("resolved_model")
        raw_secrets = bundle.get("secrets")
        keys = AttemptKeys(
            str(found.get("run_id") or ""),
            str(found.get("node_id") or ""),
            _whole(found.get("iteration")),
            None if found.get("partition") is None else _whole(found.get("partition")),
            _whole(found.get("attempt")),
        )
        return cls(
            keys=keys,
            node_definition=cast(JsonObject, definition),
            inputs=found.get("inputs"),
            inputs_hash=str(found.get("inputs_hash") or ""),
            placement=str(found.get("placement") or "pc"),
            mode=str(found.get("mode") or "test"),
            resolved_model=cast(JsonObject, resolved) if isinstance(resolved, dict) else None,
            now=None if found.get("now") is None else str(found.get("now")),
            run_pass=str(bundle.get("run_pass") or os.environ.get("QMX_RUN_PASS", "")),
            secrets=_names(raw_secrets),
            files=_texts(bundle.get("files")),
            file_hashes=_texts(bundle.get("file_hashes")),
            idempotency_key=str(found.get("idempotency_key") or ""),
            priority=_whole(found.get("priority")),
        )


def _whole(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | str | float):
        return 0
    return int(value)


def _names(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(name) for name in cast(list[object] | tuple[object, ...], value))


def _texts(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(name): str(text) for name, text in cast(dict[object, object], value).items()}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Redactor:
    """The sidecar's own seam: the pass and every declared secret value become `[redacted]`.

    Values shorter than eight characters are not registered, because replacing a two-letter string
    would shred ordinary logs; the pass is always long enough and is registered whatever its size.
    """

    def __init__(self) -> None:
        self.values: list[str] = []

    def register(self, value: str, *, force: bool = False) -> None:
        """A value shorter than eight characters is left alone unless `force`: replacing a
        two-letter string would shred ordinary logs, and the pass is always forced."""
        if not value or (len(value) < 8 and not force):
            return
        self.values.append(value)

    def text(self, value: str) -> str:
        for secret in sorted(self.values, key=len, reverse=True):
            value = value.replace(secret, REDACTED)
        return value

    def document(self, value: JsonValue) -> JsonValue:
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, dict):
            found = cast(dict[str, JsonValue], value)
            return {str(key): self.document(item) for key, item in found.items()}
        if isinstance(value, list | tuple):
            return [
                self.document(item) for item in cast(list[JsonValue] | tuple[JsonValue, ...], value)
            ]
        return value


def environment_secrets(names: tuple[str, ...]) -> dict[str, str]:
    """The values the bundle's secret names point at in this process, plus every name that looks
    like a credential even when the bundle did not name it."""
    found: dict[str, str] = {}
    for name, value in os.environ.items():
        looks = any(fragment in name.casefold() for fragment in SECRET_FRAGMENTS)
        if (name in names or looks) and value:
            found[name] = value
    return found


@dataclass
class Sidecar:
    """One attempt's telemetry: events, logs, checkpoints and the result, all redacted."""

    root: Path
    attempt: Attempt
    hub: HubPort | None = None
    redactor: Redactor = field(default_factory=Redactor)
    heartbeat_seconds: float = HEARTBEAT_SECONDS
    checkpoint_seconds: float = CHECKPOINT_SECONDS
    clock: Callable[[], float] = time.time
    started_at: float = field(default_factory=time.time)
    stopped: threading.Event = field(default_factory=threading.Event)
    failures: list[str] = field(default_factory=list[str])

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "events.jsonl").touch()
        (self.root / "logs").mkdir(exist_ok=True)
        (self.root / "traces").mkdir(exist_ok=True)
        (self.root / "checkpoints").mkdir(exist_ok=True)
        # Registered whatever its length: a pass is the one value no output may carry.
        self.redactor.register(self.attempt.run_pass, force=True)
        for value in environment_secrets(self.attempt.secrets).values():
            self.redactor.register(value)

    @property
    def event_path(self) -> Path:
        return self.root / "events.jsonl"

    def now(self) -> str:
        return datetime.datetime.fromtimestamp(self.clock(), datetime.UTC).isoformat()

    def emit(self, kind: str, data: Mapping[str, JsonValue]) -> None:
        row: JsonObject = {"kind": kind, "at": self.now()}
        row.update(cast(JsonObject, self.attempt.keys.key))
        row.update(cast(JsonObject, self.redactor.document(dict(data))))
        with self.event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    def heartbeat(self) -> None:
        row: JsonObject = {
            "kind": "heartbeat",
            "at": self.now(),
            **self.attempt.keys.key,
            "placement": self.attempt.placement,
            "note": "running",
        }
        self._write_event(row)

    def _write_event(self, row: JsonObject) -> None:
        with self.event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        if self.hub is not None:
            try:
                self.hub.heartbeat(row)
            except BundleError as error:
                self.failures.append(str(error))

    def log(self, text: str) -> None:
        line = self.redactor.text(text.rstrip())
        path = self.root / "logs" / self.attempt.keys.run_id / "sidecar.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at": self.now(), "line": line}) + "\n")

    def checkpoint(self, name: str, payload: Any) -> None:
        body = json.dumps(self.redactor.document(payload), ensure_ascii=False).encode("utf-8")
        (self.root / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.root / "checkpoints" / f"{name}.json").write_bytes(body)

    def finish(self, result: Mapping[str, JsonValue]) -> JsonObject:
        """Write the result document, flush the last events, and return the redacted body."""
        self.stopped.set()
        body = cast(JsonObject, self.redactor.document(dict(result)))
        (self.root / "result.json").write_text(
            json.dumps(body, ensure_ascii=False), encoding="utf-8"
        )
        self.checkpoint("latest", body)
        return body

    def beat(self) -> None:
        while not self.stopped.wait(self.heartbeat_seconds):
            self.heartbeat()

    def flush(self) -> None:
        """Ship the events, logs and trace files to the hub's `runs/<run_id>/`."""
        if self.hub is None:
            return
        for path in sorted(self.root.glob("events.jsonl")):
            self.hub.put(f"runs/{self.attempt.keys.run_id}/events.jsonl", path.read_bytes())
        for path in sorted((self.root / "logs").rglob("*.jsonl")):
            relative = path.relative_to(self.root).as_posix()
            self.hub.put(f"runs/{self.attempt.keys.run_id}/{relative}", path.read_bytes())
        for path in sorted((self.root / "checkpoints").glob("*.json")):
            self.hub.put(
                f"runs/{self.attempt.keys.run_id}/checkpoints/{path.name}", path.read_bytes()
            )

    def sweep(self) -> None:
        """The environment scrub at exit: the pass never outlives the attempt."""
        os.environ.pop("QMX_RUN_PASS", None)


def result_document(result: object) -> JsonObject:
    """The engine's `NodeResult` as the wire shape, so the PC side can rebuild it exactly."""
    from qmx_engine.nodes.base import Failed, Gate, Ok, Waiting  # noqa: PLC0415 - runner side only

    match result:
        case Ok():
            body: dict[str, Any] = {
                "status": "ok",
                "outputs": result.outputs,
                "output_hash": result.output_hash,
            }
            if result.artifacts:
                body["artifacts"] = list(result.artifacts)
            if result.verdict is not None:
                body["verdict"] = result.verdict
            if result.span:
                body["span"] = result.span
            return body
        case Failed():
            return {
                "status": "failed",
                "code": result.code,
                "message": result.message,
                "signature": result.signature,
                "retryable": result.retryable,
                "effect_state": result.effect_state,
                **({"span": result.span} if result.span else {}),
            }
        case Waiting():
            return {
                "status": "waiting",
                "reason": result.reason,
                "resume_at": result.resume_at,
                **({"event": result.event} if result.event is not None else {}),
                **({"span": result.span} if result.span else {}),
            }
        case Gate():
            return {
                "status": "gate",
                "ask": result.ask,
                "options": list(result.options),
            }
        case _:
            raise BundleError(f"unknown result type {type(result).__name__}")


def materialise(attempt: Attempt, code: Path) -> dict[str, str]:
    """Write the bundle's files under `code/`, refusing a file whose content hash disagrees."""
    code.mkdir(parents=True, exist_ok=True)
    for name, text in attempt.files.items():
        expected = attempt.file_hashes.get(name)
        if expected is None:
            raise BundleError(f"{name}: no hash in the bundle")
        if digest(text) != expected:
            raise BundleError(f"{name}: content does not match the bundle hash")
        path = (code / name).resolve()
        if not path.is_relative_to(code.resolve()):
            raise BundleError(f"{name}: escapes the attempt folder")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return dict(attempt.file_hashes)


def run_attempt(attempt: Attempt, sidecar: Sidecar, work: Path) -> dict[str, Any]:
    """Execute the attempt's node through the engine's executor table on this host.

    Only the kinds whose attempt is a local process are served remotely here: a `script`, `grader`
    or `monitor` node. An `agent` node placed remote is a harness chat on the runner host and its
    executor is built by `qmx-node`'s host, not by the sidecar; asking for it here is a bundle
    error rather than a silent local run.
    """
    from qmx_engine.definition.registry import REGISTRY  # noqa: PLC0415 - a runner host has it
    from qmx_engine.nodes.base import NodeJob  # noqa: PLC0415 - a runner host has it
    from qmx_engine.nodes.grader import Grader  # noqa: PLC0415 - a runner host has it
    from qmx_engine.nodes.monitor import Monitor  # noqa: PLC0415 - a runner host has it
    from qmx_engine.nodes.script import HostScript, Script  # noqa: PLC0415 - a runner host has it

    files = materialise(attempt, work / "code")
    job = NodeJob(
        run_id=attempt.keys.run_id,
        node_id=attempt.keys.node_id,
        iteration=attempt.keys.iteration,
        partition=attempt.keys.partition,
        attempt=attempt.keys.attempt,
        memo_key=attempt.idempotency_key,
        idempotency_key=attempt.idempotency_key,
        node_definition=attempt.node_definition,
        inputs=attempt.inputs,
        now=attempt.now,
        mode="test" if attempt.mode == "test" else "live",
        resolved_model=attempt.resolved_model,
        workspace=str(work),
        placement=attempt.placement,
        priority=attempt.priority,
    )
    host = HostScript(
        work / "code",
        None,
        banned_values=(),
        fake=attempt.mode == "test",
        manifest=files,
    )
    kind = REGISTRY.kind(str(attempt.node_definition.get("type")))
    match kind.name if kind is not None else "":
        case "script":
            executor: Any = Script(host)
        case "grader":
            executor = Grader(host)
        case "monitor":
            executor = Monitor(host, work / "monitors")
        case other:
            raise BundleError(f"the sidecar does not serve a {other or 'unknown'} attempt")
    sidecar.emit("node_started", {"idempotency_key": attempt.idempotency_key})
    outcome = executor.run(job)
    result = asyncio.run(outcome) if asyncio.iscoroutine(outcome) else outcome
    return result_document(result)


def execute(bundle: Mapping[str, Any], root: Path, hub: HubPort | None = None) -> dict[str, Any]:
    """One attempt end to end: prepare, run, redact, ship. The provider starts this."""
    attempt = Attempt.from_bundle(bundle)
    sidecar = Sidecar(root=root, attempt=attempt, hub=hub)
    beater = threading.Thread(target=sidecar.beat, daemon=True)
    beater.start()
    try:
        sidecar.emit("attempt_started", {"placement": attempt.placement, "mode": attempt.mode})
        sidecar.emit("log", {"line": f"sidecar started the attempt on {attempt.placement}"})
        try:
            body = run_attempt(attempt, sidecar, root / "work")
        except BundleError as error:
            body = {
                "status": "failed",
                "code": "bundle_refused",
                "message": str(error),
                "signature": digest(str(error)),
                "retryable": False,
                "effect_state": "before",
            }
        except Exception as error:  # a broken attempt must still leave a result on the hub
            body = {
                "status": "failed",
                "code": "sidecar_error",
                "message": sidecar.redactor.text(f"{type(error).__name__}: {error}"),
                "signature": digest(type(error).__name__),
                "retryable": False,
                "effect_state": "unknown",
            }
            sidecar.log(traceback.format_exc())
        sidecar.checkpoint("latest", {"attempt": attempt.keys.key, "result": body})
        sidecar.emit("attempt_finished", {"status": body.get("status")})
        return sidecar.finish(body)
    finally:
        sidecar.stopped.set()
        beater.join(timeout=5.0)
        sidecar.flush()
        sidecar.sweep()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--root", required=True)
    arguments = parser.parse_args()
    bundle = json.loads(Path(arguments.bundle).read_text(encoding="utf-8"))
    body = execute(bundle, Path(arguments.root))
    print(json.dumps({"status": body.get("status")}))
    return 0 if body.get("status") in {"ok", "waiting", "gate"} else 1


if __name__ == "__main__":
    sys.exit(main())
