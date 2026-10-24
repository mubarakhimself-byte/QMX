"""The remote `WorkerPort` adapter (AD-20, AD-25, AD-30): a placed attempt runs on its machine.

The local adapter holds the runner's executor table; this one does not, and no executor crosses the
port. It ships the attempt as a bundle, which carries the node's definition slice, its inputs and
their hash, the code files with their hashes, the placement and its resources, and a **run pass**
minted by the owning engine. It never carries a key: its model calls go through the runner host's
router, and `Library AD-12` admits only `QMX_RUN_PASS` into `ComputeProvider.start`.

The bundle lands on the machine under `qmx-run-sidecar` (`qmx_remote.sidecar`), which executes the
attempt through that host's executor table, heartbeats every five seconds, and ships events, logs
and checkpoints to the Hub's `runs/<run_id>/`. This adapter polls the gateway port (the Hub, or the
same directory in a test) and turns each row into a ledger event. The result comes back as
artifacts by hash plus the attempt's ending, which the runner writes.

A heartbeat that stops before a result arrives is not a failure with an unknown outcome guessed
either way: the attempt folds `effect_state: unknown` and retries by its effect class (AD-8). A
machine that is merely slow keeps beating, so the two cases stay apart.

`PlacementWorker` is a `LocalWorker` subclass because the engine's type says so; it routes by the
job's placement, which the runner set from `runs_on` and the data's locality (AD-70), and defers
every other attempt to the local table.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol, cast

from qmx_ledger.journal import fingerprint
from qmx_remote.models import Document, RemoteError, Resources, RunBundle

from qmx_engine.admission import declared_bytes
from qmx_engine.admission import sessions_of as sessions_for_ram
from qmx_engine.heartbeat import Heartbeat
from qmx_engine.ledger.events import KINDS, EventKind
from qmx_engine.ledger.signature import signature
from qmx_engine.nodes.base import Failed, Gate, NodeJob, NodeResult, Ok, Waiting
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.local import Emit, LocalWorker

SCHEMA: Final = "qmx.remote.attempt/1"
MIB: Final = 1024 * 1024
HEARTBEAT_TIMEOUT: Final = 30.0
"""Three missed sidecar beats: slow is not lost, and lost is not a retry until the effect folds."""
POLL_SECONDS: Final = 0.25
RELAYED: Final = KINDS - {"node_started", "node_finished", "node_failed", "node_waiting"}
"""The sidecar's rows the ledger takes as they are. Its start and finish are the adapter's own
rows (`node_started` here, the ending from the result), so relaying them would double them; a
runner-side `attempt_started` is the sidecar's bookkeeping and is not a ledger kind."""
PASS_ENV: Final = "QMX_RUN_PASS"  # noqa: S105 - an environment name, not a credential


class GatewayPort(Protocol):
    """What the Hub serves for one run: its event tail and, when the attempt ends, its result."""

    def events(self, run_id: str) -> list[dict[str, Any]]: ...

    def result(self, run_id: str) -> Document | None: ...


@dataclass(frozen=True, slots=True)
class AttemptResources:
    """The placement's resources for one attempt.

    `memory_mb` is None when neither the node declared one nor this machine has measured a
    session, so the provider's own default stands and no figure of ours is invented (D-11).
    """

    cpus: int
    memory_mb: int | None
    timeout: int
    gpu: int = 0

    def as_document(self) -> dict[str, object]:
        """The provider's resource row: the memory figure only when this attempt has one."""
        found: dict[str, object] = {
            "cpus": self.cpus,
            "timeout": self.timeout,
            "gpu": self.gpu,
        }
        if self.memory_mb is not None:
            found["memory_mb"] = self.memory_mb
        return found


def live_pair(live: Heartbeat | None) -> tuple[int, int] | None:
    """A host row's live figures: the RAM it can give and what one of its sessions holds."""
    if live is None or live.free_ram_bytes is None or not live.session_bytes:
        return None
    return live.free_ram_bytes, live.session_bytes


