"""Each unit's one lifecycle (Part A slice A9, AD-115, AG-13): every move by every actor is
allowed or refused as the table says. Only his click promotes a unit; a risk rule may send a
stopped member back to paper, and never anywhere else."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from qml.lifecycle import (
    Actor,
    ActorKind,
    Event,
    MarketKey,
    Refusal,
    State,
    fold,
)

S = State
T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
HIM = Actor(ActorKind.HIS_CLICK, "operator")
JUDGE = Actor(ActorKind.JUDGE, "run:judge-7")
RISK = Actor(ActorKind.RISK_RULE, "node:vps-1")
KEY = MarketKey("dummy-trend-pullback", "v1", "fx.eurusd")
G_RECORD = "qmbr-g-pass"
"""The passing G safety record a draft names to reach paper on his click (AD-24)."""


def _event(
    n: int,
    from_state: State,
    to_state: State,
    by: Actor,
    *,
    version: str = "v1",
    clears: str | None = None,
    at: datetime | None = None,
    writer: str = "this-pc",
    evidence: str | None = None,
) -> Event:
    return Event(
        event_id=f"e{n}-{version}",
        unit_id=KEY.unit_id,
        version_ref=version,
        compiled_fingerprint="fp1:abc",
        market_id=KEY.market_id,
        from_state=from_state,
        to_state=to_state,
        by=by,
        reason="test",
        evidence_ref=evidence,
        at=at or T0 + timedelta(minutes=n),
        writer=writer,
        sequence=n,
        clears=clears,
    )


def _path(target: State, version: str = "v1") -> list[Event]:
    """Legal events that bring one version on one market to ``target``."""
    steps = {
        S.DRAFT: [],
        S.TESTED: [(S.DRAFT, S.TESTED, JUDGE)],
        S.PARKED: [(S.DRAFT, S.PARKED, JUDGE)],
        S.PAPER: [(S.DRAFT, S.TESTED, JUDGE), (S.TESTED, S.PAPER, HIM)],
        S.LIVE: [(S.DRAFT, S.TESTED, JUDGE), (S.TESTED, S.PAPER, HIM), (S.PAPER, S.LIVE, HIM)],
        S.STOPPED: [
            (S.DRAFT, S.TESTED, JUDGE),
            (S.TESTED, S.PAPER, HIM),
            (S.PAPER, S.LIVE, HIM),
            (S.LIVE, S.STOPPED, RISK),
        ],
        S.RETIRED: [(S.DRAFT, S.RETIRED, HIM)],
    }[target]
    return [_event(n, a, b, by, version=version) for n, (a, b, by) in enumerate(steps)]


def _attempt(start: State, to: State, by: Actor) -> list[Refusal]:
    before = _path(start)
    stop = before[-1].event_id if start is S.STOPPED else None
    move = _event(10, start, to, by, clears=stop, evidence=G_RECORD)
    folded = fold([*before, move])
    assert folded.applied[: len(before)] == tuple(before), "the path to the start state is legal"
    return [rejected.refusal for rejected in folded.rejected]


NOT_RETIRED = [state for state in S if state is not S.RETIRED]
ALLOWED = {
    (S.DRAFT, S.TESTED, ActorKind.JUDGE),
    (S.DRAFT, S.PARKED, ActorKind.JUDGE),
    (S.DRAFT, S.PAPER, ActorKind.HIS_CLICK),
    (S.TESTED, S.PAPER, ActorKind.HIS_CLICK),
    (S.PAPER, S.LIVE, ActorKind.HIS_CLICK),
    (S.PAPER, S.STOPPED, ActorKind.RISK_RULE),
    (S.LIVE, S.STOPPED, ActorKind.RISK_RULE),
    (S.STOPPED, S.STOPPED, ActorKind.RISK_RULE),
    (S.STOPPED, S.PAPER, ActorKind.RISK_RULE),
    (S.STOPPED, S.PAPER, ActorKind.HIS_CLICK),
    (S.STOPPED, S.LIVE, ActorKind.HIS_CLICK),
    (S.LIVE, S.PARKED, ActorKind.HIS_CLICK),
    (S.PAPER, S.PARKED, ActorKind.HIS_CLICK),
    *((state, S.RETIRED, ActorKind.HIS_CLICK) for state in NOT_RETIRED),
}
ACTORS = {
    ActorKind.JUDGE: Actor(ActorKind.JUDGE, "operator"),
    ActorKind.HIS_CLICK: HIM,
    ActorKind.RISK_RULE: Actor(ActorKind.RISK_RULE, "operator"),
    ActorKind.SYSTEM: Actor(ActorKind.SYSTEM, "operator"),
}


def test_every_move_by_every_actor_is_allowed_or_refused_as_the_table_says() -> None:
    """Every actor carries principal ``operator`` here, so only the table decides."""
    allowed = {
        (start, to, kind)
        for start, to, kind in itertools.product(S, S, ActorKind)
        if _attempt(start, to, ACTORS[kind]) == []
    }

    assert allowed == ALLOWED


TOWARD_TRADING = [
    (S.DRAFT, S.PAPER),
    (S.TESTED, S.PAPER),
    (S.PAPER, S.LIVE),
    (S.STOPPED, S.PAPER),
    (S.STOPPED, S.LIVE),
]
OTHERS = ["agent:copilot-1", "run:wf-9", "node:vps-1", "system", "", "Operator", "operator "]
BACK_TO_PAPER = (S.STOPPED, S.PAPER, ActorKind.RISK_RULE)


@pytest.mark.parametrize("principal", OTHERS)
def test_no_principal_but_operator_promotes_a_unit(principal: str) -> None:
    """A principal that is not his click makes one move toward trading: a risk rule sends a
    stopped member back to paper. Every other move toward paper or live, and every move to live,
    stays his."""
    moves = {
        (start, to, kind): _attempt(start, to, Actor(kind, principal))
        for (start, to), kind in itertools.product(TOWARD_TRADING, ActorKind)
    }

    assert {move for move, refusals in moves.items() if refusals == []} == {BACK_TO_PAPER}
    assert all(refusals for move, refusals in moves.items() if move != BACK_TO_PAPER)
    assert {
        move: refusals for move, refusals in moves.items() if move[1] is S.LIVE
    } == {move: [Refusal.NOT_OPERATOR] for move in moves if move[1] is S.LIVE}


def test_the_judge_never_moves_a_unit_to_paper() -> None:
    events = [*_path(S.TESTED), _event(10, S.TESTED, S.PAPER, JUDGE)]

    assert fold(events).state(KEY) is S.TESTED
    assert [r.refusal for r in fold(events).rejected] == [Refusal.NOT_OPERATOR]


def test_a_draft_reaches_paper_on_his_click() -> None:
    """A draft moves straight to paper on his click, on the safety half of G and no judge pass."""
    stamped = _event(0, S.DRAFT, S.PAPER, HIM, evidence=G_RECORD)

    folded = fold([stamped])

    assert (folded.state(KEY), folded.rejected) == (S.PAPER, ())


def test_no_g_record_no_paper() -> None:
    """The same click with no G record named is refused: paper needs the safety record."""
    unstamped = _event(0, S.DRAFT, S.PAPER, HIM)

    folded = fold([unstamped])

    assert (folded.state(KEY), [r.refusal for r in folded.rejected]) == (
        S.DRAFT,
        [Refusal.G_RECORD_MISSING],
    )


@pytest.mark.parametrize("node_clock", [timedelta(seconds=-50), timedelta(minutes=30)])
def test_a_later_stop_stays_in_force_whatever_the_two_clocks_say(node_clock: timedelta) -> None:
    """Stop A, his resume naming A, then stop B from the node, stamped before or after the resume
    by the node's own clock (B still follows A on that clock): B is never cleared by a click that
    named A."""
    live = _path(S.LIVE)
    first = _event(10, S.LIVE, S.STOPPED, RISK, writer="node")
    resume = _event(11, S.STOPPED, S.LIVE, HIM, clears=first.event_id)
    later = _event(12, S.LIVE, S.STOPPED, RISK, writer="node", at=resume.at + node_clock)
    folded = fold([*live, first, resume, later])

    assert folded.state(KEY) is S.STOPPED
    assert folded.latest_stop[KEY] == later.event_id


@pytest.mark.parametrize(
    ("clears", "refusals", "state"),
    [
        ("e10-v1", [Refusal.STOP_NOT_CLEARED], S.STOPPED),
        ("e12-v1", [], S.LIVE),
    ],
)
def test_the_latest_stop_from_one_writer_is_its_highest_sequence_when_its_clock_steps_back(
    clears: str, refusals: list[Refusal], state: State
) -> None:
    """Stop B (sequence 12) is stamped 5 seconds before stop A (sequence 10) by the same node."""
    live = _path(S.LIVE)
    first = _event(10, S.LIVE, S.STOPPED, RISK, writer="node")
    later = _event(12, S.LIVE, S.STOPPED, RISK, writer="node", at=first.at - timedelta(seconds=5))
    resume = _event(13, S.STOPPED, S.LIVE, HIM, clears=clears)
    folded = fold([*live, first, later, resume])

    assert folded.latest_stop[KEY] == "e12-v1"
    assert [r.refusal for r in folded.rejected] == refusals
    assert folded.state(KEY) is state


def test_between_two_writers_the_later_stop_in_fold_order_is_the_latest() -> None:
    live = _path(S.LIVE)
    one = _event(10, S.LIVE, S.STOPPED, RISK, writer="node-1")
    two = _event(11, S.STOPPED, S.STOPPED, RISK, writer="node-2")
    stale = _event(13, S.STOPPED, S.LIVE, HIM, clears=one.event_id)
    resume = _event(14, S.STOPPED, S.LIVE, HIM, clears=two.event_id)

    refused, resumed = fold([*live, one, two, stale]), fold([*live, one, two, resume])

    assert (refused.state(KEY), refused.latest_stop[KEY]) == (S.STOPPED, "e11-v1")
    assert [r.refusal for r in refused.rejected] == [Refusal.STOP_NOT_CLEARED]
    assert (resumed.state(KEY), resumed.rejected) == (S.LIVE, ())


def test_a_second_version_is_admitted_on_a_live_market_only_after_the_first_is_parked() -> None:
    v1_live = _path(S.LIVE)
    v2_tested = [
        _event(20 + i, e.from_state, e.to_state, e.by, version="v2")
        for i, e in enumerate(_path(S.TESTED))
    ]
    admit = _event(30, S.TESTED, S.PAPER, HIM, version="v2")
    refused = fold([*v1_live, *v2_tested, admit])
    park = _event(29, S.LIVE, S.PARKED, HIM)
    admitted = fold([*v1_live, *v2_tested, park, admit])

    assert [r.refusal for r in refused.rejected] == [Refusal.SECOND_VERSION]
    v2 = MarketKey(KEY.unit_id, "v2", KEY.market_id)
    assert (refused.state(KEY), refused.state(v2)) == (S.LIVE, S.TESTED)
    assert (admitted.state(KEY), admitted.state(v2)) == (S.PARKED, S.PAPER)


def test_a_replayed_journal_folds_to_the_same_answer() -> None:
    events = _path(S.STOPPED)

    once, twice = fold(events), fold([*events, *events])

    assert (twice.states, twice.applied, twice.rejected) == (once.states, once.applied, ())
