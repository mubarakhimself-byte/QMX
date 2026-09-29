"""In-memory artifact store for local-complete PUT /artifacts/stage (Story 70.1).

Completeness is daemon-recomputed fp1 plus byte count after the daemon holds
the bytes. Browser hash is not possession. Interrupted bytes are never stored.
Same complete content reuses the existing fp1. Writes pass
``before_artifact_register``. No new sqlite class.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from qma.core.plugins.hooks import HookResult, HookSource, build_hook_result
from qma.core.vocabulary.enums import ArtifactCompleteness, HookResultDecision, HookVerb
from qma.daemon.hooks.registry import HookRegistry, event_names_for_verb
from qma.wire.stage_artifact import (
    STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA,
    claim_stage_artifact_put_existed_at_inspect_sha,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
from qmf.data.store.refusals import policy_rejection

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
    """Inspect-pattern in-memory ``_artifacts`` map. Not a Library database."""

    hooks: HookRegistry | None = None
    _artifacts: dict[str, StagedArtifact] = field(default_factory=dict[str, StagedArtifact])

    def get(self, fp1: str) -> StagedArtifact | None:
        return self._artifacts.get(fp1)

    def objects(self) -> tuple[StagedArtifact, ...]:
        return tuple(self._artifacts.values())

    def abandon_incomplete(self) -> None:
        """Interrupted PUT: drop unregistered bytes. Store holds only complete objects."""

    def stage_complete_bytes(self, body: bytes) -> Result[StagedArtifact]:
        """Register complete bytes through before_artifact_register.

        Completeness is fp1 plus ``len(body)`` after this store holds a copy.
        A complete object with the same content hash is reused — no second fp1.
        """
        held = bytes(body)
        fp1 = fingerprint_bytes(held).value
        existing = self._artifacts.get(fp1)
        if existing is not None:
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
        self._artifacts[fp1] = copy
        self._after_artifact_register(copy)
        return Ok(copy)

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