def sessions_of(
    settings: Mapping[str, object], placement: str, *, live: Heartbeat | None = None
) -> int:
    """AD-30's derived session count, from the machine's live reading (D-11).

    Free RAM over the measured session size, both from the host row that machine wrote. Zero for a
    placement that names no row of its own, and zero while no host has measured one: these figures
    are measured now, never written down.
    """
    if not any(key.startswith(f"placement.{placement}.") for key in settings):
        return 0
    pair = live_pair(live)
    return 0 if pair is None else sessions_for_ram(*pair)


def setting(settings: Mapping[str, object], key: str, fallback: object) -> object:
    if key in settings:
        return settings[key]
    return DEFAULTS.get(key, fallback)


def memory_mb(node_definition: Mapping[str, object] | None, live: Heartbeat | None) -> int | None:
    """An attempt's memory: what its node declares, else what one measured session holds."""
    declared = declared_bytes(node_definition or {})
    if declared is not None:
        return declared // MIB
    pair = live_pair(live)
    return None if pair is None else pair[1] // MIB


def resources_of(
    settings: Mapping[str, object],
    placement: str,
    node_definition: Mapping[str, object] | None = None,
    *,
    live: Heartbeat | None = None,
) -> AttemptResources:
    cpus = setting(settings, f"placement.{placement}.attempt_cpus", 1)
    timeout = setting(settings, f"placement.{placement}.attempt_timeout", 3_600)
    gpu = setting(settings, f"placement.{placement}.attempt_gpu", 0)
    return AttemptResources(
        cpus=int(cpus) if isinstance(cpus, int | str) else 1,
        memory_mb=memory_mb(node_definition, live),
        timeout=int(timeout) if isinstance(timeout, int | str) else 3_600,
        gpu=int(gpu) if isinstance(gpu, int | str) else 0,
    )


def attempt_bundle(
    job: NodeJob,
    *,
    settings: Mapping[str, object] | None = None,
    files: Mapping[str, str] | None = None,
    live: Heartbeat | None = None,
    door_url: str = "",
) -> Document:
    """The job as the sidecar receives it: definition, inputs by hash, refs, resources.

    `job.credentials` is the node's own name-to-`qmx/*` reference map; the bundle carries the
    **names** so the sidecar redacts their values from this attempt's output, and carries no value
    itself. The run pass is not in the bundle: it travels in the provider's one secret name
    (`provider_secrets`), so a bundle written to a disk or a bucket never holds it. `live` is the
    host row whose measured session size stands in for a memory the node did not declare.
    `door_url` is the market-data door this placement reads price data through (AD-70).
    """
    settings = settings or DEFAULTS
    refs = dict(job.credentials)
    for name, ref in refs.items():
        if not ref.startswith("qmx/") or not name:
            raise RemoteError(f"{name}: remote attempts take qmx/* references, never a value")
    code = dict(files or {})
    resources = resources_of(settings, job.placement, job.node_definition, live=live)
    return cast(
        Document,
        {
            "schema": SCHEMA,
            "job": {
                **attempt_keys(job),
                "idempotency_key": job.idempotency_key,
                "node_definition": job.node_definition,
                "inputs": job.inputs,
                "inputs_hash": fingerprint(job.inputs),
                "mode": job.mode,
                "resolved_model": job.resolved_model,
                "now": job.now,
                "placement": job.placement,
                "priority": job.priority,
                "door_url": door_url,
            },
            "files": code,
            "file_hashes": {name: text_hash(text) for name, text in code.items()},
            "secrets": sorted(refs),
            "resources": resources.as_document(),
        },
    )


