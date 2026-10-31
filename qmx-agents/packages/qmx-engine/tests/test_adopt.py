"""Adoption on another machine (AD-7, ruling 117): the seeded fold, the memo a finished chunk keeps,
the memo a node that committed files loses, and the old home's moved mark.

Every run here is a real `Engine` on a real ledger, and the Hub is one object standing in for the
route `journal_put`/`journal_adopt`, so what the tests exercise is the engine's own seam.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from flows import edge, folder, node
from qmx_home import resolve

from qmx_engine.definition.validate import checked
from qmx_engine.ledger import mirror
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.ledger.mirror import Journal, MirrorRefused
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.runner import Engine, Refused
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.context import Refused as ServiceRefused
from qmx_engine.service.runs import RunView, status_of
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.zones import zones_root

START = node("start", "trigger")
HOLD = node("hold", "wait", seconds=3600)
SAVING = node("save", "script", script="scripts/save.py")
SAVING["outputs"] = {"files": [{"path": "out/saved.txt"}]}
SAVE = """
import json
from pathlib import Path
Path("out").mkdir(exist_ok=True)
Path("out", "saved.txt").write_text("kept")
print(json.dumps("saved"))
"""
PLAIN = "import json\nprint(json.dumps('done'))\n"


class JournalBox:
    """The Hub in one object: the journal it holds, the home it speaks for, and its one claim."""

    def __init__(self, home: str = "pc") -> None:
        self.home = home
        self.journals: dict[str, Journal] = {}
        self.adopted: dict[str, str] = {}
        self.pushes = 0

    def push(self, journal: Journal) -> float:
        self.journals[journal.run_id] = journal
        self.pushes += 1
        return 0.0

    def adoption(self, run_id: str) -> str | None:
        return self.adopted.get(run_id)

    def adopt(self, run_id: str) -> Journal:
        held = self.adopted.get(run_id)
        if held is not None and held != self.home:
            raise MirrorRefused("claim_held", f"{held} already adopts {run_id}")
        found = self.journals.get(run_id)
        if found is None:
            raise MirrorRefused("no_journal", f"no journal for {run_id}")
        self.adopted[run_id] = self.home
        return found


def machine(tmp_path: Path, name: str) -> Path:
    """The home of machine `name`: the `data/` of its own QMX folder, so each keeps its zones."""
    return resolve(tmp_path / name, create=True, drives=[]).home


@contextmanager
def running(home: Path) -> Generator[Engine]:
    home.mkdir(parents=True, exist_ok=True)
    with Ledger.open(home) as ledger, InboxTable.open(home) as inbox:
        yield Engine(
            home,
            ledger,
            settings=DEFAULTS,
            inbox=inbox,
            watch_every=0.01,
        )


def held(tmp_path: Path, middle: dict[str, Any], name: str, text: str) -> tuple[JournalBox, str]:
    """A run cut while one node holds it: the node before it runs, and nothing after it does."""
    root = folder(
        tmp_path / "wf",
        [START, middle, HOLD],
        {
            "start": {"main": [edge(str(middle["id"]))]},
            str(middle["id"]): {"main": [edge("hold")]},
        },
        {name: text},
    )
    found = checked(root)
    assert not isinstance(found, list), found
    box = JournalBox("pc")
    mirror.attach(box)
    try:
        with running(machine(tmp_path, "pc")) as engine:
            outcome = asyncio.run(engine.start(root, found[1], mode="test", inputs=None))
    finally:
        mirror.attach(None)
    assert outcome.status == "waiting", outcome
    return box, outcome.run_id


def adopt(tmp_path: Path, box: JournalBox, run_id: str) -> tuple[RunView, list[Event]]:
    """Adopt the run into a second home, and read the ledger the adoption left."""
    box.home = "contabo"
    target = machine(tmp_path, "contabo")
    mirror.attach(box)
    try:
        with EngineService.open(target, name="contabo") as service:
            view = asyncio.run(service.runs.adopt(run_id, caller=OPERATOR))
    finally:
        mirror.attach(None)
    with Reader.open(target) as reader:
        return view, reader.events(run_id)


def after(events: list[Event], kind: str) -> list[dict[str, Any]]:
    """The events of `kind` written after the adoption's own `run_resumed` line."""
    line = next(
        i
        for i, event in enumerate(events)
        if event.kind == "run_resumed" and event.data.get("reason") == "adopted"
    )
    return [dict(e.data) for e in events[line + 1 :] if e.kind == kind]


def test_a_finished_chunk_keeps_its_memo_across_adoption(tmp_path: Path) -> None:
    box, run_id = held(tmp_path, node("work", "script", script="scripts/work.py"), "work", PLAIN)
    ends = [e for e in box.journals[run_id].events if e.kind == "node_finished"]
    pushed = box.pushes

    view, events = adopt(tmp_path, box, run_id)

    assert (pushed, len(ends)) == (2, 2)
    assert view.status == "waiting"
    assert after(events, "node_started") == []
    assert [line.data.get("reason") for line in events if line.kind == "node_waiting"] == ["wait"]


def test_a_node_that_committed_files_runs_again_after_adoption(tmp_path: Path) -> None:
    box, run_id = held(tmp_path, SAVING, "save", SAVE)

    view, events = adopt(tmp_path, box, run_id)

    assert view.status == "waiting"
    assert [line.get("node_id") for line in after(events, "node_started")] == ["save"]
    assert [line.get("paths") for line in after(events, "zone_committed")] == [["out/saved.txt"]]
    work = zones_root(machine(tmp_path, "contabo")) / run_id / "work"
    assert (work / "out" / "saved.txt").read_text() == "kept"


def test_the_old_home_marks_its_copy_moved_and_never_resumes_it(tmp_path: Path) -> None:
    box, run_id = held(tmp_path, node("work", "script", script="scripts/work.py"), "work", PLAIN)
    adopt(tmp_path, box, run_id)
    box.home = "pc"
    mirror.attach(box)
    try:
        with running(machine(tmp_path, "pc")) as engine:
            with pytest.raises(Refused):
                asyncio.run(engine.resume(run_id))
            with pytest.raises(Refused):
                asyncio.run(engine.resume(run_id))
    finally:
        mirror.attach(None)

    with Reader.open(machine(tmp_path, "pc")) as reader:
        events = reader.events(run_id)

    moved = [e.data for e in events if e.kind == "run_cancelled"]
    state = status_of(events)
    assert moved == [{"reason": "moved", "to": "contabo"}]
    assert (state.status, state.reason) == ("stopped", "moved")


def test_adoption_is_refused_with_no_hub_and_when_another_home_holds_the_claim(
    tmp_path: Path,
) -> None:
    box, run_id = held(tmp_path, node("work", "script", script="scripts/work.py"), "work", PLAIN)
    mirror.attach(None)
    try:
        with (
            EngineService.open(tmp_path / "qmb", name="qmb") as service,
            pytest.raises(ServiceRefused) as nobody,
        ):
            asyncio.run(service.runs.adopt(run_id, caller=OPERATOR))
    finally:
        mirror.attach(None)
    adopt(tmp_path, box, run_id)
    box.home = "qmb"
    mirror.attach(box)
    try:
        with (
            EngineService.open(tmp_path / "qmb", name="qmb") as service,
            pytest.raises(ServiceRefused) as lost,
        ):
            asyncio.run(service.runs.adopt(run_id, caller=OPERATOR))
    finally:
        mirror.attach(None)

    assert nobody.value.code == "no_hub"
    assert lost.value.code == "claim_held"
