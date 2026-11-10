"""This PC's lifecycle writer: the judge's move lands once, an illegal move never, and a spec
edit after a result is a counted try. Every run of a unit's lineage is one family, so the best
of many versions judged alone still counts them all."""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmf.core import fingerprint_bytes, is_refusal
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders
from qml.lifecycle import Actor, ActorKind, Event, MarketKey, Refusal, State
from qmx_judge.judge import JudgedResult, Trade, Verdict, judge, land_judgement, parse_spec
from qmx_judge.landing import Lander
from qmx_judge.runs import Landing, parse_bundle
from qmx_library.kinds import KindRefused
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store
from qmx_tools import DomainContext
from qmx_tools.functions import domain_functions

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
SPEC_FIELDS: JsonObject = {
    "origin": "written",
    "claim": {"edge": "buys pullbacks in an uptrend"},
    "markets": "admitted",
    "preset": "shipped",
}
SPEC = parse_spec(SPEC_FIELDS)
EVIDENCE = {
    "random_entries": {"fx.eurusd": {"edge_ratio": "1.4", "p": "0.01"}},
    "cost_stress": {"fx.eurusd": {"multiplier": "1.5", "expectancy_r": "0.2"}},
    "walk_forward": {"fx.eurusd": {"efficiency": "0.7"}},
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

    # RC-16's law names his click "promotes" and a rule's move "send", so the pin follows it.
    assert (refused.value.refusal, str(refused.value)) == (
        Refusal.NOT_OPERATOR,
        "only his click promotes a unit to paper; a risk rule may only send it to paper",
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


def version(store: Store, item: str, n: int) -> str:
    head = store.head(item, MAIN)
    draft = Draft("note", item, f"{item} v{n}", fields={"text": f"version {n}"})
    return store.put(
        OPERATOR, draft, on=MAIN, expected_head=None if head is None else head[0]
    ).object_id


def qmb_only(app_id: str, version: str) -> set[str]:
    return {"backtest-result"}


def clock() -> datetime:
    return datetime(2026, 11, 2, tzinfo=UTC)


def backtest(lander: Lander, unit: str, study: str, rs: list[Decimal], out: Path) -> str:
    """One run of `unit` through the real lander: its opened try, its result, its landed try."""
    ticket = lander.open("qmb", "0.1.0", "jobs/backtest.py", {"unit": unit, "study": study}, "x")
    assert ticket is not None
    trades = [
        {"trade_id": f"t{day}", "market_id": "fx.eurusd", "closed_at": START + day * DAY}
        | {"r": str(r)}
        for day, r in enumerate(rs)
    ]
    report = json.dumps({"trades": trades}).encode()
    folder = out / ticket.run_id
    folder.mkdir(parents=True)
    (folder / "report.json").write_bytes(report)
    bundle = parse_bundle(
        {
            "run_id": ticket.run_id,
            "status": "finished",
            "tester": {"app": "qmb", "version": "0.1.0"},
            "measures": {"trades": len(rs)},
            "labels": {"zero_trades": False, "fidelity": "bars"},
            "files": [
                {"slot": "report", "path": "report.json", "fp": fingerprint_bytes(report).value}
            ],
            "consumed": [],
        }
    )
    return lander.close(Landing(ticket, bundle, folder))


def test_the_best_of_30_versions_judged_alone_counts_30_tries(tmp_path: Path) -> None:
    """A weak +0.06R unit saved 20 times and varied into 10 more versions, each run once: the
    luckiest run judged through the judge door still answers for the whole lineage."""
    context = DomainContext(root=tmp_path / "home")
    store = context.library.store
    register_checkers(store)
    library = LanderLibrary(store)
    lander = Lander(library, "operator", "pc", qmb_only, clock, family_of=library.family_of)
    study = store.put(
        OPERATOR, Draft("study-spec", "study", "s", fields=SPEC_FIELDS), on=MAIN, expected_head=None
    ).object_id
    versions = [version(store, "unit", n) for n in range(20)]
    varied = [version(store, "unit-varied", n) for n in range(10)]
    store.relate(OPERATOR, varied[0], "variant-of", versions[3])
    draw = random.Random(0)  # noqa: S311 - a seeded fixture, not a secret
    runs: list[tuple[Decimal, str]] = []
    for unit in [*versions, *varied]:
        rs = [Decimal(f"{draw.gauss(0.06, 1):.4f}") for _ in range(150)]
        runs.append((sum(rs, Decimal(0)), backtest(lander, unit, study, rs, tmp_path / "runs")))
    best = max(runs)[1]

    judged = domain_functions(context)["backtest"]["backtest_judge_run"](results=[best])["result"]

    assert (judged["overall"], judged["raw_tries"], judged["effective_tries"]) == ("fail", 30, 30)
    assert judged["says"] == (
        "Fail by the shipped preset. fx.eurusd fails the try-corrected verdict: deflated Sharpe "
        "0.8265 over 30 effective tries (luck alone reaches 0.1699 per trade, this market 0.2477). "
        "Behind it: 30 tries, 30 effective."
    )
    tries = store.with_field("try", "kind", "run")
    assert {str(store.get(OPERATOR, found).fields["family"]) for found in tries} == {"unit"}
