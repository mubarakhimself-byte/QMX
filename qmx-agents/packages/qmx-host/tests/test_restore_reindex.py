"""Memory after a restore (B5): the copy holds no index, so the first start rebuilds it on its own
thread, logs `reindexed` only when the rebuild succeeds, and says recall is partial until then."""

from __future__ import annotations

import threading
from pathlib import Path

from qmx_engine.ledger import redact
from qmx_home import Layout, resolve
from qmx_home.versions import log_lines
from qmx_library.store import Store
from qmx_memory.engine import RecallEngine
from test_after_restore import backups_of, quick_copy, restored

LESSON = "the copy alone held this lesson about pod Z and its 9 day ATR"


def recalled(engine: RecallEngine) -> list[str]:
    return [hit.row_id for hit in engine.recall("pod Z lesson ATR", ("home",), 1_000)]


def reindexed(layout: Layout) -> int:
    return sum(line.get("kind") == "reindexed" for line in log_lines(layout))


def lesson_restored(tmp_path: Path) -> tuple[Layout, str]:
    """A folder restored from a copy that holds one lesson; the lesson's row."""
    layout = resolve(tmp_path / "QMX", create=True)
    with Store.open(layout.home / "library", redactor=redact) as store:
        engine = RecallEngine(store, home=layout.home / "memory")
        row = engine.write("home", "hub", {"tag": "lesson", "content": LESSON}).object_id
        engine.close()
    restored(layout, quick_copy(layout))
    return layout, row


def test_the_first_start_after_a_restore_rebuilds_memory_and_recall_finds_a_row_the_copy_held(
    tmp_path: Path,
) -> None:
    layout, row = lesson_restored(tmp_path)
    backups = backups_of(layout)

    with Store.open(layout.home / "library", redactor=redact) as store:
        engine = RecallEngine(store, home=layout.home / "memory")
        try:
            before = recalled(engine)
            thread = backups.reindex(lambda: engine.rebuild("all"), hindsight=False)
            assert thread is not None
            thread.join(30)
            after = recalled(engine)
            again = backups_of(layout).reindex(lambda: engine.rebuild("all"), hindsight=False)
        finally:
            engine.close()

    assert (before, after) == ([], [row])
    assert reindexed(layout) == 1
    assert again is None, "a restore already reindexed starts nothing"
    assert "recall is partial" not in backups.doctor_line().detail


def test_a_rebuild_that_fails_writes_no_reindexed_line_says_recall_is_partial_and_runs_again(
    tmp_path: Path,
) -> None:
    layout, row = lesson_restored(tmp_path)
    first = backups_of(layout)
    go = threading.Event()

    def broken() -> object:
        go.wait(30)
        raise OSError("the index file is locked")

    thread = first.reindex(broken, hindsight=True)
    assert thread is not None
    running = first.doctor_line().detail
    go.set()
    thread.join(30)
    failed = first.doctor_line().detail
    lines = reindexed(layout)

    second = backups_of(layout)
    with Store.open(layout.home / "library", redactor=redact) as store:
        engine = RecallEngine(store, home=layout.home / "memory")
        try:
            retried = second.reindex(lambda: engine.rebuild("all"), hindsight=False)
            assert retried is not None
            retried.join(30)
            found = recalled(engine)
        finally:
            engine.close()

    assert running.startswith(
        "recall is partial while QMX rebuilds its memory index after the restore; Hindsight "
        "starts its database and embeds every row again, which takes a while; "
    )
    assert failed.startswith(
        "recall is partial: the memory rebuild after the restore stopped (OSError: the index "
        "file is locked); QMX runs it again at the next start; "
    )
    assert lines == 0
    assert (reindexed(layout), found) == (1, [row])
