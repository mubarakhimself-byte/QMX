"""Artifact cache backed by the declared CT-11 store for PUT /artifacts/stage.

Completeness is daemon-recomputed fp1 plus byte count after the daemon holds
the bytes. Browser hash is not possession. Interrupted bytes are never stored.
Same complete content reuses the existing fp1. Writes pass
``before_artifact_register``. No new sqlite class.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from qma.core.plugins.hooks import HookResult, HookSource, build_hook_result
from qma.core.vocabulary.enums import ArtifactCompleteness, HookResultDecision, HookVerb
from qma.daemon.hooks.registry import HookRegistry, event_names_for_verb
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.wire.stage_artifact import (
    STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA,
    claim_stage_artifact_put_existed_at_inspect_sha,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
from qmf.data.store.append_store import AppendStore
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA",
    "ArtifactStore",
    "StagedArtifact",
    "claim_stage_artifact_put_existed_at_inspect_sha",
]


ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA: Final[bool] = STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA

_BLOCKING_BEFORE: Final[frozenset[HookResultDecision]] = frozenset(
    {
        HookResultDecision.DENY,
        HookResultDecision.DEFER,
        HookResultDecision.ASK,
        HookResultDecision.BLOCK_STOP,
    }
)


@dataclass(frozen=True, slots=True)
class StagedArtifact:
    """Local-complete possession: durable fp1 + byte count after the daemon holds bytes."""

    fp1: str
    byte_count: int
    completeness: str
    content: bytes
    reused: bool = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "fp1": self.fp1,
                "byte_count": self.byte_count,
                "completeness": self.completeness,
                "local_complete": True,
            }
        )


@dataclass
class ArtifactStore:
    """Complete-byte cache; daemon receipts commit to artifact store and announcement."""

    hooks: HookRegistry | None = None
    _artifacts: dict[str, StagedArtifact] = field(default_factory=dict[str, StagedArtifact])
    journal: AuthoritativeJournal | None = None
    durable_store: AppendStore | None = None
    _durable_fp1s: set[str] = field(default_factory=set, init=False)

    def get(self, fp1: str) -> StagedArtifact | None:
        return self._artifacts.get(fp1)

    def objects(self) -> tuple[StagedArtifact, ...]:
        return tuple(self._artifacts.values())

    def abandon_incomplete(self) -> None:
        """Interrupted PUT: drop unregistered bytes. Store holds only complete objects."""

    def drop_incomplete(self, fp1: str) -> None:
        """Dest interrupt/mismatch: never leave a runnable incomplete object.

        Complete dest objects with this fp1 stay. The store holds only complete
        objects, so a first-time mismatch has nothing to drop.
        """
        if self._artifacts.get(fp1) is None:
            return

    def stage_complete_bytes(self, body: bytes) -> Result[StagedArtifact]:
        """Register complete bytes through before_artifact_register.

        Completeness is fp1 plus ``len(body)`` after this store holds a copy.
        A complete object with the same content hash is reused — no second fp1.
        """
        held = bytes(body)
        fp1 = fingerprint_bytes(held).value
        existing = self._artifacts.get(fp1)
        if existing is not None and (self.journal is None or fp1 in self._durable_fp1s):
            return Ok(
                StagedArtifact(
                    fp1=existing.fp1,
                    byte_count=existing.byte_count,
                    completeness=existing.completeness,
                    content=existing.content,
                    reused=True,
                )
            )
        copy = StagedArtifact(
            fp1=fp1,
            byte_count=len(held),
            completeness=ArtifactCompleteness.COMPLETE.value,
            content=held,
        )
        hook = self._before_artifact_register(copy)
        if is_refusal(hook):
            return hook
        gate = hook.value
        if gate.decision in _BLOCKING_BEFORE:
            before, _after = event_names_for_verb(HookVerb.ARTIFACT_REGISTER)
            return policy_rejection(
                before,
                f"{before} resolved to {gate.decision.value}; staged bytes not retained",
                given=gate.reason or gate.decision.value,
                wrote_object=False,
            )
        if self.journal is not None:
            if self.durable_store is None:
                return policy_rejection(
                    "artifact_store", "durable staging requires the declared CT-11 store"
                )
            declared = self.journal.declare_store("artifact_store")
            if is_refusal(declared):
                return declared
            row = {
                "class": "qma-staged-artifact-v1",
                "format_version": 1,
                "fp1": copy.fp1,
                "byte_count": copy.byte_count,
                "completeness": copy.completeness,
                "content_base64": base64.b64encode(copy.content).decode("ascii"),
            }
            stored = self.durable_store.append_raw([row])
            if is_refusal(stored):
                return stored
            durable = self.journal.announce_evidence_append(
                "artifact_store",
                stored.value.fingerprint,
                extra_payload={
                    "kind": "local_complete_stage",
                    "format_version": 1,
                    "fp1": copy.fp1,
                    "byte_count": copy.byte_count,
                    "completeness": copy.completeness,
                },
            )
            if is_refusal(durable):
                return durable
            self._durable_fp1s.add(fp1)
        self._artifacts[fp1] = copy
        self._after_artifact_register(copy)
        return Ok(copy)

    def restore_from_journal(self) -> Result[int]:
        """Resolve announced stage-only bytes before accepting consumer requests.

        Existing editor_draft.saved rows remain independently restorable by the
        draft service. Bytes live in the independent artifact store, not a journal
        projection. Existing artifact.registered announces its record reference.
        """
        if self.journal is None:
            return Ok(0)
        if self.durable_store is None:
            return policy_rejection("artifact_store", "restore requires the declared CT-11 store")
        stream = self.journal.read_events()
        if is_refusal(stream):
            return stream
        restored = 0
        for event in stream.value:
            if (
                event.event != "artifact.registered"
                or event.payload.get("kind") != "local_complete_stage"
            ):
                continue
            announcement = event.payload
            if announcement.get("store") != "artifact_store":
                return invalid_input(
                    "artifact_store", "stage announcement names its independent store"
                )
            rows = self.durable_store.read_raw(
                announcement.get("record_fp1"), for_world=self.durable_store.world
            )
            if is_refusal(rows):
                return rows
            if len(rows.value) != 1:
                return invalid_input(
                    "artifact_store", "stage reference resolves exactly one immutable envelope"
                )
            row = rows.value[0]
            encoded, fp1, count = row.get("content_base64"), row.get("fp1"), row.get("byte_count")
            if (
                row.get("class") != "qma-staged-artifact-v1"
                or row.get("format_version") != 1
                or isinstance(row.get("format_version"), bool)
                or not isinstance(encoded, str)
                or not isinstance(fp1, str)
                or not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
                or row.get("completeness") != ArtifactCompleteness.COMPLETE.value
            ):
                return invalid_input(
                    "artifact_store", "invalid durable stage receipt", journal_seq=event.journal_seq
                )
            try:
                content = base64.b64decode(encoded, validate=True)
            except binascii.Error, ValueError:
                return invalid_input(
                    "artifact_store", "invalid durable staged bytes", journal_seq=event.journal_seq
                )
            if len(content) != count:
                return invalid_input(
                    "artifact_store",
                    "durable stage byte count mismatch",
                    journal_seq=event.journal_seq,
                )
            if any(
                announcement.get(key) != row.get(key)
                for key in ("format_version", "fp1", "byte_count", "completeness")
            ):
                return invalid_input(
                    "artifact_store",
                    "stage announcement differs from immutable envelope",
                    journal_seq=event.journal_seq,
                )
            result = self.restore_complete_bytes(content, expected_fp1=fp1)
            if is_refusal(result):
                return result
            self._durable_fp1s.add(fp1)
            restored += 1
        return Ok(restored)

    def restore_complete_bytes(self, body: bytes, *, expected_fp1: str) -> Result[StagedArtifact]:
        """Rehydrate daemon-held complete bytes from checked durable evidence.

        Restore does not re-run the artifact-registration hook: the durable
        receipt proves these immutable bytes passed that gate before persistence.
        """
        held = bytes(body)
        actual_fp1 = fingerprint_bytes(held).value
        if actual_fp1 != expected_fp1:
            return policy_rejection(
                "fp1",
                "durable staged bytes do not match the expected immutable fp1",
                expected=expected_fp1,
                actual=actual_fp1,
            )
        existing = self._artifacts.get(expected_fp1)
        if existing is not None:
            if (
                existing.content != held
                or existing.completeness != ArtifactCompleteness.COMPLETE.value
            ):
                return policy_rejection(
                    "fp1",
                    "in-memory staged bytes conflict with their durable journal copy",
                    given=expected_fp1,
                )
            return Ok(existing)
        restored = StagedArtifact(
            fp1=expected_fp1,
            byte_count=len(held),
            completeness=ArtifactCompleteness.COMPLETE.value,
            content=held,
        )
        self._artifacts[expected_fp1] = restored
        return Ok(restored)

    def _before_artifact_register(self, copy: StagedArtifact) -> Result[HookResult]:
        if self.hooks is None:
            return Ok(build_hook_result(HookResultDecision.ALLOW, reason="no_hook_registry"))
        before, _after = event_names_for_verb(HookVerb.ARTIFACT_REGISTER)
        payload = dict(copy.to_payload())
        payload["kind"] = "local_complete_stage"
        result = self.hooks.dispatch(
            before,
            payload=payload,
            source=HookSource.MISSION,
        )
        if is_refusal(result):
            return result
        return Ok(result.value)

    def _after_artifact_register(self, copy: StagedArtifact) -> None:
        if self.hooks is None:
            return
        _before, after = event_names_for_verb(HookVerb.ARTIFACT_REGISTER)
        payload = dict(copy.to_payload())
        payload["kind"] = "local_complete_stage"
        self.hooks.dispatch(
            after,
            payload=payload,
            source=HookSource.MISSION,
        )
