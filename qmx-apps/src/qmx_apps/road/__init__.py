"""Immutable versions, current proof, CAS activation and evidenced rollback."""

from __future__ import annotations

import hmac
import sqlite3
import sys
import time
from typing import TYPE_CHECKING, cast

from qmx_agents.guards.journal import encoded, fingerprint

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition, Trust
from qmx_apps.road.history import definition, history, project
from qmx_apps.road.models import STAGES, Evidence, Stage
from qmx_apps.road.validation import validate
from qmx_apps.volume import Volume

if TYPE_CHECKING:
    from qmx_apps.supervisor import Supervisor


class Road:
    def __init__(self, owner: Supervisor) -> None:
        self.owner = owner
        self._signing_key: bytes | None = None

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

    def advance(self, app_id: str, expected_hash: str, stage: Stage | None = None) -> Document:
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
        if target == "shadow" and image.manifest.risk != "money":
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
        self.owner.emit(app_id, {"type": "published", **record})
        return record
