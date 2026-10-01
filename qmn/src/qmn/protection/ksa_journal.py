"""Checked CT-13 projection for the configured CT-30 KSA fold."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, cast

from qmf.core import Fingerprint, Ok, Result, World, WriterId, fingerprint, is_refusal
from qmf.data import JournalEventType, JournalReader
from qmf.data.store import JournalStore

from qmn.protection._refuse import clean_token, invalid, policy, unavailable
from qmn.protection.ksa import (
    KsaEnforcementScope,
    KsaEscalationRecord,
    KsaLevel,
    LevelEpoch,
    fold_ksa_level,
    mint_escalation,
)

__all__ = [
    "KSA_EPOCH_CLASS",
    "KSA_ESCALATION_CLASS",
    "KsaFoldEvidence",
    "KsaJournalProjection",
]

KSA_EPOCH_CLASS: Final[str] = "qmn-ksa-level-epoch"
KSA_ESCALATION_CLASS: Final[str] = "qmn-ksa-escalation"


@dataclass(frozen=True, slots=True)
class KsaFoldEvidence:
    """Exact levels and CT-13 fingerprints consumed by a decision."""

    global_level: KsaLevel
    stream_level: KsaLevel
    epoch_fingerprints: tuple[Fingerprint, ...]
    event_fingerprints: tuple[Fingerprint, ...]


@dataclass(frozen=True, slots=True)
class KsaJournalProjection:
    """Read pinned global and stream epochs and fold checked CT-30 records.

    The authorized writer set, stream, world, scopes, and epochs are boot
    configuration. GREEN is emitted only after each configured epoch has a
    checked CT-13 witness; absence, a gap, or an unrecognized KSA payload fails
    closed.
    """

    reader: JournalReader
    world: World
    stream_name: str
    global_epoch: LevelEpoch
    stream_epoch: LevelEpoch
    authorized_writers: frozenset[WriterId]

    @classmethod
    def try_create(
        cls,
        *,
        reader: object,
        world: object,
        stream_name: object,
        global_epoch: object,
        stream_epoch: object,
        authorized_writers: object,
    ) -> Result[KsaJournalProjection]:
        token = clean_token(stream_name)
        if not isinstance(reader, JournalReader) or not isinstance(world, World) or token is None:
            return invalid(
                "ksa_journal", "KSA projection uses a typed QMF reader, world, and stream"
            )
        if reader.journal.world is not world:
            return policy("ksa_world", "the checked CT-13 reader is pinned to the configured world")
        if not isinstance(global_epoch, LevelEpoch) or not isinstance(stream_epoch, LevelEpoch):
            return invalid("ksa_epoch", "global and stream KSA epochs are typed LevelEpoch values")
        if global_epoch.scope.kind != "global" or stream_epoch.scope.kind != "stream":
            return policy("ksa_scope", "the configured KSA epochs cover global and stream scopes")
        if not isinstance(authorized_writers, (set, frozenset, tuple, list)):
            return invalid("ksa_writers", "authorized CT-30 writers are an explicit collection")
        raw_writers = tuple(cast("Iterable[object]", authorized_writers))
        if not raw_writers or any(not isinstance(writer, WriterId) for writer in raw_writers):
            return invalid("ksa_writers", "at least one typed CT-30 writer is configured")
        writers: frozenset[WriterId] = frozenset(cast("Iterable[WriterId]", raw_writers))
        return Ok(
            cls(
                reader=reader,
                world=world,
                stream_name=token,
                global_epoch=global_epoch,
                stream_epoch=stream_epoch,
                authorized_writers=writers,
            )
        )

    @property
    def journal(self) -> JournalStore:
        return self.reader.journal

    def levels(self, *, expected_stream_scope: KsaEnforcementScope) -> Result[KsaFoldEvidence]:
        if not self.stream_epoch.scope.matches(expected_stream_scope):
            return policy("ksa_scope", "configured stream KSA epoch matches this Book account")
        events = self.reader.read_checked(self.stream_name, for_world=self.world)
        if is_refusal(events):
            return events
        epoch_fps: set[tuple[str, str, str]] = set()
        records: list[KsaEscalationRecord] = []
        source_fps: list[Fingerprint] = []
        expected_epochs = (self.global_epoch, self.stream_epoch)
        expected_epoch_ids = {epoch.epoch_id for epoch in expected_epochs}
        expected_epoch_refs = {
            (epoch.scope.token(), epoch.epoch_id, _epoch_fp(epoch) or "")
            for epoch in expected_epochs
        }
        for event in events.value:
            if event.event_type is not JournalEventType.CONTROL_ACTION:
                continue
            payload = event.payload
            kind = payload.get("control_action_subtype")
            body_class = payload.get("class")
            if body_class == KSA_EPOCH_CLASS or kind == "ksa-level-epoch":
                if body_class != KSA_EPOCH_CLASS or kind != "ksa-level-epoch":
                    return invalid("ksa_epoch", "KSA epoch class and control subtype agree")
                if event.writer not in self.authorized_writers:
                    return policy("ksa_writer", "KSA epoch is written by a configured authority")
                for epoch in expected_epochs:
                    if (
                        payload.get("epoch_id") == epoch.epoch_id
                        and payload.get("scope") == epoch.scope.token()
                        and payload.get("epoch_fp1") == _epoch_fp(epoch)
                    ):
                        epoch_fps.add((epoch.scope.token(), epoch.epoch_id, _epoch_fp(epoch) or ""))
                        source_fps.append(event.fingerprint)
                continue
            if body_class != KSA_ESCALATION_CLASS and kind != "ksa-escalation":
                continue
            if body_class != KSA_ESCALATION_CLASS or kind != "ksa-escalation":
                return invalid("ksa_record", "CT-30 KSA escalation class and subtype agree")
            if event.writer not in self.authorized_writers:
                return policy("ksa_writer", "CT-30 escalation is written by a configured authority")
            epoch_id = payload.get("level_epoch_id")
            scope_token = payload.get("scope")
            if not isinstance(epoch_id, str):
                return invalid("ksa_record", "CT-30 escalation identifies a string level epoch")
            epoch = next(
                (
                    row
                    for row in expected_epochs
                    if row.epoch_id == epoch_id and row.scope.token() == scope_token
                ),
                None,
            )
            if epoch is None:
                if epoch_id in expected_epoch_ids:
                    return policy("ksa_scope", "CT-30 escalation scope matches its pinned epoch")
                continue
            if (epoch.scope.token(), epoch.epoch_id, _epoch_fp(epoch) or "") not in epoch_fps:
                return unavailable("ksa_epoch_witness", "escalation references a witnessed epoch")
            issued_at = event.instant
            minted = mint_escalation(
                level=payload.get("level"),
                trigger_class=payload.get("trigger_class"),
                scope=epoch.scope,
                level_epoch_id=epoch_id,
                issued_at=issued_at,
                writer_id="/".join(event.writer.order_tuple()),
                arbitration_rank=payload.get("arbitration_rank"),
                quiet_elapsed_ns=payload.get("quiet_elapsed_ns", 0),
            )
            if is_refusal(minted):
                return minted
            records.append(minted.value)
            source_fps.append(event.fingerprint)
        if not expected_epoch_refs.issubset(epoch_fps):
            return unavailable(
                "ksa_epoch_witness",
                "checked CT-13 stream contains both configured KSA level epoch identities",
            )
        global_level = fold_ksa_level(
            records, scope=self.global_epoch.scope, epoch=self.global_epoch
        )
        if is_refusal(global_level):
            return global_level
        stream_level = fold_ksa_level(
            records, scope=self.stream_epoch.scope, epoch=self.stream_epoch
        )
        if is_refusal(stream_level):
            return stream_level
        epoch_fingerprints: list[Fingerprint] = []
        for epoch in expected_epochs:
            fp = fingerprint(epoch.fp1_identity())
            if is_refusal(fp):
                return fp
            epoch_fingerprints.append(fp.value)
        return Ok(
            KsaFoldEvidence(
                global_level=global_level.value,
                stream_level=stream_level.value,
                epoch_fingerprints=tuple(epoch_fingerprints),
                event_fingerprints=tuple(source_fps),
            )
        )


def _epoch_fp(epoch: LevelEpoch) -> str | None:
    resolved = fingerprint(epoch.fp1_identity())
    return None if is_refusal(resolved) else resolved.value.value
