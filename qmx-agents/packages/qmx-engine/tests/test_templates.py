"""The template pack: every folder validates, every catalogue row names its card, install is
idempotent, `meta.needs` keeps a template a draft, and each template's test run delivers what its
card promises. Model turns come from a `FakePort` that answers each chat from the template's
recorded answers, picked by the prompt's first words; a chunked node gets the recorded items whose
ids appear in its own chunk."""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from fake_port import TOKENS, FakePort

from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import checked, validate
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import Turn
from qmx_engine.ports.library import Bundle, drafts_ref
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.templates.catalog import CATALOG, PACK, SHARED, SHARED_COPIES, find
from qmx_engine.templates.install import install, listing
from qmx_engine.triggers import rows

FOLDERS = sorted(path.parent for path in PACK.rglob("definition.json"))
RS1 = PACK / "rs1-paper-scout"
T3 = PACK / "t3-news-calendar-watch"
RS0 = PACK / "rs0-idea-grill"
RS2 = PACK / "rs2-source-to-component-card"
RS4 = PACK / "rs4-literature-review"
A = PACK / "a-fill-the-library"
RV = PACK / "rv-weekly-review"
DB = PACK / "db-desk-brief"
T4 = PACK / "t4-research-desk-overnight"
DRAFTS = [PACK / t.folder for t in CATALOG if t.folder and t.needs]


def recorded(folder: Path, name: str) -> str:
    return (folder / "fixtures" / "recorded" / name).read_text("utf-8")


def mine(folders: list[Path], name: str, key: str, field: str, chunk: str) -> str:
    """The recorded items under `key` whose `field` names something in this chunk's input."""
    found = [item for f in folders for item in json.loads(recorded(f, name))[key]]
    return json.dumps({key: [item for item in found if str(item[field]) in chunk]})


def votes(chunk: str) -> str:
    items = json.loads(chunk)["in"]["items"]
    return json.dumps({"votes": [{"id": item["id"], "answer": "holds"} for item in items]})


def answers(
    note: str | None = None, synthesis: str | None = None, planted: dict[str, str] | None = None
) -> FakePort:
    """A port that answers every model turn from the recorded files, by the prompt's first words.
    `planted` replaces the answer to a prompt that starts with its key."""
    whole = {
        "You triage new quant-finance papers": recorded(RS1, "triage.json"),
        "You write the research note": note or recorded(RS1, "note.json"),
        "You are the desk's news scanner": recorded(T3, "notes.json"),
        "You grill a trading idea": recorded(RS0, "questions.json"),
        "You write the term sheet": recorded(RS0, "term_sheet.json"),
        "You turn one piece of a paper": recorded(RS2, "component.json"),
        "You plan a literature review": recorded(RS4, "plan.json"),
        "You are the synthesiser of a literature review": synthesis
        or recorded(RS4, "synthesis.json"),
        "You judge a literature review": recorded(RS4, "judge.json"),
        "You write the literature review": recorded(RS4, "review.json"),
        "You triage one captured source": recorded(A, "triage.json"),
        "You are the extractor for a quant research library": recorded(A, "cards.json"),
        "You are the auditor": recorded(A, "audit.json"),
        "You are the analyst of QMX's weekly": recorded(RV, "clusters.json"),
        "You propose edits for QMX's": recorded(RV, "edits.json"),
        "You are the writer of the trader's desk brief": recorded(DB, "brief.json"),
        "You are the coordinator of QMX's overnight": recorded(T4, "lines.json"),
    } | (planted or {})
    chunked: dict[str, Callable[[str], str]] = {
        "You are the paper reader": lambda c: mine([RS1], "cards.json", "cards", "paper_id", c),
        "You are the section reader": lambda c: mine(
            [RS2, A], "claims.json", "claims", "source_id", c
        ),
        "You are a searcher on a literature review": lambda c: mine(
            [RS4], "findings.json", "findings", "source_id", c
        ),
        "You check headline claims": votes,
        "You are an analyst on QMX's overnight": lambda c: mine(
            [T4], "claims.json", "claims", "source_id", c
        ),
    }

    async def answer(port: FakePort, chat: str) -> Turn:
        sent = next(sent for to, sent in reversed(port.sent) if to == chat)
        system = port.chats[int(chat.removeprefix("chat-")) - 1]["system"]
        text = f"{system or ''}\n\n{sent}"
        chunk = text.rsplit("Input:\n", 1)[-1]
        for start, reply in chunked.items():
            if start in text:
                return Turn(reply(chunk), dict(TOKENS))
        found = next((reply for start, reply in whole.items() if start in text), "{}")
        return Turn(found, dict(TOKENS))

    return FakePort(*[answer] * 80)


