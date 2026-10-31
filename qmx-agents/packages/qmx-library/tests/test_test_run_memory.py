"""A test run's memory is sample data. At its summary its run-scope rows, and any row derived only
from them, are archived with its other samples, so recall and `check_built` leave them out; a live
run's rows, and a row derived from both runs, stay. Over the real store, with memory's FTS
fallback and no index."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_engine.ports.library import JsonObject, RunSummary
from qmx_memory.engine import RecallEngine

from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.principal import state_ref
from qmx_library.store import Store

NOW = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)


@pytest.fixture
def opened(tmp_path: Path) -> Generator[tuple[Store, RecallEngine]]:
    with Store.open(tmp_path / "library", redactor=redact) as store:
        memory = RecallEngine(store, home=tmp_path / "memory", clock=lambda: NOW)
        try:
            yield store, memory
        finally:
            memory.close()


def archived(store: Store, object_id: str) -> bool:
    item = store.get(store.engine, object_id).item
    found = store.head(item, state_ref(item))
    return found is not None and found[0] == "archived"


def summarized(store: Store, run_id: str, mode: str) -> None:
    summary = RunSummary(
        run_id, "clips", "obj", "live" if mode == "live" else "test", "passed",
        None, {}, {}, None, "operator", False,
    )  # fmt: skip
    EngineLibraryAdapter(store).put_run_summary(summary, principal=f"run:{run_id}")


def test_a_test_runs_rows_and_rows_derived_only_from_them_are_archived_at_its_summary(
    opened: tuple[Store, RecallEngine],
) -> None:
    store, memory = opened
    note: JsonObject = {"tag": "procedure", "keywords": ["grade", "working-state"]}
    tested = memory.note("test-run", note | {"content": "grade step working state from a test"})
    folded = memory.consolidate("test-run", "workflow", "clips")
    lived = memory.note("live-run", note | {"content": "grade step working state from a live run"})
    built = {"tag": "built", "content": "the clippings card"}
    test_built = memory.write(
        "workflow", "clips", built | {"intent_key": "key-test"}, derived_from=[tested]
    ).object_id
    live_built = memory.write(
        "workflow", "clips", built | {"intent_key": "key-live"}, derived_from=[lived]
    ).object_id
    mixed = memory.write(
        "workflow", "clips", {"tag": "lesson", "content": "both"}, derived_from=[tested, lived]
    ).object_id
    before = sorted(hit.row_id for hit in memory.recall("grade working state", ("run",), 10_000))

    summarized(store, "test-run", "test")
    summarized(store, "live-run", "live")
    (consolidated,) = [
        oid for oid in store.with_field("memory-row", "scope", "workflow")
        if store.get(store.engine, oid).fields.get("tag") == "procedure"
    ]  # fmt: skip

    assert folded.added == 1
    assert before == sorted([tested, lived])
    assert [hit.row_id for hit in memory.recall("grade working state", ("run",), 10_000)] == [lived]
    assert (memory.check_built("key-test"), memory.check_built("key-live")) == ([], [live_built])
    assert [archived(store, oid) for oid in (tested, consolidated, test_built)] == [True] * 3
    assert [archived(store, oid) for oid in (lived, live_built, mixed)] == [False] * 3


def test_his_note_derived_from_a_test_runs_row_stays_visible(
    opened: tuple[Store, RecallEngine],
) -> None:
    store, memory = opened
    tested = memory.note("test-run", {"tag": "lesson", "content": "a test run's lesson"})
    library = EngineLibraryAdapter(store)
    note = library.put_artifact(
        b"what I took from that lesson", "note", {}, run_id="chat-1", principal="run:chat-1"
    )
    his = note.object_id
    store.relate(store.engine, his, "derived-from", tested)

    summarized(store, "test-run", "test")

    assert (archived(store, tested), archived(store, his)) == (True, False)
