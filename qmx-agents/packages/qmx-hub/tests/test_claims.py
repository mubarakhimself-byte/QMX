"""Intent claims on the Hub: compare-and-swap with expiry, one renewal per heartbeat, the sweep,
and the local fallback when the Hub cannot be reached (Library AD-24, engine AD-27)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.port import Claim, LibraryRefused
from qmx_library.store import Store

from qmx_hub.claims import acquire, held_for, renew, sweep

KEY = "fingerprint:build:paper-17"


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as opened:
        yield opened


class Unreachable:
    def claim(self, intent_key: str, run_id: str, ttl: int) -> Claim:
        raise LibraryRefused("storage_failure", "the tailnet is down")


def test_a_claim_is_granted_then_held_by_the_other_run(store: Store) -> None:
    first = acquire(store, None, intent_key=KEY, run_id="run-a", ttl=60)
    second = acquire(store, None, intent_key=KEY, run_id="run-b", ttl=60)

    assert (first.claim.granted, first.where) == (True, "local")
    assert second.claim.granted is False
    assert second.claim.run_id == "run-a"
    holder = held_for(store, KEY)
    assert holder is not None
    assert holder[0] == "run-a"


def test_a_claim_past_its_ttl_is_taken_by_the_next_caller(tmp_path: Path) -> None:
    moment = [datetime(2026, 10, 21, 12, 0, tzinfo=UTC)]
    with Store.open(
        tmp_path / "server", redactor=redact, name="server", wall=lambda: moment[0]
    ) as store:
        held = store.claim(store.engine, KEY, "run-a", 60)
        moment[0] = moment[0] + timedelta(seconds=61)
        taken = store.claim(store.engine, KEY, "run-b", 60)

    assert held.granted is True
    assert taken.granted is True
    assert taken.run_id == "run-b"


def test_renewal_extends_every_claim_in_one_call_and_the_sweep_prunes(store: Store) -> None:
    store.claim(store.engine, KEY, "run-a", 60)
    store.claim(store.engine, "fingerprint:build:paper-18", "run-a", 60)
    store.claim(store.engine, "fingerprint:build:paper-19", "run-b", 1)

    renewed = renew(store, "run-a", 600)
    pruned = sweep(store)

    assert renewed == ["fingerprint:build:paper-17", "fingerprint:build:paper-18"]
    held = store.claim_holder(KEY)
    assert held is not None
    assert held[0] == "run-a"
    assert pruned == 0


def test_an_unreachable_hub_claims_locally_and_says_so(store: Store) -> None:
    reached = acquire(store, Unreachable(), intent_key=KEY, run_id="run-a", ttl=60)

    assert (reached.claim.granted, reached.where) == (True, "local")
    assert store.claim_holder(KEY) is not None


def test_release_is_the_holders_alone(store: Store) -> None:
    store.claim(store.engine, KEY, "run-a", 60)

    store.release(store.engine, KEY, "run-b")
    assert store.claim_holder(KEY) is not None
    store.release(store.engine, KEY, "run-a")
    assert store.claim_holder(KEY) is None