def try_template(home: Path, folder: Path, inputs: Any, port: FakePort | None = None) -> Any:
    """`folder` saved as a draft and test-run with `inputs`: the report and what Deliver gave."""
    with EngineService.open(home, harness=port or answers()) as svc:
        item = svc.drafts.put(folder.name, Bundle.read(folder), 0, caller=OPERATOR).item
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs=inputs))
    with Reader.open(home) as reader:
        delivered = [
            cast(dict[str, Any], e.data["outputs"])["main"]
            for e in reader.events(report.run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "deliver"
        ]
    return report, delivered[0] if delivered else None


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda path: path.name)
def test_every_folder_in_the_pack_validates_for_publish_and_only_its_needs_hold_it_back(
    folder: Path,
) -> None:
    template = next((t for t in CATALOG if t.folder == folder.name), None)
    found = checked(folder)

    assert validate(load(folder), publish=True) == []
    if template is None or not template.needs:
        assert not isinstance(found, list)
    else:
        assert isinstance(found, list)
        assert [(p.code, p.message) for p in found] == [
            ("needs_unmet", f"needs: {', '.join(template.needs)}")
        ]


def test_the_catalogue_lists_31_templates_each_with_a_source_card_and_its_own_folder() -> None:
    ids = [t.id for t in CATALOG]

    assert len(ids) == 31
    assert len(set(ids)) == 31
    assert all(t.cards and all(c.file in ("15", "16", "17") and c.card for c in t.cards)
               for t in CATALOG)  # fmt: skip
    assert [t.id for t in CATALOG if not t.needs] == [
        "RS1", "T3", "RS0", "RS2", "RS4", "A", "RV", "DB", "T4",
    ]  # fmt: skip
    assert find("P1").needs == ("trading-node", "risk-session")
    assert all(t.folder for t in CATALOG)
    assert sorted(str(t.folder) for t in CATALOG) == sorted(
        f.name for f in FOLDERS if f.parent == PACK
    )
    assert sum(1 for t in CATALOG if t.needs) == 22


def test_each_built_folder_names_the_needs_its_catalogue_row_names() -> None:
    for template in CATALOG:
        if template.folder:
            definition = json.loads((PACK / template.folder / "definition.json").read_text())
            assert tuple(definition["meta"].get("needs", [])) == template.needs, template.id
            assert definition["meta"]["template"] == template.id


def test_each_template_carries_an_identical_copy_of_every_block_file_it_uses() -> None:
    for shared, copies in SHARED_COPIES.items():
        for copy in copies:
            assert (PACK / copy).read_bytes() == (SHARED / shared).read_bytes(), copy


def test_rs0_records_every_unanswered_question_as_an_assumption(tmp_path: Path) -> None:
    report, sheet = try_template(tmp_path, RS0, {"fixture": True})

    assert report.status == "passed"
    assert len(sheet["assumptions"]) == 5
    assert sheet["dead_end_warning"].startswith("The Library holds a dead end")


def test_rs2_keeps_the_holes_the_paper_leaves(tmp_path: Path) -> None:
    report, card = try_template(tmp_path, RS2, {"fixture": True})

    assert report.status == "passed"
    assert card["holes"] == ["warm_up", "parameter threshold"]
    assert card["changes"] == ["warm_up rests on no cited claim: unresolved"]
    assert card["warm_up"] == {"value": "unresolved", "claim_id": ""}
    assert [(c["id"], c["basis"], c["confidence"]) for c in card["calibration"]] == [
        ("claimed_effect", "retrieved", "high"),
        ("formula", "retrieved", "high"),
    ]


def test_rs4_splits_its_sources_into_chunks_by_the_setting_and_drops_none(tmp_path: Path) -> None:
    report, review = try_template(tmp_path, RS4, {"fixture": True})
    with Reader.open(tmp_path) as reader:
        chunks = [
            cast(dict[str, Any], e.data["plan"])["chunk"]["items"]
            for e in reader.events(report.run_id)
            if e.kind == "node_scheduled" and e.data.get("node_id") == "search"
        ]

    assert report.status == "passed"
    assert chunks == [[0, 10], [10, 12]]
    assert review["headline"].startswith("2 of 6 methods hold up")
    assert [m["confidence"] for m in review["methods"]][:2] == ["high", "high"]