def text_hash(text: str) -> str:
    """A file's content hash, the same raw sha256 the sidecar checks on the runner host."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_files(job: NodeJob) -> Mapping[str, str]:
    """The run's code copy, which the sidecar materialises before the attempt.

    A remote executor resolves the node's scripts on its own side (L-42), so the bundle carries
    them by content hash. Files are read as text: a workflow's code folder is scripts and data,
    and a binary file is a build artifact the run should have put in its output zone instead.
    """
    code = Path(job.workspace or "") / "code"
    if job.workspace is None or not code.is_dir():
        return {}
    return {
        path.relative_to(code).as_posix(): path.read_text("utf-8", errors="replace")
        for path in sorted(code.rglob("*"))
        if path.is_file()
    }


def attempt_keys(job: NodeJob) -> dict[str, Any]:
    return {
        "run_id": job.run_id,
        "node_id": job.node_id,
        "iteration": job.iteration,
        "partition": job.partition,
        "attempt": job.attempt,
        "memo_key": job.memo_key,
    }


def provider_secrets(run_pass: str) -> dict[str, str]:
    """Library AD-12: the one thing a provider is given is the pass, by environment name."""
    if not run_pass:
        raise RemoteError("a remote attempt needs a run pass")
    return {PASS_ENV: run_pass}


def result_from_document(document: Mapping[str, Any]) -> NodeResult:
    """The wire shape the sidecar wrote, back as the engine's ending."""
    status = document.get("status")
    match status:
        case "ok":
            outputs = document.get("outputs")
            if not isinstance(outputs, dict):
                raise RemoteError("a remote ok carries an outputs object")
            artifacts = document.get("artifacts")
            verdict = document.get("verdict")
            span = document.get("span")
            return Ok(
                outputs=cast(dict[str, Any], outputs),
                artifacts=tuple(str(name) for name in cast(list[object], artifacts))
                if isinstance(artifacts, list)
                else (),
                verdict=str(verdict) if verdict is not None else None,
                span=cast(dict[str, Any], span) if isinstance(span, dict) else {},
            )
        case "failed":
            code = str(document.get("code") or "remote_failed")
            message = str(document.get("message") or "the remote attempt failed")
            state = document.get("effect_state")
            return Failed(
                code,
                message,
                str(document.get("signature") or signature(code, message)),
                bool(document.get("retryable", True)),
                state if state in {"before", "after", "unknown"} else "before",
                cast(dict[str, Any], document["span"])
                if isinstance(document.get("span"), dict)
                else {},
            )
        case "waiting":
            return Waiting(
                str(document.get("reason") or "remote_wait"),
                None if document.get("resume_at") is None else str(document["resume_at"]),
                None if document.get("event") is None else str(document["event"]),
            )
        case "gate":
            options = document.get("options")
            return Gate(
                str(document.get("ask") or "remote_gate"),
                tuple(str(option) for option in cast(list[object], options))
                if isinstance(options, list)
                else (),
            )
        case _:
            raise RemoteError(f"a remote result names no status this engine knows: {status!r}")


