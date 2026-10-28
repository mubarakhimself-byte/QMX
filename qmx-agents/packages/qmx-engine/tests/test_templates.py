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
from fake_library import fake_service
from fake_port import TOKENS, FakePort
from qmx_home import resolve
from qmx_library.store import Store

from qmx_engine.__main__ import main
from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import checked, validate
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import Turn
from qmx_engine.ports.library import Bundle, drafts_ref
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.templates.catalog import ALIASES, CATALOG, PACK, SHARED, find
from qmx_engine.templates.install import install, listing
from qmx_engine.triggers import rows
from qmx_engine.workers.zones import RunZone

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
EV = PACK / "ev-copilot-eval-battery"
REVOLUTION = PACK / "revolution-loop"
PANEL = PACK / "ask-the-panel"
CLIPPINGS = PACK / "clippings-into-research"
DIGEST = PACK / "morning-digest"
CRYSTALLISE = PACK / "crystallise-a-workflow"
DRAFTS = [PACK / t.folder for t in CATALOG if t.needs]
CALIBRATED = ("rs2-source-to-component-card", "rs4-literature-review", "a-fill-the-library")

NO_RENDER = frozenset(
    {
        "a-fill-the-library",
        "connections-health",
        "download-binance",
        "download-ccxt",
        "download-dukascopy",
        "extract-source",
        "feed",
    }
)
"""Script-first templates with no grader and no deliver step, so they carry no block copy.

`connections-health` was the first; the feed and the three downloaders
land their own output and have nothing to render or grade (DR6); `extract-source` hands the
extraction back to its caller and lands no Library object of its own (DR7).
"""

BLOCK_COPIES = {
    "preflight/scripts/new_ids.py": ("rs1-paper-scout/scripts/new_ids.py",),
    "paper-read/prompts/read.md": ("rs1-paper-scout/prompts/read.md",),
    "paper-read/schemas/cards.json": ("rs1-paper-scout/schemas/cards.json",),
    "research-harness/scripts/citation_check.py": (
        "rs1-paper-scout/scripts/citation_check.py",
        "rs4-literature-review/scripts/citation_check.py",
        "_shared/understand-extract/scripts/citation_check.py",
        "rs2-source-to-component-card/scripts/citation_check.py",
        "a-fill-the-library/scripts/citation_check.py",
        "t4-research-desk-overnight/scripts/citation_check.py",
        "rk8-incident-post-mortem/scripts/citation_check.py",
        "rs3-source-to-lab-test/scripts/citation_check.py",
    ),
    "render-and-grade/scripts/render_and_grade.py": tuple(
        f"{template.folder}/scripts/render_and_grade.py"
        for template in CATALOG
        if template.folder not in NO_RENDER
    ),
    "render-and-grade/scripts/stop.py": tuple(
        f"{template.folder}/scripts/stop.py"
        for template in CATALOG
        if template.folder not in NO_RENDER
    ),
    "render-and-grade/scripts/deliver.py": tuple(
        f"{template.folder}/scripts/deliver.py"
        for template in CATALOG
        if template.folder not in NO_RENDER
    ),
    "overfit-gates/scripts/deflated_sharpe.py": tuple(
        f"{folder}/scripts/deflated_sharpe.py"
        for folder in (
            "b-build-and-prove",
            "l4-overnight-lab-loop",
            "d3-iterate-against-qmb",
            "d4-variant-comparison",
        )
    ),
    "understand-extract/scripts/sections.py": (
        "rs2-source-to-component-card/scripts/sections.py",
        "a-fill-the-library/scripts/sections.py",
    ),
    "understand-extract/prompts/sections.md": (
        "rs2-source-to-component-card/prompts/sections.md",
        "a-fill-the-library/prompts/sections.md",
    ),
    "understand-extract/schemas/claims.json": (
        "rs2-source-to-component-card/schemas/claims.json",
        "a-fill-the-library/schemas/claims.json",
    ),
    "understand-extract/scripts/card_holes.py": ("a-fill-the-library/scripts/card_holes.py",),
    "understand-extract/prompts/extract.md": ("a-fill-the-library/prompts/extract.md",),
    "understand-extract/schemas/cards.json": ("a-fill-the-library/schemas/cards.json",),
    **{
        f"calibrate/{name}": tuple(f"{folder}/{name}" for folder in CALIBRATED)
        for name in (
            "scripts/basis.py",
            "scripts/agreement.py",
            "prompts/sample.md",
            "schemas/votes.json",
        )
    },
}
"""Each shared block file, under `_shared/`, to the copies the templates carry. `catalog` held this
list until TPL1; it lives here now because this test is its only reader, and a bundle carries a
`subworkflow` node's child folder and hashes its bytes (B-76), so a template may call a block as a
child instead and the copies can go."""


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
        "You are the copilot under evaluation": recorded(EV, "answers.json"),
        "You grade answers in QMX's copilot eval battery": recorded(EV, "verdicts.json"),
        "You draft one testable candidate": recorded(REVOLUTION / "revolution", "candidate.json"),
        "You are one member of the panel, answering from the macro backdrop": recorded(
            PANEL, "macro.json"
        ),
        "You are one member of the panel, answering from positioning": recorded(
            PANEL, "positioning.json"
        ),
        "You are one member of the panel, answering from sentiment": recorded(
            PANEL, "sentiment.json"
        ),
        "You judge the panel": recorded(PANEL, "judge.json"),
        "Summarise every new clipping into a research note line": recorded(CLIPPINGS, "notes.json"),
        "Write the morning digest from what ran": recorded(DIGEST, "digest.json"),
        "Label the sampled items the way you would label": recorded(CRYSTALLISE, "sample.json"),
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


