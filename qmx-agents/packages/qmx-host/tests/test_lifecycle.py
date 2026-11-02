"""This PC's lifecycle writer: the judge's move lands once, an illegal move never, and a spec
edit after a result is a counted try."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmf.core import is_refusal
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qml.lifecycle import Actor, ActorKind, Event, MarketKey, Refusal, State
from qmx_judge.judge import JudgedResult, Trade, Verdict, judge, land_judgement, parse_spec
from qmx_library.kinds import KindRefused
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal

from qmx_host.first_start import land_dummy
from qmx_host.host import (
    HostStore,
    LanderLibrary,
    open_store,
    record_judge_moves,
    register_checkers,
)
from qmx_host.lifecycle import LifecycleWriter, MoveRefused

OPERATOR = Principal("operator")
DUMMY = "dummy-trend-pullback"
DAY = 86_400 * 10**9
START = 1_735_689_600 * 10**9
NOW = 1_762_041_600 * 10**9
"""2025-11-02 00:00 UTC, the writer's fixed clock."""
SPEC = parse_spec(
    {
        "origin": "written",
        "claim": {"edge": "buys pullbacks in an uptrend"},
        "markets": "admitted",
        "preset": "shipped",
    }
)
EVIDENCE = {
    "random_entries": {"edge_ratio": "1.4", "p": "0.01"},
    "cost_stress": {"multiplier": "1.5", "expectancy_r": "0.2"},
    "walk_forward": {"efficiency": "0.7"},
}


@pytest.fixture
def store(tmp_path: Path) -> Iterator[HostStore]:
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as opened:
        register_checkers(opened)
        opened.lifecycle = LifecycleWriter(tmp_path / "journals", "pc", "test", clock=lambda: NOW)
        yield opened


def note(store: HostStore, item: str) -> str:
    return store.put(
        OPERATOR, Draft("note", item, item, fields={}), on=MAIN, expected_head=None
    ).object_id


def verdict_on_the_dummy(store: HostStore, edge: str) -> tuple[Verdict, list[JudgedResult]]:
    unit = cast(str, land_dummy(store))
    landed = note(store, "result")
    trades = tuple(
        Trade("fx.eurusd", START + day * DAY, Decimal(edge) + Decimal(1 if day % 2 else -1))
        for day in range(150)
    )
    result = JudgedResult(
        result_id=landed,
        run_id="qmbr-pc-1",
        status="finished",
        unit=unit,
        tester="qmb@0.1.0",
        zero_trades=False,
        trades=trades,
        markets=("fx.eurusd",),
        compiled_fp="fp1:sha256:dummy",
        evidence=EVIDENCE,
    )
    tries = [{"kind": "run", "state": "opened", "run_id": "qmbr-pc-1", "family": unit}]
    found = judge(
        SPEC,
        study=note(store, "study"),
        results=[result],
        tries=tries,
        principal="agent:chat",
        versions={},
    )
    return found, [result]


def land(store: HostStore, verdict: Verdict, results: list[JudgedResult]) -> str:
    library = LanderLibrary(store)
    return land_judgement(library, verdict, results=results, spec=SPEC, writer="operator").verdict


def rows(root: Path) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    for folder in stream_folders(root):
        lines = read_committed(folder)
        assert not is_refusal(lines)
        found += [dict(line.record) for line in lines.value if isinstance(line, JournalLine)]
    return found


def test_a_passing_verdict_on_the_draft_lands_one_tested_row_and_landing_again_adds_none(
    store: HostStore, tmp_path: Path
) -> None:
    found, results = verdict_on_the_dummy(store, "0.5")
    verdict = land(store, found, results)
    assert land(store, found, results) == verdict
    record_judge_moves(store, cast(LifecycleWriter, store.lifecycle), verdict)
    written = rows(tmp_path / "journals")
    body = cast(dict[str, object], written[0]["body"])

    assert store.get(OPERATOR, verdict).fields["overall"] == "pass"
    assert len(written) == 1
    assert (written[0]["kind"], written[0]["record_id"]) == ("lifecycle", body["event_id"])
    assert (body["unit_id"], body["market_id"], body["from"], body["to"]) == (
        DUMMY,
        "fx.eurusd",
        "draft",
        "tested",
    )
    assert body["by"] == {"kind": "judge", "principal": "agent:chat"}
    assert body["evidence_ref"] == verdict
    key = MarketKey(DUMMY, results[0].unit, "fx.eurusd")
    assert cast(LifecycleWriter, store.lifecycle).state(key) is State.TESTED


