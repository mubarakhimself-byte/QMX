"""AD-18's memory port against every verb, over the library's rows (MEM)."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_engine.ports.memory import Hit
from qmx_library.principal import Principal
from qmx_library.port import Draft
from qmx_library.store import Store

from qmx_memory.engine import RecallEngine
from qmx_memory.fts import FtsIndex
from qmx_memory.retain import RetainWorker

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


@pytest.fixture
def engine(store: Store, tmp_path: Path) -> Iterator[RecallEngine]:
    built = RecallEngine(store, home=tmp_path, clock=lambda: NOW)
    try:
        yield built
    finally:
        built.close()


def lesson(engine: RecallEngine, content: str, **row: object) -> str:
    """One home-scope lesson row, the shape a chat's note has."""
    written = engine.write("home", "hub", {"tag": "lesson", "content": content, **row})
    return written.object_id


def test_recall_finds_a_live_row_and_leaves_out_a_closed_window(engine: RecallEngine) -> None:
    old = lesson(
        engine,
        "pod P broke when the ATR period was 14 days",
        valid_from=(NOW - timedelta(days=60)).isoformat(),
        valid_to=(NOW - timedelta(days=30)).isoformat(),
    )
    live = lesson(engine, "pod P needed a 20 day ATR period", valid_from=NOW.isoformat())

    today = {hit.row_id for hit in engine.recall("pod P ATR period", ("home",), 1_000)}

    assert today == {live}
    inside = {
        hit.row_id
        for hit in engine.recall(
            "pod P ATR period", ("home",), 1_000, now=NOW - timedelta(days=45)
        )
    }
    assert inside == {old}


def test_a_row_learnt_in_the_current_regime_outranks_the_same_row_from_another(
    engine: RecallEngine,
) -> None:
    flat = lesson(engine, "the break-out filter wants a 20 day ATR period")
    trend = lesson(engine, "the break-out filter wants a 20 day ATR period")
    engine.store.annotate(engine.store.engine, trend, {"regime": ["trend"]})
    engine.rebuild("all")

    plain = engine.recall("break-out filter ATR period", ("home",), 1_000)
    matching = engine.recall("break-out filter ATR period", ("home",), 1_000, regime=("trend",))

    assert {hit.row_id for hit in plain} == {flat, trend}
    first = matching[0]
    assert first.row_id == trend
    assert first.score == pytest.approx(dict(_scores(plain))[trend] * 1.25, rel=1e-6)


def test_forget_archives_the_row_and_a_rebuild_does_not_bring_it_back(
    engine: RecallEngine,
) -> None:
    kept = lesson(engine, "the library stores a memory row as its own object")
    gone = lesson(engine, "a forgotten lesson about pod Q and its 9 day ATR")

    assert engine.forget([gone]) == 1
    assert engine.recall("forgotten lesson pod Q ATR", ("home",), 1_000) == []

    engine.rebuild("all")

    assert {hit.row_id for hit in engine.recall("pod Q ATR lesson", ("home",), 1_000)} == set()
    assert {hit.row_id for hit in engine.recall("memory row object", ("home",), 1_000)} == {kept}


def test_check_built_answers_by_intent_key_and_a_dead_end_stops_the_same_check(
    engine: RecallEngine,
) -> None:
    key = "build:dataset:aapl-1d:2026-10"
    built = engine.write(
        "home",
        "hub",
        {"tag": "built", "content": "the aapl 1d dataset", "intent_key": key},
    )
    dead = engine.write(
        "home",
        "hub",
        {
            "tag": "dead_end",
            "content": "the aapl build failed on a missing calendar",
            "intent_key": "build:dataset:msft-1d:2026-10",
        },
    )

    assert engine.check_built(key) == [built.object_id]
    dead_ends = engine.check_dead_end("build:dataset:msft-1d:2026-10")

    assert [hit.row_id for hit in dead_ends] == [dead.object_id]
    assert engine.check_built("build:dataset:never-made") == []


def test_snapshot_is_frozen_with_the_rows_it_carried(engine: RecallEngine) -> None:
    first = lesson(
        engine,
        "pod P runs a 20 day ATR",
        when_to_use="before tuning pod P",
        learned_at=(NOW - timedelta(hours=2)).isoformat(),
    )
    second = lesson(
        engine,
        "the hub home keeps the operator's rows",
        learned_at=(NOW - timedelta(hours=1)).isoformat(),
    )

    frozen = engine.snapshot(("home",), 4_000, ("what did we learn about pod P?",))

    assert frozen.row_ids == (second, first)
    assert frozen.text.splitlines()[0] == "? what did we learn about pod P?"
    assert "20 day ATR" in frozen.text
    assert len(frozen.version) == 16


