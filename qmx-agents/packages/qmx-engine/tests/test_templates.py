"""The template pack: every folder validates, every catalogue row names its card, install is
idempotent, and `meta.needs` keeps a template a draft. Model turns come from a `FakePort` that
answers each chat with the template's recorded answer for the prompt it was sent."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest
from fake_port import TOKENS, FakePort

from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import checked, validate
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import Turn
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.templates.catalog import CATALOG, PACK, SHARED, SHARED_COPIES, find
from qmx_engine.templates.install import install, listing
from qmx_engine.triggers import rows

FOLDERS = sorted(path.parent for path in PACK.rglob("definition.json"))
RS1 = PACK / "rs1-paper-scout"
T3 = PACK / "t3-news-calendar-watch"


def recorded(folder: Path, name: str) -> str:
    return (folder / "fixtures" / "recorded" / name).read_text("utf-8")


def answers(note: str | None = None) -> FakePort:
    """A port that answers every model turn from the recorded files, by the prompt's first words.
    A reader gets the cards of the papers in its own chunk."""
    cards = json.loads(recorded(RS1, "cards.json"))["cards"]
    by_prompt = {
        "You triage new quant-finance papers": recorded(RS1, "triage.json"),
        "You write the research note": note or recorded(RS1, "note.json"),
        "You are the desk's news scanner": recorded(T3, "notes.json"),
    }

    async def answer(port: FakePort, chat: str) -> Turn:
        text = next(sent for to, sent in reversed(port.sent) if to == chat)
        if "You are the paper reader" in text:
            given = text.rsplit("Input:\n", 1)[-1]
            mine = [c for c in cards if c["paper_id"] in given]
            return Turn(json.dumps({"cards": mine}), dict(TOKENS))
        found = next((reply for start, reply in by_prompt.items() if start in text), "{}")
        return Turn(found, dict(TOKENS))

    return FakePort(*[answer] * 40)


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda path: path.name)
def test_every_folder_in_the_pack_validates_for_publish_and_runs(folder: Path) -> None:
    assert validate(load(folder), publish=True) == []
    assert not isinstance(checked(folder), list)


def test_the_catalogue_lists_31_templates_each_with_a_source_card() -> None:
    ids = [t.id for t in CATALOG]

    assert len(ids) == 31
    assert len(set(ids)) == 31
    assert all(t.cards and all(c.file in ("15", "16", "17") and c.card for c in t.cards)
               for t in CATALOG)  # fmt: skip
    assert [t.id for t in CATALOG if not t.needs] == [
        "RS1", "T3", "RS0", "RS2", "RS4", "A", "RV", "DB", "T4",
    ]  # fmt: skip
    assert find("P1").needs == ("trading-node", "risk-session")
    assert [t.folder for t in CATALOG if t.folder] == ["rs1-paper-scout", "t3-news-calendar-watch"]


def test_each_template_carries_an_identical_copy_of_every_block_file_it_uses() -> None:
    for shared, copies in SHARED_COPIES.items():
        for copy in copies:
            assert (PACK / copy).read_bytes() == (SHARED / shared).read_bytes(), copy


def test_install_publishes_both_disabled_and_a_second_install_changes_nothing(
    tmp_path: Path,
) -> None:
    with EngineService.open(tmp_path, harness=answers()) as svc:
        first = asyncio.run(install(svc))
        seen = len(svc.ctx.library.events())
        second = asyncio.run(install(svc))
        status = {row.template.id: (row.status, row.version) for row in listing(svc)}
        library_after = len(svc.ctx.library.events())
    with Reader.open(tmp_path) as reader:
        triggers = rows.triggers(reader.connection)

    assert [(i.template.id, i.action) for i in first] == [("RS1", "published"), ("T3", "published")]
    assert [i.action for i in second] == ["unchanged", "unchanged"]
    assert library_after == seen
    assert status["RS1"] == ("published, disabled", "0.1.0")
    assert status["T3"] == ("published, disabled", "0.1.0")
    assert sum(s == ("not yet built", None) for s in status.values()) == 29
    assert sorted((t.workflow_item, t.kind, t.enabled) for t in triggers) == [
        ("rs1-paper-scout", "cron", False),
        ("t3-news-calendar-watch", "cron", False),
    ]


def test_a_quiet_calendar_day_makes_no_model_call(tmp_path: Path) -> None:
    port = answers()
    with EngineService.open(tmp_path, harness=port) as svc:
        item = svc.drafts.put("t3-news-calendar-watch", Bundle.read(T3), 0, caller=OPERATOR).item
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs={"fixture": "quiet"}))
        with Reader.open(tmp_path) as reader:
            delivered: list[Any] = [
                cast(dict[str, Any], e.data["outputs"])["main"]
                for e in reader.events(report.run_id)
                if e.kind == "node_finished" and e.data.get("node_id") == "deliver"
            ]

    assert report.status == "passed"
    assert port.chats == []
    assert [(d["surprise_count"], d["notes"], d["guard_cross_check"]) for d in delivered] == [
        (0, [], "could not check: trading node")
    ]


def test_a_note_with_a_number_the_papers_never_gave_fails_the_test_run(tmp_path: Path) -> None:
    note = json.loads(recorded(RS1, "note.json"))
    note["papers"][0]["summary"] = "The rule earns a Sharpe ratio of 1.4 after costs."
    with EngineService.open(tmp_path, harness=answers(json.dumps(note))) as svc:
        item = svc.drafts.put("rs1-paper-scout", Bundle.read(RS1), 0, caller=OPERATOR).item
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs={"fixture": True}))
        state = svc.drafts.state(item)

    assert (report.status, state) == ("failed", "validated")


def test_a_template_with_needs_validates_but_its_test_run_is_refused(tmp_path: Path) -> None:
    folder = shutil.copytree(RS1, tmp_path / "rs1-needs")
    definition = json.loads((folder / "definition.json").read_text("utf-8"))
    definition["meta"]["needs"] = ["trading-node"]
    (folder / "definition.json").write_text(json.dumps(definition), "utf-8")
    definition["meta"]["needs"] = ["a-crystal-ball"]
    unknown = Bundle(definition, Bundle.read(folder).files).folder()

    with EngineService.open(tmp_path / "home") as svc:
        item = svc.drafts.put("rs1-needs", Bundle.read(folder), 0, caller=OPERATOR).item
        state = svc.drafts.state(item)
        with pytest.raises(Refused) as refused:
            asyncio.run(svc.tests.run(item, caller=OPERATOR))

    assert state == "validated"
    assert refused.value.code == "needs_unmet"
    assert str(refused.value).endswith("needs: trading-node")
    refused_run = checked(folder)
    assert isinstance(refused_run, list)
    assert [(p.code, p.message) for p in refused_run] == [("needs_unmet", "needs: trading-node")]
    assert [p.code for p in validate(unknown)] == ["schema_invalid"]