class PlacementWorker(LocalWorker):
    """Routes a placed attempt to its machine and everything else to the local table."""

    def __init__(
        self,
        *,
        gateway: GatewayPort,
        providers: Mapping[str, Any],
        settings: Mapping[str, object],
        mint: Callable[[NodeJob], str],
        remote: Collection[str],
        heartbeat_timeout: float = HEARTBEAT_TIMEOUT,
        poll_seconds: float = POLL_SECONDS,
        clock: Callable[[], float] = time.time,
        code: Callable[[NodeJob], Mapping[str, str]] | None = None,
        live: Callable[[], Heartbeat | None] | None = None,
        doors: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.gateway = gateway
        self.providers = providers
        self.settings = settings
        self.mint = mint
        self.remote = frozenset(remote)
        self.heartbeat_timeout = heartbeat_timeout
        self.poll_seconds = poll_seconds
        self.clock = clock
        self.code: Callable[[NodeJob], Mapping[str, str]] = code or run_files
        self.live = live
        """The newest heartbeat row of the machines this host dispatches to, read per attempt: it
        carries the live RAM and measured session size a bundle's resources come from (D-11)."""
        self.doors = dict(doors or {})
        """Placement to the market-data door URL its attempts read price data through (AD-70)."""
        self.handles: dict[str, tuple[Any, Any]] = {}
        """Run id to `(provider, handle)` of the attempt in flight, so `cancel` reaches it."""

    def reading(self) -> Heartbeat | None:
        return None if self.live is None else self.live()

    def routes(self, placement: str) -> bool:
        return placement in self.remote

    async def run(self, job: NodeJob, emit: Emit) -> NodeResult:
        if not self.routes(job.placement):
            return await super().run(job, emit)
        provider = self.providers.get(job.placement)
        if provider is None:
            message = f"no provider serves placement {job.placement}"
            return Failed("placement", message, signature("placement", message), False, "before")
        bundle = attempt_bundle(
            job,
            settings=self.settings,
            files=self.code(job),
            live=self.reading(),
            door_url=self.doors.get(job.placement, ""),
        )
        return await self.dispatch(job, provider, bundle, emit)

    async def dispatch(
        self, job: NodeJob, provider: Any, bundle: Document, emit: Emit
    ) -> NodeResult:
        emit(
            "node_started",
            attempt_keys(job)
            | {"placement": job.placement, "idempotency_key": job.idempotency_key},
        )
        try:
            handle = provider.provision(job.run_id, _as_bundle(bundle, job.placement))
            handle = provider.start(handle, provider_secrets(self.mint(job)))
        except RemoteError as error:
            return Failed(
                "placement",
                str(error),
                signature("placement", str(error)),
                True,
                "before",
            )
        self.handles[job.run_id] = (provider, handle)
        seen = 0
        last_beat = self.clock()
        try:
            while True:
                rows = self.gateway.events(job.run_id)
                for row in rows[seen:]:
                    kind = str(row.get("kind") or "")
                    if kind == "heartbeat":
                        last_beat = self.clock()
                    if kind in RELAYED:
                        emit(cast(EventKind, kind), _event_data(row))
                seen = len(rows)
                result = self.gateway.result(job.run_id)
                if result is not None:
                    return result_from_document(result)
                status = provider.status(handle)
                if status in {"failed", "stopped", "interrupted"}:
                    # A runner that ends between the two reads is a success whose result arrived
                    # one poll late; only no result at all is the unknown fold.
                    ended = self.gateway.result(job.run_id)
                    if ended is not None:
                        return result_from_document(ended)
                    message = "the runner was lost mid-attempt; its effect is unknown"
                    return Failed(
                        "heartbeat_lost",
                        message,
                        signature("heartbeat_lost", message),
                        True,
                        "unknown",
                    )
                if self.clock() - last_beat > self.heartbeat_timeout:
                    message = "the runner stopped heartbeating; its effect is unknown"
                    return Failed(
                        "heartbeat_lost",
                        message,
                        signature("heartbeat_lost", message),
                        True,
                        "unknown",
                    )
                await asyncio.sleep(self.poll_seconds)
        finally:
            self.handles.pop(job.run_id, None)

    def cancel(self, idempotency_key: str, reason: str = "stop") -> bool:
        """A remote attempt stops through its provider; the local table answers for the rest."""
        found = super().cancel(idempotency_key, cast(Any, reason))
        if found:
            return True
        for run_id, (provider, handle) in list(self.handles.items()):
            try:
                provider.stop(handle)
            except RemoteError:
                continue
            self.handles.pop(run_id, None)
            return True
        return False


def _as_bundle(bundle: Document, placement: str) -> RunBundle:
    """The provider's own envelope. The node attempt is a run of one node, so it goes as a
    `workflow` bundle whose definition is the sidecar's whole document and whose files carry the
    run's code by hash; the provider ships the definition and files together."""
    definition = {**bundle, "placement": placement}
    files = cast(Mapping[str, str], bundle["files"])
    hashes = {name: text_hash(text) for name, text in files.items()}
    return RunBundle(
        kind="workflow",
        definition=definition,
        definition_hash=fingerprint({"definition": definition, "files": hashes}),
        files=hashes,
        resources=Resources.model_validate(bundle["resources"]),
    )


def _event_data(row: Mapping[str, Any]) -> dict[str, Any]:
    """The event body without the attempt key words the emitter owns, so a gateway row and a
    local event carry the same fields."""
    drop = {"kind", "run_id", "node_id", "iteration", "partition", "attempt", "memo_key"}
    return {key: value for key, value in row.items() if key not in drop}