def qmx_folder(at: Path) -> Path:
    """A QMX folder made at `at` the way `--create` makes one, and its home `data/`."""
    return resolve(at, create=True, drives=[]).home


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return qmx_folder(tmp_path / "QMX")


def try_template(home: Path, folder: Path, inputs: Any, port: FakePort | None = None) -> Any:
    """`folder` saved as a draft and test-run with `inputs`: the report and what Deliver gave."""
    with fake_service(home, harness=port or answers()) as svc:
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
    slot = [("place_unset", "name the place this node runs on")]

    assert validate(load(folder), publish=True) == []
    if template is None or not template.needs:
        assert not isinstance(found, list)
    else:
        assert isinstance(found, list)
        assert [(p.code, p.message) for p in found] == [
            *(slot if folder.name == "run-on-a-machine" else []),
            ("needs_unmet", f"needs: {', '.join(template.needs)}"),
        ]


def test_the_catalogue_lists_45_templates_each_with_a_source_card_and_its_own_folder() -> None:
    ids = [t.id for t in CATALOG]

    assert len(ids) == 45
    assert len(set(ids)) == 45
    assert all(t.cards and all(c.file in ("15", "16", "17", "44", "46") and c.card for c in t.cards)
               for t in CATALOG)  # fmt: skip
    assert [t.id for t in CATALOG if not t.needs] == [
        "paper-scout-to-research-note",
        "news-and-macro-calendar-watch",
        "rough-idea-to-test-plan",
        "source-to-component-card",
        "literature-review-on-a-topic",
        "video-to-strategy-ideas",
        "weekly-review",
        "morning-market-brief",
        "research-desk-overnight",
        "copilot-eval-battery",
        "revolution-loop",
        "ask-the-panel",
        "clippings-into-research",
        "morning-digest",
        "crystallise-a-workflow",
        "synthetic-data",
        "connections-health",
        "feed",
        "download-dukascopy",
        "download-binance",
        "download-ccxt",
        "extract-source",
    ]
    assert find("portfolio-combination-study").needs == ("trading-node", "risk-session")
    assert sorted(str(t.folder) for t in CATALOG) == sorted(
        f.name for f in FOLDERS if f.parent == PACK
    )
    assert sum(1 for t in CATALOG if t.needs) == 23