def test_rs4_fails_when_the_synthesis_invents_a_quote(tmp_path: Path) -> None:
    synthesis = json.loads(recorded(RS4, "synthesis.json"))
    synthesis["claims"][0]["quote"] = "shrinkage doubled the Sharpe ratio of every book"
    port = answers(synthesis=json.dumps(synthesis))
    report, review = try_template(tmp_path, RS4, {"fixture": True}, port)

    assert (report.status, review) == ("failed", None)


def plant(folder: Path, name: str, path: list[str | int], text: str) -> str:
    """The recorded answer with `text` appended to the string at `path`."""
    doc = json.loads(recorded(folder, name))
    node = doc
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] += text
    return json.dumps(doc)


@pytest.mark.parametrize(
    ("folder", "inputs", "prompt", "planted"),
    [
        (RS0, {"fixture": True}, "You write the term sheet",
         plant(RS0, "term_sheet.json", ["capacity_guess"], " About 75 million USD a day.")),
        (RS2, {"fixture": True}, "You turn one piece of a paper",
         plant(RS2, "component.json", ["claimed_effect", "value"], ", and to 1.45 net")),
        (A, {"fixture": "one-video"}, "You are the extractor for a quant research library",
         plant(A, "cards.json", ["cards", 0, "summary"], " Wins 73% of trades.")),
        (DB, {"fixture": "busy"}, "You are the writer of the trader's desk brief",
         plant(DB, "brief.json", ["summary"], " Equity stands at 12,450 USD.")),
        (T4, {"fixture": True}, "You are the coordinator of QMX's overnight",
         plant(T4, "lines.json", ["lines", 0, "text"], " It could reach 1.0975 by noon.")),
    ],
    ids=["rs0-capacity", "rs2-claimed-effect", "a-card-summary", "db-summary", "t4-line"],
)  # fmt: skip
def test_an_output_with_a_number_its_sources_never_gave_fails_the_test_run(
    tmp_path: Path, folder: Path, inputs: Any, prompt: str, planted: str
) -> None:
    report, delivered = try_template(tmp_path, folder, inputs, answers(planted={prompt: planted}))

    assert (report.status, delivered) == ("failed", None)


def produced_files(home: Path, run_id: str) -> list[str]:
    with EngineService.open(home) as svc:
        library = svc.ctx.library
        summary = library.objects(run_id, "workflow-run")[-1]
        made = [
            library.get(edge.from_id)
            for edge in library.edges(summary.object_id, "produced-by", reverse=True)
        ]
    return sorted(
        str(cast(dict[str, Any], m.fields["metadata"])["path"])
        for m in made
        if m.fields["type"] == "run-file"
    )


def test_a_lands_its_cards_as_run_artifacts_produced_by_the_run(tmp_path: Path) -> None:
    report, entry = try_template(tmp_path, A, {"fixture": "one-video"})

    assert report.status == "passed"
    assert [(c["kind"], c["status"], c["exit"], c["audit"]["verdict"]) for c in entry["cards"]] == [
        ("strategy", "entry_hypothesis", "unresolved", "accepted"),
        ("component", "component", "unresolved", "accepted"),
    ]
    assert entry["inventory"][0]["provenance"] == [
        "https://www.youtube.com/watch?v=qmxFixture01&si=share",
        "https://youtu.be/qmxFixture01",
    ]
    assert produced_files(tmp_path, report.run_id) == sorted(
        [f"library/cards/{c['library_id']}.json" for c in entry["cards"]]
        + [f"library/sources/{s['library_id']}.json" for s in entry["sources"]]
        + ["library/inventory.json"]
    )


def test_a_video_with_no_captions_is_recorded_and_the_run_goes_on(tmp_path: Path) -> None:
    port = answers()
    report, entry = try_template(tmp_path, A, {"fixture": "no-captions"}, port)

    assert report.status == "passed"
    assert port.chats == []
    assert [(row["kind"], row["status"]) for row in entry["inventory"]] == [
        ("video", "no captions"),
        ("note", "skipped by the pre-filter: no trading words"),
    ]


