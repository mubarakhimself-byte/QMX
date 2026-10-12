"""Story 41.3 — command idempotency and correlation provenance (FR-Q16)."""

from __future__ import annotations

from qma.wire import (
    DEDUP_WINDOW_REGISTRY_KEY,
    CommandDedupCursor,
    IdempotencyKey,
    WireEnvelope,
    idempotency_key_from_envelope,
)
from qma.wire.idempotency import IdempotencyError
from qmf.core.chrono import Duration, Instant
from qmf.core.refusal import Ok


def _instant(ns: int) -> Instant:
    result = Instant.try_create(ns)
    assert isinstance(result, Ok)
    return result.value


def _duration(ns: int) -> Duration:
    result = Duration.try_create(ns)
    assert isinstance(result, Ok)
    return result.value


def _key(producer_id: str = "client-a", msg_id: str = "cmd-1") -> IdempotencyKey:
    result = IdempotencyKey.try_create(producer_id=producer_id, id=msg_id)
    assert isinstance(result, Ok)
    return result.value


def test_dedup_window_registry_key_is_homed() -> None:
    assert DEDUP_WINDOW_REGISTRY_KEY == "wire.dedup_window"
    cursor = CommandDedupCursor(window=_duration(1_000_000_000))
    assert cursor.window_registry_key == DEDUP_WINDOW_REGISTRY_KEY


def test_same_producer_id_and_id_are_one_idempotent_command() -> None:
    cursor = CommandDedupCursor(window=_duration(10_000_000_000))
    key = _key()
    first = cursor.observe(key, now=_instant(1_000))
    second = cursor.observe(key, now=_instant(2_000))
    assert isinstance(first, Ok) and isinstance(second, Ok)
    assert first.value.disposition == "accept"
    assert second.value.disposition == "duplicate"
    assert second.value.is_idempotent_replay is True
    assert second.value.first_seen_at == first.value.first_seen_at
    assert second.value.window_registry_key == DEDUP_WINDOW_REGISTRY_KEY


def test_changed_pair_member_is_not_the_same_command() -> None:
    cursor = CommandDedupCursor(window=_duration(10_000_000_000))
    base = _key(producer_id="client-a", msg_id="cmd-1")
    other_producer = _key(producer_id="client-b", msg_id="cmd-1")
    other_id = _key(producer_id="client-a", msg_id="cmd-2")
    assert base.same_command_as(other_producer) is False
    assert base.same_command_as(other_id) is False

    assert isinstance(cursor.observe(base, now=_instant(1)), Ok)
    changed_producer = cursor.observe(other_producer, now=_instant(2))
    changed_id = cursor.observe(other_id, now=_instant(3))
    assert isinstance(changed_producer, Ok) and isinstance(changed_id, Ok)
    assert changed_producer.value.disposition == "accept"
    assert changed_id.value.disposition == "accept"


def test_idempotency_outside_dedup_window_is_not_duplicate() -> None:
    window = _duration(100)
    cursor = CommandDedupCursor(window=window)
    key = _key()
    assert isinstance(cursor.observe(key, now=_instant(0)), Ok)
    later = cursor.observe(key, now=_instant(101))
    assert isinstance(later, Ok)
    assert later.value.disposition == "accept"
    assert cursor.contains(key, now=_instant(101)) is True


def test_idempotency_key_from_envelope() -> None:
    env = WireEnvelope.try_create(
        v="1.0.0",
        type="start_mission",
        id="msg-9",
        producer_id="producer-9",
        correlation_id="corr-9",
        scope_path=[{"kind": "desk", "id": "d"}],
        payload={},
    )
    assert isinstance(env, Ok)
    key = idempotency_key_from_envelope(env.value.to_dict())
    assert isinstance(key, Ok)
    assert key.value == IdempotencyKey(producer_id="producer-9", id="msg-9")


def test_non_positive_dedup_window_refused() -> None:
    try:
        CommandDedupCursor(window=_duration(0))
    except IdempotencyError as exc:
        assert DEDUP_WINDOW_REGISTRY_KEY in str(exc)
    else:
        raise AssertionError("expected IdempotencyError")
