"""Marks derived at read, hypothesis status, locators and reads as of a date (LIB2)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_engine.triggers.preflight import Blocked, quarantined_input

from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.port import Draft, JsonObject, LibraryRefused, Relation
from qmx_library.principal import Principal
from qmx_library.status import Status, status
from qmx_library.store import Store

OPERATOR = Principal("operator")
ALICE = Principal("agent", "alice")
START = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(tmp_path: Path, clock: Clock) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=clock) as opened:
        yield opened


def put(
    store: Store,
    kind: str,
    item: str,
    relations: list[Relation] | None = None,
    fields: JsonObject | None = None,
    title: str = "",
) -> str:
    found = store.head(item, "main")
    draft = Draft(kind, item, title or item, fields=fields or {}, relations=relations or [])
    head = None if found is None else found[0]
    return store.put(OPERATOR, draft, on="main", expected_head=head).object_id


def result(store: Store, item: str, on: str, outcome: str, tests: str | None = None) -> str:
    relations: list[Relation] = [("consumed", on)]
    if tests is not None:
        relations.append(("tests", tests))
    return put(store, "backtest-result", item, relations, {"outcome": outcome})


def test_a_quarantine_shows_downstream_with_its_path_and_clearing_restores_it(
    store: Store,
) -> None:
    r12 = put(store, "dataset", "r12")
    run = put(store, "note", "run-notes", [("derived-from", r12)])
    res = put(store, "backtest-result", "res", [("consumed", r12)])
    memory = put(store, "note", "lesson", [("derived-from", res), ("cites", run)])
    elsewhere = put(store, "note", "elsewhere", [("cites", res)])

    store.mark(OPERATOR, "r12", True, "feed corrected upstream")

    seen = store.marks(OPERATOR, memory)
    assert (seen.worst, seen.path, seen.reason) == (
        "quarantined",
        (memory, res, r12),
        "feed corrected upstream",
    )
    assert store.marks(OPERATOR, res).label == f"built on quarantined input: {res} -> {r12}"
    assert store.marks(OPERATOR, r12).label == "quarantined"
    assert store.marks(OPERATOR, elsewhere).worst is None

    store.mark(OPERATOR, "r12", False, "checked again")
    assert store.marks(OPERATOR, memory).worst is None
    assert store.marks(OPERATOR, memory).path == ()


def test_only_the_operator_marks(store: Store) -> None:
    put(store, "dataset", "r12")
    with pytest.raises(LibraryRefused, match=r"^ref_not_owned:"):
        store.mark(ALICE, "r12", True, "an agent thinks so")
    with pytest.raises(LibraryRefused, match=r"^not_found:"):
        store.mark(OPERATOR, "nothing", True, "no such item")


def test_superseded_and_corrected_are_computed_without_a_stored_mark(store: Store) -> None:
    v1 = put(store, "dataset", "feed")
    res = result(store, "res", v1, "supports")
    assert store.marks(OPERATOR, res).worst is None

    put(store, "dataset", "feed", title="feed v2")
    assert (store.marks(OPERATOR, res).worst, store.marks(OPERATOR, res).path) == (
        "superseded",
        (res, v1),
    )

    fix = put(store, "dataset", "feed-fix")
    store.relate(OPERATOR, fix, "replaces", v1)
    assert store.marks(OPERATOR, res).worst == "corrected"


def test_a_book_reads_the_mark_of_the_pod_compiled_to_it(store: Store) -> None:
    feed = put(store, "dataset", "feed")
    pod = put(store, "note", "pod-notes", [("uses", feed)])
    book = put(store, "note", "book-notes")
    store.relate(OPERATOR, pod, "compiles-to", book)
    store.mark(OPERATOR, "feed", True, "bad ticks")
    assert store.marks(OPERATOR, book).path == (book, pod, feed)


def test_a_hypothesis_supported_only_by_quarantined_results_is_open_until_cleared(
    store: Store,
) -> None:
    idea = put(store, "hypothesis", "idea", fields={"statement": "momentum holds in Asia"})
    r12 = put(store, "dataset", "r12")
    clean = put(store, "dataset", "clean")
    first = result(store, "res-1", r12, "supports", idea)
    second = result(store, "res-2", r12, "supports", idea)
    result(store, "res-3", clean, "inconclusive", idea)
    assert status(store, OPERATOR, "idea").status == "supported"

    store.mark(OPERATOR, "r12", True, "feed corrected upstream")
    found = status(store, OPERATOR, "idea")
    assert (found.status, set(found.ignored)) == ("open", {first, second})

    store.mark(OPERATOR, "r12", False, "checked again")
    assert status(store, OPERATOR, "idea").status == "supported"


def test_status_by_regime_and_prose_counts_for_nothing(store: Store) -> None:
    feed = put(store, "dataset", "feed")
    prose = Draft(
        "hypothesis", "said", "said", "supported, everyone agrees", {"statement": "it works"}
    )
    store.put(OPERATOR, prose, on="main", expected_head=None)
    assert status(store, OPERATOR, "said") == Status("open")

    idea = put(store, "hypothesis", "idea", fields={"statement": "carry pays"})
    low = result(store, "res-low", feed, "supports", idea)
    high = result(store, "res-high", feed, "refutes", idea)
    store.annotate(OPERATOR, low, {"tags": ["regime:low-vol"]})
    store.annotate(OPERATOR, high, {"tags": ["regime:high-vol"]})
    found = status(store, OPERATOR, "idea")
    assert (found.status, dict(found.by_regime)) == (
        "mixed",
        {"high-vol": "refuted", "low-vol": "supported"},
    )


def test_a_relation_carries_a_locator_and_a_bad_one_is_refused(store: Store) -> None:
    video = put(store, "source", "talk")
    note = put(store, "note", "clip", [("derived-from", video, {"seconds": 754})])
    assert store.get(OPERATOR, note).locators == {video: {"seconds": 754}}
    with pytest.raises(LibraryRefused, match=r"^schema_invalid:"):
        put(store, "note", "bad", [("derived-from", video, {"minute": 12})])


def test_reads_as_of_a_date_answer_with_the_older_version(store: Store, clock: Clock) -> None:
    first = put(store, "note", "plan", title="plan alpha")
    then = clock.now
    later = put(store, "note", "plan", title="plan omega")
    extra = put(store, "note", "extra")
    store.relate(OPERATOR, later, "related-to", extra)

    assert store.resolve(OPERATOR, "plan") == later
    assert store.resolve(OPERATOR, "plan", as_of=then) == first
    assert [h.object_id for h in store.search(OPERATOR, "plan", as_of=then)] == [first]
    assert store.search(OPERATOR, "omega", as_of=then) == []
    assert store.walk(OPERATOR, [later], as_of=then) == []
    with pytest.raises(LibraryRefused, match=r"^not_found:"):
        store.get(OPERATOR, later, as_of=then)
    assert store.get(OPERATOR, first, as_of=1).title == "plan alpha"


def test_preflight_refuses_a_version_built_on_a_quarantined_input(store: Store) -> None:
    adapter = EngineLibraryAdapter(store)
    feed = put(store, "dataset", "feed")
    flow = put(store, "note", "flow", [("uses", feed)])
    assert quarantined_input(flow, adapter) is None

    store.mark(OPERATOR, "feed", True, "bad ticks")
    assert quarantined_input(flow, adapter) == Blocked(
        "config", "quarantined_input", f"{flow} is built on quarantined input: {flow} -> {feed}"
    )
