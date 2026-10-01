"""Durable CT-15 key authority backed by the world's CT-13 journal.

The authority writes an exact normalized CT-10 observation as an intent before
raw-room admission, then acknowledges completion after that admission succeeds.
On restart, an intent without completion replays the retained observation
verbatim, so a lost append acknowledgement cannot mint a second observation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final, cast

from qmf.core import Instant, Ok, Result, WriterId, fingerprint, is_refusal
from qmf.data.ingest import IntakeKey
from qmf.data.journal import JournalEventType
from qmf.data.journal_producer import JournalReader, JournalWriter
from qmf.data.observation import SourceObservation
from qmf.data.store import JournalStore
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = ["IntakeAuthority", "IntakeReservation"]

_EVENT_CLASS: Final[str] = "qmf-ct15-intake-key"
_INTENT: Final[str] = "intent"
_COMPLETE: Final[str] = "complete"


@dataclass(frozen=True, slots=True)
class IntakeReservation:
    """The canonical observation retained for a key and whether CT-10 is complete."""

    observation: SourceObservation
    complete: bool


@dataclass(slots=True)
class IntakeAuthority:
    """QMF-owned durable mapping from a CT-15 key to a canonical CT-10 identity."""

    writer: JournalWriter
    _keys: dict[IntakeKey, tuple[str, IntakeReservation]] = field(default_factory=lambda: {})

    @classmethod
    def resume(
        cls,
        journal: JournalStore,
        writer_id: WriterId,
        *,
        stream_name: str = "ct15-intake-authority",
    ) -> Result[IntakeAuthority]:
        """Validate the checked CT-13 stream and resume its single writer/high-water."""
        events = JournalReader(journal).read_checked(
            stream_name, for_world=journal.world, expected_start=0
        )
        if is_refusal(events):
            return events
        keys: dict[IntakeKey, tuple[str, IntakeReservation]] = {}
        for event in events.value:
            if event.event_type is not JournalEventType.DATA_QUALITY:
                continue
            payload = event.payload
            if payload.get("class") != _EVENT_CLASS:
                continue
            parsed = _parse_event(payload, journal.world)
            if is_refusal(parsed):
                return parsed
            action, key, fact_fp, observation_fp, observation = parsed.value
            current = keys.get(key)
            if action == _INTENT:
                if observation is None:
                    return _inconsistent_key(key)
                if current is not None:
                    if (
                        current[0] != fact_fp
                        or current[1].observation.fingerprint != observation.fingerprint
                    ):
                        return _inconsistent_key(key)
                    continue
                keys[key] = (fact_fp, IntakeReservation(observation, complete=False))
            else:
                if current is None or current[0] != fact_fp:
                    return _inconsistent_key(key)
                if current[1].observation.fingerprint.value != observation_fp:
                    return _inconsistent_key(key)
                keys[key] = (fact_fp, IntakeReservation(current[1].observation, complete=True))
        resumed = JournalWriter.resume(journal, writer_id, stream_name=stream_name)
        if is_refusal(resumed):
            return resumed
        return Ok(cls(writer=resumed.value, _keys=keys))

    def reserve(
        self,
        key: IntakeKey,
        observation: SourceObservation,
        *,
        instant: Instant,
    ) -> Result[IntakeReservation]:
        """Durably reserve an exact CT-10 row or return the earlier canonical row.

        Provider-fact identity excludes only receipt metadata (writer, sequence,
        receive-wall-time). A later retry with the same provider facts therefore
        reuses the original CT-10 value, while changed source facts under the same
        CT-15 key are refused.
        """
        valid = _validate_key_observation(key, observation, self.writer.world)
        if is_refusal(valid):
            return valid
        fact_fp = _fact_fingerprint(observation)
        if is_refusal(fact_fp):
            return fact_fp
        prior = self._keys.get(key)
        if prior is not None:
            if prior[0] != fact_fp.value:
                return _changed_fact(key, prior[0], fact_fp.value)
            return Ok(prior[1])

        persisted = self.writer.record_data_quality(
            _intent_payload(key, observation, fact_fp.value), instant=instant
        )
        if is_refusal(persisted):
            return persisted
        reservation = IntakeReservation(observation, complete=False)
        self._keys[key] = (fact_fp.value, reservation)
        return Ok(reservation)

    def complete(
        self,
        key: IntakeKey,
        observation: SourceObservation,
        *,
        instant: Instant,
    ) -> Result[None]:
        """Persist explicit completion after CT-10 admission and its acknowledgement."""
        valid = _validate_key_observation(key, observation, self.writer.world)
        if is_refusal(valid):
            return valid
        fact_fp = _fact_fingerprint(observation)
        if is_refusal(fact_fp):
            return fact_fp
        prior = self._keys.get(key)
        if prior is None or prior[0] != fact_fp.value:
            return _inconsistent_key(key)
        if prior[1].observation.fingerprint != observation.fingerprint:
            return policy_rejection(
                "intake_identity",
                "completion must acknowledge the exact CT-10 observation retained by its intent",
                source=key.source,
                source_native_id=key.source_native_id,
                revision=key.revision,
            )
        if prior[1].complete:
            return Ok(None)
        persisted = self.writer.record_data_quality(
            {
                "class": _EVENT_CLASS,
                "action": _COMPLETE,
                "complete": True,
                "source": key.source,
                "source_native_id": key.source_native_id,
                "revision": key.revision,
                "fact_fingerprint": fact_fp.value,
                "observation_fingerprint": observation.fingerprint.value,
            },
            instant=instant,
        )
        if is_refusal(persisted):
            return persisted
        self._keys[key] = (
            fact_fp.value,
            IntakeReservation(observation, complete=True),
        )
        return Ok(None)


def _intent_payload(
    key: IntakeKey, observation: SourceObservation, fact_fingerprint: str
) -> dict[str, object]:
    return {
        "class": _EVENT_CLASS,
        "action": _INTENT,
        "source": key.source,
        "source_native_id": key.source_native_id,
        "revision": key.revision,
        "fact_fingerprint": fact_fingerprint,
        "observation_fingerprint": observation.fingerprint.value,
        "observation": observation.to_row(),
    }


def _parse_event(
    payload: Mapping[str, object], world: object
) -> Result[tuple[str, IntakeKey, str, str, SourceObservation | None]]:
    action = payload.get("action")
    if action not in (_INTENT, _COMPLETE):
        return policy_rejection(
            "ct15_intake_authority", "a CT-15 authority event has a declared intent/complete action"
        )
    key = IntakeKey.try_create(
        payload.get("source"), payload.get("source_native_id"), payload.get("revision")
    )
    fact_fp = payload.get("fact_fingerprint")
    observation_fp = payload.get("observation_fingerprint")
    if is_refusal(key) or not isinstance(fact_fp, str) or not isinstance(observation_fp, str):
        return policy_rejection(
            "ct15_intake_authority", "a CT-15 authority event carries a valid key and fingerprints"
        )
    if action == _INTENT:
        observation = SourceObservation.from_row(payload.get("observation"))
        if is_refusal(observation):
            return observation
    else:
        if payload.get("complete") is not True or "observation" in payload:
            return policy_rejection(
                "ct15_intake_authority",
                "a completion event carries explicit complete=true and references its prior intent",
            )
        observation = Ok(None)
    if observation.value is not None:
        if observation.value.fingerprint.value != observation_fp:
            return policy_rejection(
                "ct15_intake_authority", "the durable CT-10 observation fingerprint does not verify"
            )
        valid = _validate_key_observation(key.value, observation.value, world)
        if is_refusal(valid):
            return valid
        actual_fact_fp = _fact_fingerprint(observation.value)
        if is_refusal(actual_fact_fp):
            return actual_fact_fp
        if actual_fact_fp.value != fact_fp:
            return policy_rejection(
                "ct15_intake_authority", "the durable provider-fact fingerprint does not verify"
            )
    return Ok((cast(str, action), key.value, fact_fp, observation_fp, observation.value))


def _validate_key_observation(
    key: IntakeKey, observation: SourceObservation, world: object
) -> Result[None]:
    if (key.source, key.source_native_id, key.revision) != (
        observation.source,
        observation.source_native_id,
        observation.revision,
    ):
        return invalid_input(
            "intake_identity",
            "the CT-15 key must match source, native id, and revision on the CT-10 observation",
        )
    if observation.world is not world:
        return policy_rejection(
            "world", "a CT-15 key authority is scoped to one world's CT-13 room"
        )
    return Ok(None)


def _fact_fingerprint(observation: SourceObservation) -> Result[str]:
    identity = observation.fp1_identity()
    identity.pop("receive_wall_time", None)
    identity.pop("writer", None)
    identity.pop("sequence", None)
    built = fingerprint(identity)
    if is_refusal(built):
        return built
    return Ok(built.value.value)


def _changed_fact(key: IntakeKey, prior: str, presented: str):
    return policy_rejection(
        "intake_identity",
        "the same CT-15 key was presented with different provider facts; issue a new revision",
        source=key.source,
        source_native_id=key.source_native_id,
        revision=key.revision,
        accepted_fact_fingerprint=prior,
        presented_fact_fingerprint=presented,
    )


def _inconsistent_key(key: IntakeKey):
    return policy_rejection(
        "ct15_intake_authority",
        "the checked CT-13 stream contains an inconsistent intent/completion for one CT-15 key",
        source=key.source,
        source_native_id=key.source_native_id,
        revision=key.revision,
    )