def test_every_id_is_a_plain_phrase_and_every_title_says_what_the_template_does() -> None:
    for template in CATALOG:
        assert template.id == template.id.casefold()
        assert all(word.isalnum() for word in template.id.split("-")), template.id
        assert not template.id.startswith(("rs", "rk", "tp", "db", "dm", "dc", "gw", "bc")), (
            template.id
        )
        assert template.name[0].isupper() and not template.name.endswith("."), template.name
    assert [t.name for t in CATALOG if t.id == "video-to-strategy-ideas"] == [
        "Turn a video, a playlist or saved posts into strategy ideas"
    ]


def test_every_id_the_pack_used_before_tpl1_still_finds_its_template() -> None:
    assert find("RS1") is find("paper-scout-to-research-note")
    assert find("rs1") is find("paper-scout-to-research-note")
    assert find("rs1-paper-scout") is find("paper-scout-to-research-note")
    assert find(" A ") is find("video-to-strategy-ideas")
    assert find("b-build-and-prove").id == "strategy-idea-to-paper-tested"
    assert set(ALIASES.values()) <= {template.id for template in CATALOG}
    assert {template.id for template in CATALOG} - set(ALIASES.values()) == {
        "revolution-loop",
        "ask-the-panel",
        "clippings-into-research",
        "morning-digest",
        "crystallise-a-workflow",
        "run-one-job-on-his-server",
        "synthetic-data",
        "connections-health",
        "feed",
        "download-dukascopy",
        "download-binance",
        "download-ccxt",
        "extract-source",
    }
    for old, new in ALIASES.items():
        assert find(old).id == new, old
    with pytest.raises(KeyError):
        find("no-such-template")


def test_each_built_folder_names_the_needs_its_catalogue_row_names() -> None:
    for template in CATALOG:
        if template.folder:
            definition = json.loads((PACK / template.folder / "definition.json").read_text())
            assert tuple(definition["meta"].get("needs", [])) == template.needs, template.id
            assert definition["meta"]["template"] == template.id


def test_each_template_carries_an_identical_copy_of_every_block_file_it_uses() -> None:
    for shared, copies in BLOCK_COPIES.items():
        for copy in copies:
            assert (PACK / copy).read_bytes() == (SHARED / shared).read_bytes(), copy


def test_rs0_records_every_unanswered_question_as_an_assumption(home: Path) -> None:
    report, sheet = try_template(home, RS0, {"fixture": True})

    assert report.status == "passed"
    assert len(sheet["assumptions"]) == 5
    assert sheet["dead_end_warning"].startswith("The Library holds a dead end")


def test_rs2_keeps_the_holes_the_paper_leaves(home: Path) -> None:
    report, card = try_template(home, RS2, {"fixture": True})

    assert report.status == "passed"
    assert card["holes"] == ["warm_up", "parameter threshold"]
    assert card["changes"] == ["warm_up rests on no cited claim: unresolved"]
    assert card["warm_up"] == {"value": "unresolved", "claim_id": ""}
    assert [(c["id"], c["basis"], c["confidence"]) for c in card["calibration"]] == [
        ("claimed_effect", "retrieved", "high"),
        ("formula", "retrieved", "high"),
    ]


def test_rs4_splits_its_sources_into_chunks_by_the_setting_and_drops_none(home: Path) -> None:
    report, review = try_template(home, RS4, {"fixture": True})
    with Reader.open(home) as reader:
        chunks = [
            cast(dict[str, Any], e.data["plan"])["chunk"]["items"]
            for e in reader.events(report.run_id)
            if e.kind == "node_scheduled" and e.data.get("node_id") == "search"
        ]

    assert report.status == "passed"
    assert chunks == [[0, 10], [10, 12]]
    assert review["headline"].startswith("2 of 6 methods hold up")
    assert [m["confidence"] for m in review["methods"]][:2] == ["high", "high"]


