"""Immutable versions, current proof, CAS activation and evidenced rollback.

A publish also lands the app's pack: one `mini-app` Library item whose `bundle.tar` blob is the
plugin tree a chat loads (engine AD-19, AD-55). The item is what a host materialises at its next
start, so publishing is how a mini app reaches a chat's surface.
"""

from __future__ import annotations

import hmac
import io
import json
import sqlite3
import sys
import tarfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

from qmx_ledger.journal import encoded, fingerprint

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition, Trust
from qmx_apps.road.history import definition, history, project
from qmx_apps.road.models import STAGES, Evidence, Stage
from qmx_apps.road.validation import validate
from qmx_apps.volume import Volume

if TYPE_CHECKING:
    from qmx_apps.supervisor import Supervisor

PLUGIN_JSON: Final = ".claude-plugin/plugin.json"
"""The one file a chat's CLI reads to see a pack. The view keeps the app's `skills/` beside it
and nothing else, since a pack ships no hook and starts no server (AD-55)."""
SKILLS: Final = "skills"


@dataclass(frozen=True, slots=True)
class Pack:
    """What a publish hands the Library: the app's plugin tree as one `bundle.tar`, and the few
    facts the `mini-app` item carries beside it."""

    app_id: str
    version: str
    definition_hash: str
    operations: tuple[str, ...]
    bundle: bytes


type PackSink = Callable[[Pack], str]
"""`Pack -> the Library object id`. The host closes over the store it writes the item on; a host
that attaches no sink keeps the publish local, as before."""


def pack_bundle(app_id: str, image: Definition) -> bytes:
    """The published pack as one tar: its `plugin.json`, naming the app and the rows it serves,
    and its `skills/` folder when the definition ships one."""
    manifest = image.manifest
    plugin = {
        "name": app_id,
        "version": manifest.version,
        "description": manifest.name,
        "operations": {
            name: {"approval": operation.approval, "description": operation.description}
            for name, operation in manifest.operations.items()
        },
    }
    files: dict[str, bytes] = {
        PLUGIN_JSON: (json.dumps(plugin, indent=2, sort_keys=True) + "\n").encode()
    }
    skills = image.root / SKILLS
    for path in sorted(skills.rglob("*")):
        if path.is_file():
            files[f"{SKILLS}/{path.relative_to(skills).as_posix()}"] = path.read_bytes()
    return tarball(files)


def tarball(files: Mapping[str, bytes]) -> bytes:
    """One tar of these files by posix path, with no timestamps and no owner: the bytes are the
    identity, so two publishes of one version make one blob."""
    with io.BytesIO() as buffer:
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for name in sorted(files):
                body = files[name]
                info = tarfile.TarInfo(name)
                info.size = len(body)
                info.mtime = 0
                archive.addfile(info, io.BytesIO(body))
        return buffer.getvalue()


