"""The mirrored journal (AD-7, ruling 117): what travels, what a seed leaves out, and what the
Hub's answer becomes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
from pydantic import JsonValue

from qmx_engine.ledger.events import Event, EventKind
from qmx_engine.ledger.mirror import (
    HubJournals,
    Journal,
    MirrorRefused,
    committed,
    seedable,
)
from qmx_engine.ports.library import Bundle

AT = "2026-10-22T09:00:00+00:00"
NEW = Path("D:/tmp/adopted")


def event(seq: int, kind: EventKind, **data: JsonValue) -> Event:
    return Event(seq, "run-1", AT, kind, dict(data))


def journal(*events: Event) -> Journal:
    bundle = Bundle({"schema": "qmx.workflow/1", "id": "flow"}, {"scripts/a.py": b"print(1)\n"})
    return Journal("run-1", "pc", AT, bundle, events)


def test_a_journal_round_trips_and_a_binary_ref_travels_unchanged() -> None:
    bundle = Bundle({"schema": "qmx.workflow/1", "id": "flow"}, {"data/x.bin": b"\x00\xff bytes"})
    held = Journal("run-1", "pc", AT, bundle, (event(1, "run_created"),))

    again = Journal.of(json.loads(json.dumps(held.as_json())))

    assert again.bundle.files == {"data/x.bin": b"\x00\xff bytes"}
    assert [(e.seq, e.kind, e.run_id) for e in again.events] == [(1, "run_created", "run-1")]
    assert (again.home, again.at) == ("pc", AT)


def test_a_node_that_committed_files_keeps_one_line_and_reruns() -> None:
    held = journal(
        event(1, "run_created"),
        event(2, "node_finished", node_id="save", iteration=0, partition=None, attempt=1),
        event(3, "zone_committed", node_id="save", iteration=0, partition=None, attempt=1),
        event(4, "node_finished", node_id="hold", iteration=0, partition=None, attempt=1),
    )

    seeded = seedable(held, NEW)

    assert committed(held.events) == frozenset({"save"})
    assert [e.kind for e in seeded] == ["run_created", "zone_committed", "node_finished"]
    assert [e.data.get("node_id") for e in seeded] == [None, "save", "hold"]
    assert seeded[0].data["folder"] == str(NEW)
    assert seeded[0].data["adopted_from"] == "pc"


def test_a_push_records_its_milliseconds_and_the_hubs_refusal_is_the_hubs_word() -> None:
    calls: list[tuple[str, Mapping[str, JsonValue]]] = []

    def post(url: str, body: Mapping[str, JsonValue], _: Mapping[str, str]) -> JsonValue:
        calls.append((url, body))
        return {"ok": True, "value": 2}

    hub = HubJournals("http://hub:1", "not-a-key-value", home="pc", post=post)

    first = hub.push(journal(event(1, "run_created")))
    second = hub.push(journal(event(1, "run_created")))

    assert calls[0][0] == "http://hub:1/v1/op/journal_put"
    assert calls[0][1]["args"]["journal"]["home"] == "pc"  # type: ignore[index]
    assert hub.times == [first, second]
    assert 0.0 < first < 1_000.0


def test_a_refused_push_is_counted_and_raises_its_code() -> None:
    def post(url: str, body: Mapping[str, JsonValue], _: Mapping[str, str]) -> JsonValue:
        return {"ok": False, "code": "journal_moved", "message": "another home owns it"}

    hub = HubJournals("http://hub:1", "not-a-key-value", home="pc", post=post)

    with pytest.raises(MirrorRefused) as refused:
        hub.push(journal(event(1, "run_created")))

    assert refused.value.code == "journal_moved"
    assert (hub.times, hub.failures) == ([], 1)