def test_rv_names_the_runs_and_parked_items_of_its_own_home(tmp_path: Path) -> None:
    try_template(tmp_path, RS0, {"fixture": True})
    note = json.loads(recorded(RS1, "note.json"))
    plant_number(note)
    parked, _ = try_template(tmp_path, RS1, {"fixture": True}, answers(json.dumps(note)))
    report, card = try_template(tmp_path, RV, None)

    assert report.status == "passed"
    assert [(r["workflow"], r["status"]) for r in card["runs"]] == [
        ("rs0-idea-grill", "passed"),
        ("rs1-paper-scout", "failed"),
    ]
    assert [p["run_id"] for p in card["parked"]] == [parked.run_id]
    assert [e["status"].split(":")[0] for e in card["edits"]] == ["untested", "rejected"]


def test_the_confidence_rule_needs_a_source_and_full_agreement() -> None:
    basis = {
        "items": [
            {"id": "a", "text": "", "basis": "retrieved"},
            {"id": "b", "text": "", "basis": "retrieved"},
            {"id": "c", "text": "", "basis": "inferred"},
            {"id": "d", "text": "", "basis": "remembered"},
        ]
    }
    every = {"votes": [{"id": i, "answer": "holds"} for i in "abcd"]}
    all_but_b = {"votes": [{"id": i, "answer": "holds"} for i in "acd"]}
    done = subprocess.run(
        [sys.executable, "-I", str(SHARED / "calibrate" / "scripts" / "agreement.py")],
        input=json.dumps({"in": [basis, every, every, all_but_b]}),
        capture_output=True,
        text=True,
        check=True,
    )

    assert [(c["id"], c["confidence"]) for c in json.loads(done.stdout)["calibration"]] == [
        ("a", "high"),
        ("b", "medium"),
        ("c", "medium"),
        ("d", "low"),
    ]


def test_a_quiet_calendar_day_makes_no_model_call(tmp_path: Path) -> None:
    port = answers()
    report, strip = try_template(tmp_path, T3, {"fixture": "quiet"}, port)

    assert report.status == "passed"
    assert port.chats == []
    assert (strip["surprise_count"], strip["notes"], strip["guard_cross_check"]) == (
        0,
        [],
        "could not check: trading node",
    )


def plant_number(note: dict[str, Any]) -> None:
    note["papers"][0]["summary"] = "The rule earns a Sharpe ratio of 1.4 after costs."


def plant_quote(note: dict[str, Any]) -> None:
    invented = {"claim": "It never loses.", "quote": "the rule never loses money in any year"}
    note["papers"][0]["citations"].append(invented | {"source_id": "2610.90001"})


@pytest.mark.parametrize("plant", [plant_number, plant_quote], ids=["number", "quote"])
def test_a_note_with_an_invented_number_or_quote_fails_the_test_run(
    tmp_path: Path, plant: Callable[[dict[str, Any]], None]
) -> None:
    note = json.loads(recorded(RS1, "note.json"))
    plant(note)
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


