"""Kind-file checks (Part A AD-112, Level 0 AD-29): a refusal names every problem with the first
message as its text, a kind file's checks run on the event they name, and a check that applies
with no registered checker refuses. The checkers here are stand-ins; the Library imports no QML."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import JsonValue
from qmx_engine.ledger import redact

from qmx_library.kinds import KindRefused, Problem
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store

OPERATOR = Principal("operator")
TWO = [
    Problem("one is wrong", ("/a",), "check_failed"),
    Problem("two too", ("/b",), "check_failed"),
]
ENTRY: dict[str, JsonValue] = {"entry": {"schema": "qmx.entry/1"}}
UNIT: dict[str, JsonValue] = {
    "schema": "qmx.unit/1",
    "unit_id": "u",
    "family_id": "f",
    "claim_card": {"idea": "an idea", "sources": [], "written_at": "2026-11-01"},
    "markets": [],
    "streams": [],
    "direction": "long",
    "logic": {},
    "exit_set": [],
    "halts": {},
    "reads": [],
    "numbers": {},
    "pins": [],
}


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(
        tmp_path / "library", redactor=redact, wall=lambda: datetime(2026, 11, 1, tzinfo=UTC)
    ) as opened:
        yield opened


def fails(fields: JsonObject) -> list[Problem]:
    return TWO


def passes(fields: JsonObject) -> list[Problem]:
    return []


def put(store: Store, kind: str, item: str, fields: dict[str, JsonValue]) -> None:
    draft = Draft(kind, item, item, fields=fields)
    store.put(OPERATOR, draft, on=drafts_ref(item), expected_head=None)


def test_a_refusal_keeps_the_first_message_and_lists_every_problem(store: Store) -> None:
    with pytest.raises(KindRefused) as refused:
        put(store, "component", "c", {"component_type": "nope", "inputs": [1]})

    assert str(refused.value) == "schema_invalid: component: 'nope' is not one of " + (
        "['indicator', 'combination', 'feature', 'filter', 'labeler', 'trigger', 'exit', "
        "'sizer', 'motion', 'reading', 'combiner', 'calendar', 'context', 'structure', "
        "'statistic', 'model', 'entry_order', 'halt', 'hook']"
    )
    assert [p.where for p in refused.value.problems] == [("/component_type",), ("/inputs/0",)]


def test_an_entry_save_refuses_without_its_checker_and_a_plain_component_saves(
    store: Store,
) -> None:
    with pytest.raises(KindRefused) as refused:
        put(store, "component", "entry", ENTRY)
    put(store, "component", "provides", {"legacy_provides": "k", "app_id": "a"})

    assert str(refused.value) == (
        "checker_unavailable: component: no checker 'qml.entry/1' is registered on this host"
    )
    assert store.head("provides", drafts_ref("provides")) is not None


def test_a_put_check_names_every_problem_its_checker_found(store: Store) -> None:
    store.register_checker("qml.entry/1", fails)

    with pytest.raises(KindRefused) as refused:
        put(store, "component", "entry", ENTRY)

    assert str(refused.value) == "check_failed: component: one is wrong"
    assert refused.value.problems == tuple(TWO)


def test_a_publish_check_runs_on_every_move_of_main(store: Store) -> None:
    store.register_checker("qml.unit/1", fails)
    put(store, "unit", "u", UNIT)
    draft = store.head("u", drafts_ref("u"))
    assert draft is not None

    with pytest.raises(KindRefused) as merged:
        store.merge(OPERATOR, "u", from_ref=drafts_ref("u"), into=MAIN)
    with pytest.raises(KindRefused) as advanced:
        store.advance(OPERATOR, "u", MAIN, draft[0], expected_head=None)
    with pytest.raises(KindRefused) as branched:
        store.branch(OPERATOR, "u", from_ref=drafts_ref("u"), name=MAIN)
    assert [r.value.problems for r in (merged, advanced, branched)] == [tuple(TWO)] * 3
    assert store.head("u", MAIN) is None

    store.register_checker("qml.unit/1", passes)
    assert store.merge(OPERATOR, "u", from_ref=drafts_ref("u"), into=MAIN).outcome == (
        "fast-forward"
    )


def test_a_unit_publish_refuses_on_a_store_with_no_checker(store: Store) -> None:
    put(store, "unit", "u", UNIT)

    with pytest.raises(KindRefused) as refused:
        store.merge(OPERATOR, "u", from_ref=drafts_ref("u"), into=MAIN)

    assert refused.value.code == "checker_unavailable"
    assert store.head("u", MAIN) is None