class Road:
    def __init__(self, owner: Supervisor) -> None:
        self.owner = owner
        self._signing_key: bytes | None = None
        self.packs: PackSink | None = None

    def attach_packs(self, sink: PackSink | None) -> None:
        """Give the road the Library its published packs go to, or take it away."""
        self.packs = sink

    def signing_key(self, key: str) -> None:
        self._signing_key = key.encode()

    def register(self, image: Definition, trust: Trust, expected_hash: str | None) -> None:
        app_id = image.manifest.id
        Volume(self.owner.home, app_id).create(agents=bool(image.manifest.entrypoints.agents))
        with history(self.owner.home, app_id) as state:
            if state.head == image.hash:
                project(self.owner.home, app_id, state)
                return
            if state.head != expected_hash:
                raise AppError(
                    "head_conflict", "Candidate head changed; reload before saving.", 409
                )
            if any(
                record["stage"] == "build" and record["version"] == image.manifest.version
                for record in state.records
            ):
                raise AppError("immutable_version", "Changed content requires a new version.", 409)
            record = Evidence(
                definition_hash=image.hash,
                version=image.manifest.version,
                stage="build",
                passed=True,
                inputs={"manifest": cast(Document, image.manifest.model_dump(mode="json"))},
                versions=self._versions(image),
                results={"valid_definition": True},
                duration_seconds=0.0,
                parent=state.head,
                trust=trust,
            )
            state.append(record)
            project(self.owner.home, app_id, state)

    @staticmethod
    def _versions(image: Definition) -> Document:
        return {
            "definition": image.hash,
            "python": sys.version.split()[0],
            "lock": fingerprint((image.root / "uv.lock").read_text()),
        }

    def evidence(self, app_id: str) -> list[Document]:
        self.owner.get(app_id)
        with history(self.owner.home, app_id) as state:
            project(self.owner.home, app_id, state)
            return state.records

    def advance(
        self,
        app_id: str,
        expected_hash: str,
        stage: Stage | None = None,
        *,
        auto_publish: bool = True,
    ) -> Document:
        self.owner.get(app_id)
        with history(self.owner.home, app_id) as state:
            if state.head != expected_hash:
                raise AppError(
                    "head_conflict", "Proof must target the current immutable head.", 409
                )
            current = state.stages[expected_hash]
            index = STAGES.index(current) + 1
            if index >= len(STAGES) or STAGES[index] == "live":
                raise AppError("stage_refused", "Use publication for live activation.", 409)
            target = STAGES[index]
            if stage is not None and target != stage:
                raise AppError("stage_refused", "Road stages cannot be skipped or repeated.", 409)
            image = definition(self.owner.home, app_id, expected_hash)
            started = time.monotonic()
            inputs: Document = {"expected_hash": expected_hash}
            results: Document
            error: Exception | None = None
            try:
                actual_inputs, results = validate(self.owner, image, target)
                inputs.update(actual_inputs)
                definition(self.owner.home, app_id, expected_hash)
                passed = results.get("passed") is True
                if not passed:
                    error = AppError(
                        "stage_failed",
                        "The actual app tests or MCP probes failed; inspect the step evidence.",
                        422,
                    )
            except Exception as failure:
                error = failure
                passed = False
                results = {
                    "error": failure.document()
                    if isinstance(failure, AppError)
                    else {"type": type(failure).__name__}
                }
            record = state.append(
                Evidence(
                    definition_hash=image.hash,
                    version=image.manifest.version,
                    stage=target,
                    passed=passed,
                    inputs=inputs,
                    versions=self._versions(image),
                    results=results,
                    duration_seconds=time.monotonic() - started,
                )
            )
        self.owner.emit(app_id, {"type": "road_step", **record})
        if error:
            if isinstance(error, AppError):
                raise error
            raise AppError(
                "stage_failed",
                "Proof configuration or runtime failed; inspect the step evidence.",
                422,
            ) from error
        active = self.active_revision(app_id)
        if auto_publish and target == "shadow" and image.manifest.risk != "money":
            return self.publish(app_id, expected_hash, active)
        return record

    def active_revision(self, app_id: str) -> str | None:
        with history(self.owner.home, app_id) as state:
            return str(state.active["revision"]) if state.active else None

    def sign(
        self,
        app_id: str,
        definition_hash: str,
        expected_active: str | None,
        *,
        rollback: bool = False,
    ) -> str:
        definition(self.owner.home, app_id, definition_hash)
        if self._signing_key is None:
            raise AppError(
                "operator_unavailable",
                "Operator signing is available through authenticated local REST.",
                409,
            )
        return hmac.new(
            self._signing_key,
            encoded(
                {
                    "app_id": app_id,
                    "definition_hash": definition_hash,
                    "expected_active": expected_active,
                    "action": "rollback" if rollback else "publish",
                }
            ),
            "sha256",
        ).hexdigest()

    def publish(
        self,
        app_id: str,
        expected_hash: str,
        expected_active: str | None = None,
        signature: str | None = None,
        *,
        rollback: bool = False,
    ) -> Document:
        try:
            return self._publish(
                app_id, expected_hash, expected_active, signature, rollback=rollback
            )
        except AppError as error:
            if error.code == "volume_busy":
                raise AppError(
                    "publication_conflict",
                    "Another road transition owns this app; reload before publishing.",
                    409,
                ) from error
            raise

    def _publish(
        self,
        app_id: str,
        expected_hash: str,
        expected_active: str | None,
        signature: str | None,
        *,
        rollback: bool,
    ) -> Document:
        self.owner.get(app_id)
        started = time.monotonic()
        with history(self.owner.home, app_id) as state:
            active = state.active
            current = str(active["revision"]) if active else None
            if current != expected_active:
                raise AppError(
                    "publication_conflict",
                    "Active revision changed; reload before publishing.",
                    409,
                )
            target = expected_hash
            if rollback:
                prior = state.publications[-2] if len(state.publications) >= 2 else None
                if prior is None:
                    raise AppError(
                        "rollback_refused", "There is no previous published version.", 409
                    )
                target = str(prior["definition_hash"])
            elif state.head != target:
                raise AppError("head_conflict", "Only the current candidate head can publish.", 409)
            if state.stages.get(target) not in {"shadow", "live"}:
                raise AppError(
                    "stage_refused", "Current tests, sandbox and shadow evidence are required.", 409
                )
            image = definition(self.owner.home, app_id, target)
            previous = (
                definition(self.owner.home, app_id, str(active["definition_hash"]))
                if active
                else None
            )
            broken = self.owner.contract_problems(image, previous)
            if broken:
                raise AppError(
                    "contract_changed",
                    "A provides schema changed and a consumer cannot read it: "
                    + "; ".join(
                        f"{name} breaks {', '.join(rows)}" for name, rows in broken.items()
                    ),
                    409,
                )
            if image.manifest.risk == "money":
                signed = self.sign(app_id, target, current, rollback=rollback)
                if (
                    signature is None
                    or not signature.isascii()
                    or not hmac.compare_digest(signature, signed)
                ):
                    raise AppError(
                        "signature_required",
                        "Proposal-only money apps require the operator's bound signature.",
                        409,
                    )
            previous = str(active["definition_hash"]) if active else None
            old_runtime = self.owner.status(app_id)
            try:
                if old_runtime.get("status") == "running":
                    self.owner.stop(app_id)
                runtime = self.owner.start(app_id, definition_hash=target)
                definition(self.owner.home, app_id, target)
                record = state.append(
                    Evidence(
                        definition_hash=target,
                        version=image.manifest.version,
                        stage="live",
                        passed=True,
                        inputs={
                            "expected_hash": expected_hash,
                            "expected_active": current,
                            "operator_signed": image.manifest.risk == "money",
                        },
                        versions=self._versions(image),
                        results={
                            "runtime": runtime,
                            "budget": cast(Document, image.manifest.budget.model_dump(mode="json")),
                            "proposal_only": image.manifest.risk == "money",
                        },
                        duration_seconds=time.monotonic() - started,
                        expected_active=current,
                        action="rollback" if rollback else "publish",
                    )
                )
            except BaseException as error:
                self.owner.stop(app_id)
                if previous and old_runtime.get("status") == "running":
                    self.owner.start(app_id, definition_hash=previous)
                if isinstance(error, AppError):
                    state.append(
                        Evidence(
                            definition_hash=target,
                            version=image.manifest.version,
                            stage="live",
                            passed=False,
                            inputs={"expected_hash": expected_hash, "expected_active": current},
                            versions=self._versions(image),
                            results={"error": error.document()},
                            duration_seconds=time.monotonic() - started,
                            expected_active=current,
                            action="rollback" if rollback else "publish",
                        )
                    )
                raise
            # Journal acceptance survives a failed catalog write; retry repairs it.
            try:
                project(self.owner.home, app_id, state)
            except (OSError, sqlite3.Error) as error:
                raise AppError(
                    "publication_committed",
                    "Publication committed; read app evidence to reconcile its catalog.",
                    503,
                ) from error
            self._landed(app_id, image)
        self.owner.emit(app_id, {"type": "published", **record})
        return record

    def _landed(self, app_id: str, image: Definition) -> None:
        """Hand the published pack to the Library sink (AD-19, AD-55). A host that attached no
        sink keeps the publish local; the next publish lands the item."""
        sink = self.packs
        if sink is None:
            return
        sink(
            Pack(
                app_id=app_id,
                version=image.manifest.version,
                definition_hash=image.hash,
                operations=tuple(sorted(image.manifest.operations)),
                bundle=pack_bundle(app_id, image),
            )
        )
