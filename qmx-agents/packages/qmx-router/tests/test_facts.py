"""What the two pools agree on (E53): the newest fact wins, and one key's concurrency is shared.

Two hosts learn different things about the same account. The rule is not a vote and not a merge by
kind: the fact observed later replaces the one observed earlier, whichever machine sent it, and a
message that crossed a newer one in flight loses. Concurrency is carried beside the facts as live
leases, so a machine that crashed mid-request stops counting when its lease lapses.
"""

from __future__ import annotations

import json

import pytest

from qmx_router.facts import (
    EVERY_MODEL,
    Fact,
    FactStore,
    LeaseRow,
    State,
    close,
)


class Clock:
    def __init__(self, at: float = 1_800_000_000.0) -> None:
        self.at = at

    def __call__(self) -> float:
        return self.at

    def tick(self, seconds: float) -> None:
        self.at += seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


def _fact(
    state: str = "cooling",
    *,
    until: float | None = 1_800_003_600.0,
    observed_at: float = 1_800_000_000.0,
    site: str = "pc",
    account: str = "openrouter#1",
    model: str = EVERY_MODEL,
    reading: float | None = None,
) -> Fact:
    return Fact(
        account=account,
        model=model,
        state=state,  # type: ignore[arg-type]
        until=until,
        reading=reading,
        observed_at=observed_at,
        site=site,
    )


def test_the_newest_fact_wins(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    assert store.apply(_fact("cooling", observed_at=100.0)) is True
    assert store.apply(_fact("open", until=None, observed_at=200.0)) is True
    assert store.state("openrouter#1", EVERY_MODEL) == ("open", None)


def test_an_older_fact_that_arrives_late_loses(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.apply(_fact("benched", until=None, observed_at=200.0))
    assert store.apply(_fact("open", until=None, observed_at=100.0)) is False
    assert store.state("openrouter#1", EVERY_MODEL) == ("benched", None)
    assert store.accepted == 1


def test_one_clock_two_machines_still_agree(clock: Clock) -> None:
    left = FactStore("a", clock=clock)
    right = FactStore("b", clock=clock)
    left.merge(State(facts=(_fact("cooling", site="a"),)))
    right.merge(State(facts=(_fact("benched", until=None, site="b"),)))
    left.merge(right.snapshot())
    right.merge(left.snapshot())
    assert left.snapshot().facts == right.snapshot().facts
    assert left.state("openrouter#1", EVERY_MODEL)[0] == "benched"


def test_a_passed_deadline_reads_probing(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.apply(_fact("cooling", until=1_800_000_100.0))
    clock.tick(200)
    assert store.state("openrouter#1", EVERY_MODEL) == ("probing", 1_800_000_100.0)


def test_a_model_fact_wins_over_the_accounts(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.merge(
        State(
            facts=(
                _fact("benched", until=None),
                _fact("open", until=None, model="claude/haiku", observed_at=1_800_000_050.0),
            )
        )
    )
    assert store.state("openrouter#1", "claude/haiku") == ("open", None)
    assert store.state("openrouter#1", "claude/opus") == ("benched", None)


def test_shared_concurrency_counts_live_leases_only(clock: Clock) -> None:
    pc = FactStore("pc", clock=clock)
    node = FactStore("node", clock=clock)
    pc.hold("openrouter#1", "pc:1", clock() + 60)
    node.merge(pc.snapshot())
    assert node.leases("openrouter#1") == 1
    assert node.room("openrouter#1", ceiling=2) is True
    pc.hold("openrouter#1", "pc:2", clock() + 60)
    node.merge(pc.snapshot())
    assert node.leases("openrouter#1") == 2
    assert node.room("openrouter#1", ceiling=2) is False
    clock.tick(120)
    assert node.leases("openrouter#1") == 0
    assert node.room("openrouter#1", ceiling=2) is True


def test_a_lease_renewed_elsewhere_is_not_shortened(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.hold("a#1", "pc:1", clock() + 60)
    store.hold("a#1", "pc:1", clock() + 30)
    assert store.leases("a#1") == 1
    assert store.snapshot().leases[0].expires_at == clock() + 60


def test_a_lease_dropped_is_no_longer_counted(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.hold("a#1", "pc:1", clock() + 60)
    store.drop("a#1", "pc:1")
    assert store.leases("a#1") == 0


def test_one_sync_carries_facts_and_leases(clock: Clock) -> None:
    pc = FactStore("pc", clock=clock)
    pc.apply(_fact("cooling"))
    pc.hold("openrouter#1", "pc:1", clock() + 60)
    document = json.loads(json.dumps(pc.snapshot().document()))
    node = FactStore("node", clock=clock)
    assert node.merge(State.from_document(document)) == 1
    assert node.state("openrouter#1", EVERY_MODEL)[0] == "cooling"
    assert node.leases("openrouter#1") == 1


def test_a_message_with_a_bad_row_drops_it_and_keeps_the_rest(clock: Clock) -> None:
    store = FactStore("node", clock=clock)
    taken = store.merge(
        State.from_document(
            {
                "facts": [
                    {"account": "a#1", "model": "", "state": "open", "observed_at": 5},
                    {"account": "", "state": "open", "observed_at": 5},
                    {"account": "a#1", "state": "not-a-state", "observed_at": 5},
                    "not-a-row",
                ],
                "leases": [{"account": "a#1", "holder": "h", "expires_at": 9_999_999_999}],
            }
        )
    )
    assert taken == 1
    assert store.leases("a#1") == 1


def test_a_readings_number_survives_a_cooldown(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.apply(_fact("cooling", until=1_800_000_600.0, reading=0.42, observed_at=10.0))
    assert store.reading("openrouter#1", "claude/haiku") is None
    clock.tick(700)
    assert store.reading("openrouter#1", "claude/haiku") == 0.42


def test_close_stamps_the_machines_own_clock(clock: Clock) -> None:
    stamped = close("a#1", EVERY_MODEL, "open", site="pc", clock=clock)
    assert stamped.observed_at == 1_800_000_000.0
    assert stamped.site == "pc"


def test_a_state_document_round_trips() -> None:
    state = State(facts=(_fact("cooling"),), leases=(LeaseRow("a#1", "pc:1", 99.0),))
    assert State.from_document(state.document()) == state


def test_leases_are_counted_per_account(clock: Clock) -> None:
    store = FactStore("pc", clock=clock)
    store.hold("a#1", "pc:1", clock() + 60)
    store.hold("a#1", "pc:2", clock() + 60)
    store.hold("a#2", "pc:3", clock() + 60)
    assert store.leases("a#1") == 2
    assert store.leases("a#2") == 1
