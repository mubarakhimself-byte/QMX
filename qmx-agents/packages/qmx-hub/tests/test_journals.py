"""The mirrored journals on the Hub (AD-7, ruling 117): the mirror, the refusal while the run's home
still beats, the one claim two machines contend for, and the journal's only writer after an
adoption."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import JsonValue
from qmx_engine.heartbeat import Heartbeat
from qmx_engine.ledger import redact
from qmx_library.port import LibraryRefused
from qmx_library.store import Store

from qmx_hub.server import Hub

NOW = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)


def row(host: str, at: datetime) -> Heartbeat:
    return Heartbeat(
        subject="host",
        id=host,
        at=at.isoformat(),
        cpu_seconds=0.0,
        rss_bytes=0,
        machine_minutes=0.0,
        qmx_version="0.1.0",
        kinds_digest="d",
        paused=False,
    )


def journal() -> dict[str, JsonValue]:
    line: dict[str, JsonValue] = {
        "seq": 1,
        "at": NOW.isoformat(),
        "kind": "run_created",
        "data": {},
    }
    return {"run_id": "run-1", "home": "pc", "events": [line]}


@pytest.fixture
def hub(tmp_path: Path) -> Iterator[Hub]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as store:
        yield Hub(store, home=tmp_path / "hub")


def test_the_mirror_is_refused_while_the_home_still_beats_and_granted_after(hub: Hub) -> None:
    hub.put_journal(journal(), at=NOW.isoformat())
    hub.hear(row("pc", NOW).model_dump(mode="json"))

    with pytest.raises(LibraryRefused) as fresh:
        hub.adopt("run-1", "contabo", 900, at=NOW)

    hub.hear(row("pc", NOW - timedelta(minutes=10)).model_dump(mode="json"))
    granted = hub.adopt("run-1", "contabo", 900, at=NOW)

    assert fresh.value.code == "home_fresh"
    assert (granted["from"], granted["to"]) == ("pc", "contabo")
    assert hub.adoption_of("run-1") == {
        "run_id": "run-1",
        "from": "pc",
        "to": "contabo",
        "at": NOW.isoformat(),
    }


def test_two_machines_adopting_at_once_leave_exactly_one_winner(hub: Hub) -> None:
    hub.put_journal(journal(), at=NOW.isoformat())

    first = hub.adopt("run-1", "contabo", 900, at=NOW)
    with pytest.raises(LibraryRefused) as lost:
        hub.adopt("run-1", "qmb", 900, at=NOW)

    assert (first["to"], lost.value.code) == ("contabo", "claim_held")


def test_the_home_that_adopted_the_run_is_the_journals_only_writer(hub: Hub) -> None:
    hub.put_journal(journal(), at=NOW.isoformat())
    hub.adopt("run-1", "contabo", 900, at=NOW)

    with pytest.raises(LibraryRefused) as moved:
        hub.put_journal(journal(), at=NOW.isoformat())

    adopted = journal() | {"home": "contabo"}
    assert moved.value.code == "journal_moved"
    assert hub.put_journal(adopted, at=NOW.isoformat()) == 1
    assert (hub.journal("run-1") or {}).get("home") == "contabo"