def test_rs4_fails_when_the_synthesis_invents_a_quote(home: Path) -> None:
    synthesis = json.loads(recorded(RS4, "synthesis.json"))
    synthesis["claims"][0]["quote"] = "shrinkage doubled the Sharpe ratio of every book"
    port = answers(synthesis=json.dumps(synthesis))
    report, review = try_template(home, RS4, {"fixture": True}, port)

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
    home: Path, folder: Path, inputs: Any, prompt: str, planted: str
) -> None:
    report, delivered = try_template(home, folder, inputs, answers(planted={prompt: planted}))

    assert (report.status, delivered) == ("failed", None)


def produced_files(home: Path, run_id: str) -> list[str]:
    with fake_service(home) as svc:
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


def test_a_lands_its_cards_as_run_artifacts_produced_by_the_run(home: Path) -> None:
    report, entry = try_template(home, A, {"fixture": "one-video"})

    assert report.status == "passed"
    assert [(c["kind"], c["status"], c["exit"], c["audit"]["verdict"]) for c in entry["cards"]] == [
        ("strategy", "entry_hypothesis", "unresolved", "accepted"),
        ("component", "component", "unresolved", "accepted"),
    ]
    assert entry["inventory"][0]["provenance"] == [
        "https://www.youtube.com/watch?v=qmxFixture01&si=share",
        "https://youtu.be/qmxFixture01",
    ]
    assert produced_files(home, report.run_id) == sorted(
        [f"library/cards/{c['library_id']}.json" for c in entry["cards"]]
        + [f"library/sources/{s['library_id']}.json" for s in entry["sources"]]
        + [
            "library/inventory.json",
            "library/sources/68591196f5a58e9a65dd7d30f9efe689.json",
            "library/sources/index.json",
        ]
    )


def test_a_video_with_no_captions_is_recorded_and_the_run_goes_on(home: Path) -> None:
    port = answers()
    report, entry = try_template(home, A, {"fixture": "no-captions"}, port)

    assert report.status == "passed"
    assert port.chats == []
    assert [(row["kind"], row["status"]) for row in entry["inventory"]] == [
        ("video", "no captions"),
        ("note", "skipped by the pre-filter: no trading words"),
    ]


def test_rv_names_the_runs_and_parked_items_of_its_own_home(home: Path) -> None:
    try_template(home, RS0, {"fixture": True})
    note = json.loads(recorded(RS1, "note.json"))
    plant_number(note)
    parked, _ = try_template(home, RS1, {"fixture": True}, answers(json.dumps(note)))
    report, card = try_template(home, RV, None)

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


def test_a_quiet_calendar_day_makes_no_model_call(home: Path) -> None:
    port = answers()
    report, strip = try_template(home, T3, {"fixture": "quiet"}, port)

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
    home: Path, plant: Callable[[dict[str, Any]], None]
) -> None:
    note = json.loads(recorded(RS1, "note.json"))
    plant(note)
    with fake_service(home, harness=answers(json.dumps(note))) as svc:
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

    with fake_service(tmp_path / "home") as svc:
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


def test_install_publishes_22_disabled_saves_23_drafts_and_a_second_install_changes_nothing(
    home: Path,
) -> None:
    with fake_service(home, harness=answers()) as svc:
        first = asyncio.run(install(svc))
        seen = len(svc.ctx.library.events())
        second = asyncio.run(install(svc))
        status = {row.template.id: (row.status, row.version) for row in listing(svc)}
        library_after = len(svc.ctx.library.events())
    with Reader.open(home) as reader:
        triggers = rows.triggers(reader.connection)

    built = [template.id for template in CATALOG if not template.needs]
    assert [(i.template.id, i.action) for i in first] == [
        (template.id, "saved draft" if template.needs else "published") for template in CATALOG
    ]
    assert [i.action for i in second] == ["unchanged"] * 45
    assert library_after == seen
    assert [status[t] for t in built] == [("published, disabled", "0.1.0")] * 22
    assert status["trading-guards-alive"] == ("validated draft, needs: trading-node", None)
    assert status["daily-book-report"] == ("validated draft, needs: broker-read-token", None)
    assert status["change-bundle-for-approval"] == (
        "validated draft, needs: trading-node, risk-session",
        None,
    )
    assert status["ml-training-run-with-a-holdout"] == (
        "validated draft, needs: qmb-door, sandbox",
        None,
    )
    assert status["question-over-a-large-table"] == ("validated draft, needs: rlm", None)
    assert sorted((t.workflow_item, t.kind, t.enabled) for t in triggers) == [
        ("connections-health", "cron", False),
        ("db-desk-brief", "cron", False),
        ("db-desk-brief", "cron", False),
        ("db-desk-brief", "cron", False),
        ("download-binance", "cron", False),
        ("download-ccxt", "cron", False),
        ("download-dukascopy", "cron", False),
        ("morning-digest", "cron", False),
        ("rs1-paper-scout", "cron", False),
        ("rv-weekly-review", "cron", False),
        ("t3-news-calendar-watch", "cron", False),
        ("t4-research-desk-overnight", "cron", False),
    ]