def test_a_failing_verdict_parks_the_draft(store: HostStore, tmp_path: Path) -> None:
    verdict = land(store, *verdict_on_the_dummy(store, "-0.3"))
    body = cast(dict[str, object], rows(tmp_path / "journals")[0]["body"])

    assert store.get(OPERATOR, verdict).fields["overall"] == "fail"
    assert (body["from"], body["to"]) == ("draft", "parked")


def move(unit: str, to: State, by: Actor, from_state: State = State.DRAFT) -> Event:
    return Event(
        event_id=f"move-{to}-{by.principal}",
        unit_id=DUMMY,
        version_ref=unit,
        compiled_fingerprint="fp1:sha256:dummy",
        market_id="fx.eurusd",
        from_state=from_state,
        to_state=to,
        by=by,
        reason="test",
        evidence_ref=None,
        at=datetime(2026, 11, 2, 12, tzinfo=UTC),
        writer="",
        sequence=0,
    )


def test_the_writer_refuses_a_move_fold_rejects_and_writes_nothing(
    store: HostStore, tmp_path: Path
) -> None:
    writer = cast(LifecycleWriter, store.lifecycle)
    unit = cast(str, land_dummy(store))
    judge_to_paper = move(unit, State.PAPER, Actor(ActorKind.JUDGE, "agent:chat"))

    with pytest.raises(MoveRefused) as refused:
        writer.record_move(judge_to_paper)

    assert (refused.value.refusal, str(refused.value)) == (
        Refusal.NOT_OPERATOR,
        "only his click moves a unit to paper",
    )
    assert rows(tmp_path / "journals") == []


def test_a_spec_edit_after_a_result_lands_one_try(store: HostStore) -> None:
    unit = cast(str, land_dummy(store))
    spec: JsonObject = {"origin": "written", "preset": "shipped", "markets": "admitted"}
    first = store.put(
        OPERATOR, Draft("study-spec", "study", "s", fields=spec), on=MAIN, expected_head=None
    )
    edited: JsonObject = {**spec, "markets": ["fx.eurusd"]}
    before = store.put(
        OPERATOR,
        Draft("study-spec", "study", "s", fields=edited),
        on=MAIN,
        expected_head=first.object_id,
    )
    result: JsonObject = {
        "run_id": "qmbr-pc-1",
        "status": "finished",
        "unit": unit,
        "study": before.object_id,
    }
    store.put(
        OPERATOR,
        Draft("backtest-result", "qmbr-pc-1", "r", fields=result),
        on=MAIN,
        expected_head=None,
    )
    after: JsonObject = {**edited, "preset": "old-qmx"}
    for _ in range(2):
        head = cast(tuple[str, int], store.head("study", MAIN))[0]
        store.put(
            OPERATOR, Draft("study-spec", "study", "s", fields=after), on=MAIN, expected_head=head
        )
    tries = [store.get(OPERATOR, t).fields for t in store.with_field("try", "kind", "spec_edit")]

    assert len(tries) == 1
    assert (tries[0]["state"], tries[0]["unit"], tries[0]["family"]) == ("recorded", unit, unit)


def test_a_study_spec_with_an_unknown_preset_is_refused(store: HostStore) -> None:
    spec: JsonObject = {"origin": "written", "preset": "lenient", "markets": "admitted"}

    with pytest.raises(KindRefused) as refused:
        store.put(
            OPERATOR, Draft("study-spec", "study", "s", fields=spec), on=MAIN, expected_head=None
        )

    assert str(refused.value) == (
        "check_failed: study-spec: preset is one of old-qmx, shipped, not 'lenient'"
    )