def test_a_quarantined_source_down_weights_the_row(engine: RecallEngine) -> None:
    source = lesson(engine, "the lab run used a stale dataset")
    row = engine.write(
        "home",
        "hub",
        {"tag": "lesson", "content": "the break-out filter wants a 20 day ATR"},
        derived_from=[source],
    )
    plain = engine.recall("break-out filter ATR", ("home",), 1_000)[0]

    item = engine.store.get(engine.store.engine, source).item
    engine.store.mark(Principal("operator"), item, True, "the lab run used a stale dataset")
    tainted = engine.recall("break-out filter ATR", ("home",), 1_000)[0]

    assert tainted.row_id == row.object_id
    assert tainted.provenance["tainted"] is True
    assert tainted.score == pytest.approx(plain.score * 0.5, rel=1e-6)


def test_note_writes_a_run_scoped_row_the_run_owns(engine: RecallEngine) -> None:
    row_id = engine.note("run-7", {"tag": "procedure", "content": "resume at step 4"})

    view = engine.store.get(engine.store.engine, row_id)

    assert view.fields["scope"] == "run"
    assert engine.recall("resume at step 4", ("run",), 1_000)[0].row_id == row_id
    assert engine.recall("resume at step 4", ("home",), 1_000) == []


def test_a_session_digest_names_the_session_item_it_came_from(engine: RecallEngine) -> None:
    session = engine.store.put(
        engine.store.engine,
        Draft(
            "session",
            item="chat-1",
            title="pod P tuning",
            fields={
                "session_id": "chat-1",
                "home": {"kind": "lab", "project_id": "qmx"},
                "created": NOW.isoformat(),
            },
        ),
        on="refs/sessions/chat-1",
        expected_head=None,
    )
    blocks: Sequence[Mapping[str, object]] = [
        {"role": "user", "text": "check pod P's ATR setting"},
        {"role": "assistant", "text": "pod P needs 20 days, not 14"},
    ]
    worker = RetainWorker(
        engine,
        blocks=lambda chat: blocks,
        session_item=lambda chat: session.object_id,
        clock=lambda: NOW,
    )

    written = worker.turn_ended("chat-1")

    assert written is not None
    view = engine.store.get(engine.store.engine, written)
    assert view.fields["tag"] == "lesson"
    edges = engine.store.edges_of(written, reverse=False)
    assert any(edge[1] == "derived-from" and edge[2] == session.object_id for edge in edges)
    assert engine.recall("pod P ATR 20 days", ("home",), 1_000)[0].row_id == written
    assert worker.turn_ended("chat-1") is None


def test_every_port_verb_answers_over_the_fts_fallback_too(
    store: Store, tmp_path: Path
) -> None:
    fallback = RecallEngine(store, home=tmp_path, clock=lambda: NOW)
    try:
        row = lesson(fallback, "a fallback answers when Hindsight is stopped")
        assert isinstance(fallback.fallback, FtsIndex)
        assert fallback.fallback.count() == 1
        assert [hit.row_id for hit in fallback.recall("Hindsight stopped", ("home",), 500)] == [
            row
        ]
        assert fallback.snapshot(("home",), 500).row_ids == (row,)
        assert fallback.check_built("build:none:2026") == []
        assert fallback.search_runs("nothing") == []
        assert fallback.feedback((row,), "pass") is None
        assert fallback.consolidate("no-such-run", "home").added == 0
    finally:
        fallback.close()


def test_a_run_consolidates_into_one_procedure_row_derived_from_its_own(
    engine: RecallEngine,
) -> None:
    first = engine.note("run-9", {"tag": "lesson", "content": "the calendar was missing"})
    second = engine.note("run-9", {"tag": "lesson", "content": "retry after a calendar import"})

    done = engine.consolidate("run-9", "home")
    rows = engine.recall("calendar", ("home",), 1_000)

    assert done.added == 1
    assert len(rows) == 1
    edges = engine.store.edges_of(rows[0].row_id, reverse=False)
    targets = {edge[2] for edge in edges if edge[1] == "derived-from"}
    assert targets == {first, second}


def _scores(hits: Sequence[Hit]) -> dict[str, float]:
    return {hit.row_id: hit.score for hit in hits}


def _only(engine: RecallEngine) -> str:
    found = engine.store.with_field("memory-row", "scope", "home")
    assert len(found) == 1
    return found[0]


def test_the_store_reads_a_memory_row_kind_that_keeps_its_window() -> None:
    from qmx_library.kinds import roster  # noqa: PLC0415

    found = roster()["memory-row"]

    assert "valid_from" in found.validator.schema["properties"]
    assert "regime" in found.annotations
    assert Principal("engine", "test").who == "engine"