def test_installing_by_an_old_id_installs_the_renamed_template(home: Path) -> None:
    with fake_service(home, harness=answers()) as svc:
        done = asyncio.run(install(svc, [find("B")]))
        found = listing(svc, [find("b-build-and-prove")])
        drafted = svc.drafts.get("b-build-and-prove")

    assert [(i.template.id, i.template.name, i.action) for i in done] == [
        (
            "strategy-idea-to-paper-tested",
            "Turn a strategy idea into a tested strategy, ending on paper",
            "saved draft",
        )
    ]
    assert [row.status for row in found] == ["validated draft, needs: qmb-door"]
    assert drafted.item == "b-build-and-prove"


def test_t4_runs_one_analyst_per_chunk_cuts_by_rule_and_cites_every_line(home: Path) -> None:
    """Fourteen kept claims: their ids sit in the graded prose, so they must carry no digits."""
    report, brief = try_template(home, T4, {"fixture": True})
    with Reader.open(home) as reader:
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


def test_t4_fails_when_the_coordinator_writes_a_line_no_kept_claim_backs(home: Path) -> None:
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
    report, brief = try_template(home, T4, {"fixture": True}, port)

    assert (report.status, brief) == ("failed", None)


def test_db_reads_every_node_fact_as_could_not_check_and_a_quiet_day_costs_nothing(
    tmp_path: Path,
) -> None:
    busy, card = try_template(qmx_folder(tmp_path / "busy"), DB, {"fixture": "busy"})
    port = answers()
    quiet, still = try_template(qmx_folder(tmp_path / "quiet"), DB, {"fixture": "quiet"}, port)

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
    home: Path, folder: Path
) -> None:
    need = f"needs: {', '.join(next(t.needs for t in CATALOG if t.folder == folder.name))}"
    with fake_service(home) as svc:
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
def test_no_template_holds_a_credential_or_a_broker_ref(folder: Path) -> None:
    definition = json.loads((folder / "definition.json").read_text("utf-8"))
    texts = [
        path.read_text("utf-8")
        for path in folder.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]

    assert [n["id"] for n in definition["nodes"] if n.get("credentials")] == []
    assert [t for t in texts if "qmn" in t or "qmx/ctrader" in t or "qmx/broker" in t] == []


def test_revolution_loop_runs_a_child_that_holds_its_own_loop_and_keeps_the_negatives(
    home: Path,
) -> None:
    candidate = json.loads(recorded(REVOLUTION / "revolution", "candidate.json"))
    candidate["evidence"] = "a source nobody gave it"
    port = answers(planted={"You draft one testable candidate": json.dumps(candidate)})
    report, card = try_template(home, REVOLUTION, {"fixture": "plateau"}, port)
    with Reader.open(home) as reader:
        runs = {row[0] for row in reader.connection.execute("SELECT DISTINCT run_id FROM events")}

    assert report.status == "passed"
    assert (card["plateau"], card["kept"], card["figures"]["kept"]) == (True, None, 0)
    assert (card["figures"]["revolutions"], card["figures"]["attempts"]) == (1, 3)
    assert card["figures"]["negatives"] == 3
    assert len(runs) == 2
    assert all(negative["problem"] == "the evidence names no source this run was given"
               for negative in card["negatives"])  # fmt: skip