def test_install_publishes_nine_disabled_saves_22_drafts_and_a_second_install_changes_nothing(
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

    built = ["RS1", "T3", "RS0", "RS2", "RS4", "A", "RV", "DB", "T4"]
    drafts = [
        "DM", "T7", "GW", "RK2", "DC", "RK5", "RK8", "P1", "P2", "PP", "B", "RS3", "RS6", "RS8",
        "L1", "L4", "BC", "D3", "D4", "D6", "MA", "D9",
    ]  # fmt: skip
    assert [(i.template.id, i.action) for i in first] == [(t, "published") for t in built] + [
        (t, "saved draft") for t in drafts
    ]
    assert [i.action for i in second] == ["unchanged"] * 31
    assert library_after == seen
    assert [status[t] for t in built] == [("published, disabled", "0.1.0")] * 9
    assert status["GW"] == ("validated draft, needs: trading-node", None)
    assert status["P2"] == ("validated draft, needs: broker-read-token", None)
    assert status["PP"] == ("validated draft, needs: trading-node, risk-session", None)
    assert status["D6"] == ("validated draft, needs: qmb-door, sandbox", None)
    assert status["RS8"] == ("validated draft, needs: rlm", None)
    assert sorted((t.workflow_item, t.kind, t.enabled) for t in triggers) == [
        ("db-desk-brief", "cron", False),
        ("db-desk-brief", "cron", False),
        ("db-desk-brief", "cron", False),
        ("rs1-paper-scout", "cron", False),
        ("rv-weekly-review", "cron", False),
        ("t3-news-calendar-watch", "cron", False),
        ("t4-research-desk-overnight", "cron", False),
    ]


def test_t4_runs_one_analyst_per_chunk_cuts_by_rule_and_cites_every_line(tmp_path: Path) -> None:
    """Fourteen kept claims: their ids sit in the graded prose, so they must carry no digits."""
    report, brief = try_template(tmp_path, T4, {"fixture": True})
    with Reader.open(tmp_path) as reader:
        chunks = [
            cast(dict[str, Any], e.data["plan"])["chunk"]["items"]
            for e in reader.events(report.run_id)
            if e.kind == "node_scheduled" and e.data.get("node_id") == "analyse"
        ]
    lines = [line for section in brief["sections"].values() for line in section]

    assert report.status == "passed"
    assert chunks == [[0, 6], [6, 12], [12, 14]]
    assert sorted(c for line in lines for c in line["claim_ids"]) == [
        f"c{x}" for x in "abcdefghijklmn"
    ]
    assert {k: len(v) for k, v in brief["sections"].items()} == {
        "HIGH": 2, "MEDIUM": 0, "CALENDAR": 1, "POSITIONING": 1, "CROSS-ASSET": 0,
    }  # fmt: skip
    assert all(line["links"] for line in lines)
    assert [(c["source_id"], c["analyst"], c["why"].split(":")[0]) for c in brief["cut"]] == [
        ("n07", "analyst B", "a sentiment reading alone counts only from 5 sd; this is 1.2"),
        ("n08", "analyst B", "single source"),
        ("n12", "analyst B", "single source"),
    ]
    assert [h["instrument"] for h in brief["hint_cards"]] == ["EURUSD", "USDJPY"]


def test_t4_fails_when_the_coordinator_writes_a_line_no_kept_claim_backs(tmp_path: Path) -> None:
    lines = json.loads(recorded(T4, "lines.json"))
    lines["lines"].append(
        {
            "section": "HIGH",
            "text": "USDJPY breaks higher.",
            "claim_ids": ["c99"],
            "label": "inferred",
        }
    )
    port = answers(planted={"You are the coordinator of QMX's overnight": json.dumps(lines)})
    report, brief = try_template(tmp_path, T4, {"fixture": True}, port)

    assert (report.status, brief) == ("failed", None)


def test_db_reads_every_node_fact_as_could_not_check_and_a_quiet_day_costs_nothing(
    tmp_path: Path,
) -> None:
    busy, card = try_template(tmp_path / "busy", DB, {"fixture": "busy"})
    port = answers()
    quiet, still = try_template(tmp_path / "quiet", DB, {"fixture": "quiet"}, port)

    assert busy.status == "passed"
    assert set(card["node_facts"].values()) == {"could not check: trading node"}
    assert [d["run_id"] for d in card["decisions"]] == ["fixture-rs4"]
    assert [e["title"] for e in card["tiles"]["events"]] == [
        "CPI Flash Estimate y/y",
        "Core Retail Sales m/m",
    ]
    assert (quiet.status, still["quiet"], port.chats) == ("passed", True, [])


@pytest.mark.parametrize("folder", DRAFTS, ids=lambda path: path.name)
def test_a_draft_validates_and_its_test_and_its_enable_are_refused_with_its_need(
    tmp_path: Path, folder: Path
) -> None:
    need = f"needs: {', '.join(next(t.needs for t in CATALOG if t.folder == folder.name))}"
    with EngineService.open(tmp_path) as svc:
        item = svc.drafts.put(folder.name, Bundle.read(folder), 0, caller=OPERATOR).item
        state = svc.drafts.state(item)
        with pytest.raises(Refused) as tested:
            asyncio.run(svc.tests.run(item, caller=OPERATOR))
        forced = svc.ctx.library.publish(item, drafts_ref(item), "0.1.0", principal="test")
        with pytest.raises(Refused) as enabled:
            svc.versions.enable(forced, caller=OPERATOR)

    assert state == "validated"
    assert (tested.value.code, str(tested.value).endswith(need)) == ("needs_unmet", True)
    assert (enabled.value.code, str(enabled.value).endswith(need)) == ("needs_unmet", True)


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda path: path.name)
def test_no_template_names_a_money_act_or_holds_a_credential(folder: Path) -> None:
    definition = json.loads((folder / "definition.json").read_text("utf-8"))
    texts = [path.read_text("utf-8") for path in folder.rglob("*") if path.is_file()]

    assert [p for p in validate(load(folder)) if p.code == "money_act"] == []
    assert [n["id"] for n in definition["nodes"] if n.get("credentials")] == []
    assert [t for t in texts if "qmn" in t or "qmx/ctrader" in t or "qmx/broker" in t] == []