def test_the_panel_marks_an_absent_seat_and_labels_a_judge_of_the_same_family(
    tmp_path: Path,
) -> None:
    folder = shutil.copytree(PANEL, tmp_path / "panel-two")
    definition = json.loads((folder / "definition.json").read_text("utf-8"))
    definition["nodes"] = [n for n in definition["nodes"] if n["id"] != "member_sentiment"]
    connections = definition["connections"]
    connections.pop("Sentiment member")
    connections["Seat the panel"]["main"][0] = [
        edge
        for edge in connections["Seat the panel"]["main"][0]
        if edge["node"] != "Sentiment member"
    ]
    (folder / "definition.json").write_text(json.dumps(definition), "utf-8")
    report, card = try_template(qmx_folder(tmp_path / "QMX"), folder, {"fixture": "recorded"})

    assert report.status == "passed"
    assert card["absent"] == ["sentiment"]
    assert [(m["slot"], m["present"], m["stance"]) for m in card["members"]] == [
        ("macro", True, "bullish"),
        ("positioning", True, "bearish"),
        ("sentiment", False, None),
    ]
    assert [line["slot"] for line in card["disagreement"]] == ["positioning"]
    assert card["judge_same_family_as"] == ["macro", "positioning"]


def test_crystallise_refuses_the_script_when_one_replay_disagrees(tmp_path: Path) -> None:
    folder = shutil.copytree(CRYSTALLISE, tmp_path / "crystallise-one-wrong")
    replays = json.loads((folder / "fixtures" / "replays.json").read_text("utf-8"))
    replays[17]["title"] = "pod"
    (folder / "fixtures" / "replays.json").write_text(json.dumps(replays), "utf-8")
    report, card = try_template(qmx_folder(tmp_path / "QMX"), folder, {"fixture": True})

    assert report.status == "passed"
    assert (card["crystallised"], card["equivalent"], card["sampling"]) == (False, False, None)
    assert [(wrong["item_id"], wrong["agent"], wrong["script"]) for wrong in card["wrong"]] == [
        ("r-18", "other", None)
    ]
    assert card["figures"]["agreeing"] == 19


def test_a_feed_run_lands_its_new_item_as_one_source_through_save_source(home: Path) -> None:
    feed = find("feed")
    report, _ = try_template(home, PACK / feed.folder, feed.test_inputs)
    name = "library/sources/4bce335b378af3d330222548e5b5a379.json"
    saved = json.loads((RunZone.of(home, report.run_id).work / name).read_text("utf-8"))

    assert report.status == "passed"
    assert produced_files(home, report.run_id) == [name, "library/sources/index.json"]
    assert {key: saved[key] for key in ("kind", "origin", "intent_key", "part_of", "licence")} == {
        "kind": "source",
        "origin": "feed",
        "intent_key": "feed://3e4d98d0cbe776cb",
        "part_of": "example",
        "licence": "",
    }


def test_the_cli_installs_one_template_into_the_homes_real_store(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    home = qmx_folder(tmp_path / "QMX")
    folder = str(home.parent)
    unknown = main(["templates", "install", "--home", folder, "--template", "no-such-template"])
    refused = capsys.readouterr().out
    installed = main(["templates", "install", "--home", folder, "--template", "connections-health"])
    with Store.open(home / "library", redactor=redact) as store:
        on_main = sorted(item for item, _ in store.heads_on("main"))

    assert (unknown, refused) == (1, "refused: no template 'no-such-template' in the catalogue\n")
    assert installed == 0
    assert "connections-health published: 0.1.0" in capsys.readouterr().out
    assert on_main == ["connections-health"]
    assert not (home / "engine" / "library-fake.sqlite").exists()
