"""The template lanes: each template test-run on real models, and the pack installed twice.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/t_templates.py [--pr PR] [--shared SLUG] [LANE ...]`
None named runs TP1's three lanes, in order. Each lane writes
`evidence/<pr>/<ENGINE_LOG_PREFIX><pr>-<lane>.log`, where `pr` is `--pr` or the PR that built the
lane's template, and the script exits 1 if any lane failed. Each lane gets its own throwaway home
whose only provider row is OpenRouter's; with `--shared SLUG` every lane named runs on one fresh
home, so `rv` reads the other lanes' runs and `install` publishes the drafts they already tested.
No lane touches the plan login or the ship home.

- `rs1` (TP1 lane 2): RS1 on its fixture papers. Pass when the run passes, the test report binds
  to the draft's content hash, and the note validates against `schemas/output.json`.
- `t3` (TP1 lane 3): T3's quiet day makes no model call; its surprise day writes one note.
- `install` (TP1 lane 4, TP2 lane 4): `templates install` twice. Pass when the first run publishes
  every built template at 0.1.0 with its card's triggers disabled and lists the rest as not yet
  built, and the second run changes nothing.
- `rs4` (TP2 lane 2): two or more searcher chunks, the synthesiser and the citation check run, and
  the review validates.
- `a` (TP2 lane 3): one synthetic video transcript. Pass when the cards land as run files in the
  Library, each linked `produced-by` to the run's summary.
- `rs0` (TP2 lane 5): the term sheet validates and lists its assumptions.
- `rs2` (TP2 lane 6): the component card validates with its holes kept.
- `rv` (TP2 lane 7): after a planted run that parks, the review names every run of the week in its
  home and the parked one.
- `a-no-captions` (TP2 lane 10): a video with no captions is recorded and the run goes on.
- `db` (TP3 lane 2): DB's busy day on real models. Pass when the brief validates and every node
  fact reads `could not check`.
- `t4` (TP3 lane 3): T4's synthetic night on real models. Pass when two or more analyst chunks run,
  the run passes, and every line of the brief links to a source.
- `drafts` (TP3 lane 4, no model): each of the 10 drafts saved, then its test run and its enable
  tried. Pass when all 20 calls are refused with the draft's own need. Publish refuses an untested
  draft, so the enable is tried on a version published straight through the Library.
- `money` (TP3 lane 6, no model): the money lint over every TP3 folder, with a planted money act as
  the control. Pass when every folder is clean and the control is caught.
- `readmes` (TP3 lane 8, no model): each draft's README names its need in one line.
- `gw` (TP3 lane 9, no model): GW validates and holds no model-bearing node.
- `t4-fake` (TP3 lane 10) and `db-fake`: the template on the fake switch with no harness at all, so
  no provider can be called. Pass when the run passes with only fake spans.
- `all` (TP4 lane 2, lane 8 and the perf block): the 9 runnable templates test-run on real models
  with their catalogue inputs. Pass when 9 of 9 pass; logs each wall time, the pack's total, and
  the pack's model spans and tokens. `all-recorded` runs the same on the recorded answers.
- `install-recorded` (TP4 lane 3 on recorded answers, no spend): the pack installed, read back
  through the engine host's workflow doors, and `templates list` grabbed as `tp4-install.png`.
  Pass when 9 read published and disabled and 22 read drafts with their need. `install` is the
  real-model lane.
- `drafts-tp4` (TP4 lane 4) and `readmes-tp4`: TP4's 12 drafts, as `drafts` and `readmes`.
- `doc` (TP4 lane 6, no model): every row of `docs/TEMPLATES.md` matches the catalogue.
- `variant` (TP4 lane 7): RS1 cloned through `extends` and test-run; the published variant records
  `variant-of` RS1's version. `variant-recorded` runs it on the recorded answers.
- `money-pack` (TP4 lane 9, no model): the money lint over all 31 folders.

Spend is the relay journals' upper bound at the Kimi row's list prices.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from functools import partial
from pathlib import Path
from typing import Any, Final

from common import ENGINE_STORE, Log, boot, throwaway_home
from ep2_lanes import ENGINE

os.environ.setdefault("QMA_LIVE_SCRATCH", str(ENGINE_STORE / "homes" / "tp1-scratch"))

from jsonschema import Draft202012Validator
from llm_lanes import OPENROUTER_ROW, harnessed, relay_usd
from qmx_engine.__main__ import install_templates, list_templates
from qmx_engine.definition.folder import load
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.definition.validate import validate
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import Bundle, drafts_ref
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.templates.catalog import CATALOG, PACK, find
from qmx_engine.templates.install import current_draft
from qmx_engine.templates.install import install as install_pack
from qmx_engine.triggers import rows

RS1: Final = PACK / "rs1-paper-scout"
T3: Final = PACK / "t3-news-calendar-watch"
RS0: Final = PACK / "rs0-idea-grill"
RS2: Final = PACK / "rs2-source-to-component-card"
RS4: Final = PACK / "rs4-literature-review"
A: Final = PACK / "a-fill-the-library"
RV: Final = PACK / "rv-weekly-review"
DB: Final = PACK / "db-desk-brief"
T4: Final = PACK / "t4-research-desk-overnight"
TP3_FOLDERS: Final = [PACK / t.folder for t in CATALOG if t.pr == "TP3" and t.folder]
PACK_FOLDERS: Final = [PACK / str(t.folder) for t in CATALOG]
NODE_FACT: Final = "could not check: trading node"


def openrouter_home(pr: str, slug: str) -> Path:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home(pr, slug)
    control_service(QmxHome(root)).settings_put("providers", {"openrouter": OPENROUTER_ROW})
    return root


def model_calls(home: Path) -> int:
    return sum(
        json.loads(line).get("event") == "model_call"
        for path in (home / "runs").glob("*/journal.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def delivered(home: Path, run_id: str) -> Any:
    with Reader.open(home) as reader:
        found = [
            e.data["outputs"]["main"]
            for e in reader.events(run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "deliver"
        ]
    return found[0] if found else None


def node_events(home: Path, run_id: str, kind: str, node_id: str) -> list[Any]:
    with Reader.open(home) as reader:
        return [
            e.data
            for e in reader.events(run_id)
            if e.kind == kind and e.data.get("node_id") == node_id
        ]


def model_spans(home: Path, run_id: str) -> list[Span]:
    with Reader.open(home) as reader:
        return [s for s in reader.spans(run_id) if s.profile is not None]


def log_spans(log: Log, spans: list[Span]) -> None:
    for span in spans:
        log(
            f"span {span.node_id} partition {span.partition} attempt {span.attempt} {span.status}: "
            f"{span.role} on {span.profile}/{span.model} tokens {span.tokens}"
        )


def schema_errors(folder: Path, value: Any) -> list[str]:
    schema = json.loads((folder / "schemas" / "output.json").read_text("utf-8"))
    if value is None:
        return ["nothing was delivered"]
    return [e.message for e in Draft202012Validator(schema).iter_errors(value)][:3]


async def test_run(
    home: Path, folder: Path, inputs: Any, *, item: str | None = None, fake: bool = False
) -> tuple[Any, float, str]:
    """A draft saved from `folder` as `item`, test-run with `inputs`; the report, its seconds,
    and the draft's state after."""
    async with harnessed(home) as opened:
        with EngineService.open(
            home, settings=ControlSettings(opened.control), harness=HarnessAdapter(opened.harness)
        ) as svc:
            item = item or folder.name
            current = current_draft(svc, item)
            revision = 0 if current is None else current.revision
            svc.drafts.put(item, Bundle.read(folder), revision, caller=OPERATOR)
            started = time.monotonic()
            report = await svc.tests.run(item, caller=OPERATOR, inputs=inputs, fake=fake)
            seconds = time.monotonic() - started
            return report, seconds, svc.drafts.state(item)


def ran(log: Log, home: Path, folder: Path, inputs: Any) -> tuple[Any, Any, list[Span]]:
    """Test-run `folder` on real models and log its spans, its result and its cost."""
    report, seconds, state = asyncio.run(test_run(home, folder, inputs))
    spans = model_spans(home, report.run_id)
    log_spans(log, spans)
    log(f"test run {report.run_id} {report.status} {report.reason or ''} in {seconds:.0f} s")
    log.check(
        f"the {folder.name} test run passes on real models and the draft reads tested",
        (report.status, state) == ("passed", "tested"),
        (report.status, report.reason, state),
    )
    result = delivered(home, report.run_id)
    log(f"result: {json.dumps(result)[:2500]}")
    errors = schema_errors(folder, result)
    log.check("the result validates against schemas/output.json", errors == [], errors)
    tokens = {k: sum(s.tokens.get(k, 0) for s in spans) for k in ("in", "out", "cache_read")}
    log(f"perf: {folder.name} test run {seconds:.0f} s, {len(spans)} model spans, tokens {tokens}")
    return report, result, spans


def rs1(log: Log, home: Path) -> None:
    report, _, spans = ran(log, home, RS1, {"fixture": True})
    log.check(
        "the test report binds to the draft's content hash",
        report.content_hash == Bundle.read(RS1).content_hash() and not report.stale,
        (report.content_hash, report.stale),
    )
    log(f"roles and models: {sorted({(s.node_id, s.role, s.model) for s in spans}, key=str)}")


def t3(log: Log, home: Path) -> None:
    calls_before = model_calls(home)
    quiet, seconds, _ = asyncio.run(test_run(home, T3, {"fixture": "quiet"}))
    strip = delivered(home, quiet.run_id)
    log(f"quiet day {quiet.run_id} {quiet.status} in {seconds:.1f} s: {json.dumps(strip)[:800]}")
    spans, calls = model_spans(home, quiet.run_id), model_calls(home) - calls_before
    log.check(
        "the quiet-day test run passes with zero model calls",
        (quiet.status, len(spans), calls) == ("passed", 0, 0),
        {"status": quiet.status, "model spans": len(spans), "relayed model calls": calls},
    )
    log.check(
        "the quiet strip has no surprise, no note, and says the guard could not be checked",
        strip is not None
        and (strip["surprise_count"], strip["notes"], strip["guard_cross_check"])
        == (0, [], "could not check: trading node")
        and not schema_errors(T3, strip),
        strip and (strip["surprise_count"], strip["notes"], strip["guard_cross_check"]),
    )
    log(f"perf: T3 quiet-day test run {seconds:.1f} s, 0 tokens")
    surprise, seconds, state = asyncio.run(test_run(home, T3, {"fixture": "surprise"}))
    strip = delivered(home, surprise.run_id)
    spans = model_spans(home, surprise.run_id)
    log_spans(log, spans)
    log(f"surprise day {surprise.run_id} {surprise.status} in {seconds:.0f} s")
    log(f"notes: {json.dumps(strip and strip['notes'])}")
    log.check(
        "the surprise-day test run passes with one scanner note and the draft reads tested",
        surprise.status == "passed"
        and state == "tested"
        and [s.role for s in spans] == ["scanner"]
        and strip is not None
        and len(strip["notes"]) == 1,
        (surprise.status, surprise.reason, state, [s.role for s in spans]),
    )
    log(f"perf: T3 surprise-day test run {seconds:.0f} s, tokens {[s.tokens for s in spans]}")


def rs4(log: Log, home: Path) -> None:
    report, review, spans = ran(log, home, RS4, {"fixture": True})
    scheduled = node_events(home, report.run_id, "node_scheduled", "search")
    chunks = [d["plan"]["chunk"]["items"] for d in scheduled]
    searchers = [s for s in spans if s.node_id == "search" and s.status == "ok"]
    log.check(
        "the sources split into two or more searcher chunks and every chunk's searcher ran",
        len(chunks) >= 2 and len(searchers) == len(chunks),
        {"chunks": chunks, "searchers ok": len(searchers)},
    )
    cite = node_events(home, report.run_id, "node_finished", "cite")
    log.check(
        "the synthesiser ran and the citation check passed its quotes",
        any(s.node_id == "synthesise" and s.status == "ok" for s in spans)
        and [d.get("verdict") for d in cite] == ["pass"],
        [d.get("verdict") for d in cite],
    )
    log(f"headline: {review and review['headline']}")


def a(log: Log, home: Path) -> None:
    report, entry, _ = ran(log, home, A, {"fixture": "one-video"})
    with EngineService.open(home) as svc:
        library = svc.ctx.library
        summary = library.objects(report.run_id, "workflow-run")[-1]
        made = [
            library.get(edge.from_id)
            for edge in library.edges(summary.object_id, "produced-by", reverse=True)
        ]
        files = {
            m.fields["metadata"]["path"]: json.loads(library.get_artifact(str(m.blob)))
            for m in made
            if m.fields["type"] == "run-file"
        }
    log(f"run files produced by {summary.object_id}: {sorted(files)}")
    cards = entry["cards"] if entry else []
    log.check(
        "every card lands as a run file in the Library, linked produced-by to the run",
        bool(cards) and all(files.get(f"library/cards/{c['library_id']}.json") == c for c in cards),
        {"cards": [c["library_id"] for c in cards], "files": len(files)},
    )


def rs0(log: Log, home: Path) -> None:
    _, sheet, _ = ran(log, home, RS0, {"fixture": True})
    assumptions = sheet["assumptions"] if sheet else []
    log.check(
        "the term sheet lists its assumptions and at least one kill criterion",
        bool(assumptions) and bool(sheet and sheet["kill_criteria"]),
        assumptions,
    )


def rs2(log: Log, home: Path) -> None:
    _, card, _ = ran(log, home, RS2, {"fixture": True})
    holes = card["holes"] if card else []
    values = {f"parameter {p['name']}": p["value"] for p in card["parameters"]} if card else {}
    values |= (
        {k: card[k]["value"] for k in ("formula", "data_frequency", "warm_up", "claimed_effect")}
        if card
        else {}
    )
    unresolved = [h for h in holes if values.get(h) == "unresolved"]
    log.check(
        "the component card keeps its holes: each one reads unresolved",
        bool(holes) and unresolved == holes,
        {"holes": holes, "changes": card and card["changes"]},
    )


def a_no_captions(log: Log, home: Path) -> None:
    calls_before = model_calls(home)
    report, entry, spans = ran(log, home, A, {"fixture": "no-captions"})
    rows_seen = [(r["kind"], r["status"]) for r in entry["inventory"]] if entry else []
    log.check(
        "the video with no captions is recorded and the run passes with no model call",
        ("video", "no captions") in rows_seen
        and not spans
        and model_calls(home) == calls_before
        and report.status == "passed",
        rows_seen,
    )


def planted(scratch: Path) -> Path:
    """RS0 with a recorded term sheet that quotes a number the idea never gave, for a fake run."""
    folder = shutil.copytree(RS0, scratch / "rs0-planted", dirs_exist_ok=True)
    path = folder / "fixtures" / "recorded" / "term_sheet.json"
    sheet = json.loads(path.read_text("utf-8"))
    sheet["mechanism"] += " A 2019 backtest earned a Sharpe ratio of 3.7."
    path.write_text(json.dumps(sheet), "utf-8")
    definition = json.loads((folder / "definition.json").read_text("utf-8"))
    definition["id"] = "rs0-planted"
    (folder / "definition.json").write_text(json.dumps(definition), "utf-8")
    return folder


def rv(log: Log, home: Path) -> None:
    folder = planted(throwaway_home("tp2", "rv-planted"))
    plant, _, _ = asyncio.run(test_run(home, folder, {"fixture": True}, fake=True))
    log(f"planted fake run {plant.run_id} {plant.status} {plant.reason or ''}")
    report, card, _ = ran(log, home, RV, None)
    with Reader.open(home) as reader:
        week = [
            run_id
            for (run_id,) in reader.connection.execute(
                "SELECT run_id FROM events WHERE kind = 'run_created' AND run_id != ? ORDER BY seq",
                (report.run_id,),
            )
        ]
    named = [r["run_id"] for r in card["runs"]] if card else []
    parked = [p["run_id"] for p in card["parked"]] if card else []
    log.check(
        "the review names every run of the week in its home and the planted parked run",
        named == week and plant.run_id in parked and plant.status == "failed",
        {"week": len(week), "named": len(named), "parked": parked},
    )
    log(f"summary: {card and card['summary']}")
    log(f"edits: {json.dumps(card and card['edits'])[:1500]}")


def captured(work: Any) -> tuple[int, list[str]]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = work()
    return code, out.getvalue().splitlines()


def snapshot(home: Path) -> tuple[int, int, list[tuple[str, str, bool, str]]]:
    with EngineService.open(home) as svc:
        library = len(svc.ctx.library.events())
    with Reader.open(home) as reader:
        events = reader.connection.execute("SELECT count(*) FROM events").fetchone()[0]
        found = rows.triggers(reader.connection)
    triggers = sorted((t.workflow_item, t.kind, t.enabled, t.pinned_object) for t in found)
    return library, events, triggers


def install(log: Log, home: Path) -> None:
    built = [t.id for t in CATALOG if t.folder and not t.needs]
    drafts = [t.id for t in CATALOG if t.folder and t.needs]
    timed = sorted((t.folder, "cron", False) for t in CATALOG if t.folder for _ in t.triggers)
    for attempt in (1, 2):
        started = time.monotonic()
        code, lines = captured(lambda: asyncio.run(install_templates(home)))
        for line in lines:
            log(f"install {attempt}: {line}")
        log(f"install {attempt} exit {code} in {time.monotonic() - started:.0f} s")
        if attempt == 1:
            _, listed = captured(lambda: list_templates(home))
            for line in listed:
                log(f"list: {line}")
            before = snapshot(home)
            log(f"after install 1: library events {before[0]}, ledger events {before[1]}")
            log(f"triggers: {before[2]}")
            published = [line for line in listed if "published, disabled 0.1.0" in line]
            waiting = [line for line in listed if "validated draft, needs: " in line]
            rest = 31 - len(built) - len(drafts)
            log.check(
                f"the first install publishes {len(built)} disabled at 0.1.0, saves "
                f"{len(drafts)} drafts each with its need, and {rest} are not yet built",
                code == 0
                and [line.split()[0] for line in published] == built
                and [line.split()[0] for line in waiting] == drafts
                and sum(line.endswith("not yet built") for line in listed) == rest
                and listed[-1] == "31 templates",
                (code, [line.split()[0] for line in published], len(waiting), listed[-1:]),
            )
            log.check(
                "each published template has its card's cron trigger, disabled",
                [(t[0], t[1], t[2]) for t in before[2]] == timed,
                before[2],
            )
        else:
            after = snapshot(home)
            log(f"after install 2: library events {after[0]}, ledger events {after[1]}")
            log.check(
                "the second install changes nothing",
                code == 0
                and all(line.split()[2] == "unchanged:" for line in lines)
                and after == before,
                (code, [line.split()[2] for line in lines], after == before),
            )


def db(log: Log, home: Path) -> None:
    _, card, _ = ran(log, home, DB, {"fixture": "busy"})
    facts = card["node_facts"] if card else {}
    log.check(
        "every node fact reads could not check: trading node",
        bool(facts) and set(facts.values()) == {NODE_FACT},
        facts,
    )
    log(f"headline: {card and card['headline']}")
    log(f"summary: {card and card['summary']}")


def lines_of(brief: Any) -> list[Any]:
    return [line for section in brief["sections"].values() for line in section] if brief else []


def t4(log: Log, home: Path) -> None:
    report, brief, spans = ran(log, home, T4, {"fixture": True})
    chunks = [
        d["plan"]["chunk"]["items"]
        for d in node_events(home, report.run_id, "node_scheduled", "analyse")
    ]
    analysts = [s for s in spans if s.node_id == "analyse" and s.status == "ok"]
    log.check(
        "the night splits into two or more analyst chunks and every chunk's analyst ran",
        len(chunks) >= 2 and len(analysts) == len(chunks),
        {"chunks": chunks, "analysts ok": len(analysts)},
    )
    lines = lines_of(brief)
    log.check(
        "the brief has lines and every line links to at least one source",
        bool(lines) and all(line["links"] for line in lines),
        [(line["text"][:60], line["links"]) for line in lines],
    )
    log(f"cut: {json.dumps(brief and brief['cut'])[:1500]}")


def fake_run(log: Log, home: Path, folder: Path, inputs: Any) -> Any:
    """`folder` test-run on the fake switch in a service opened with no harness, so no provider
    can be reached at all."""
    with EngineService.open(home) as svc:
        svc.drafts.put(folder.name, Bundle.read(folder), 0, caller=OPERATOR)
        started = time.monotonic()
        report = asyncio.run(svc.tests.run(folder.name, caller=OPERATOR, inputs=inputs, fake=True))
        seconds = time.monotonic() - started
    with Reader.open(home) as reader:
        profiles = sorted({s.profile for s in reader.spans(report.run_id) if s.profile})
    result = delivered(home, report.run_id)
    errors = schema_errors(folder, result)
    log(f"fake run {report.run_id} {report.status} {report.reason or ''} in {seconds:.1f} s")
    log.check(
        f"the {folder.name} fake run passes with only fake spans and no relay call",
        report.status == "passed" and profiles == ["fake"] and model_calls(home) == 0,
        {"status": report.status, "span profiles": profiles, "relay calls": model_calls(home)},
    )
    log.check("the result validates against schemas/output.json", errors == [], errors)
    return result


def t4_fake(log: Log, home: Path) -> None:
    brief = fake_run(log, home, T4, {"fixture": True})
    log(f"lines: {[line['text'] for line in lines_of(brief)]}")


def db_fake(log: Log, home: Path) -> None:
    card = fake_run(log, home, DB, {"fixture": "busy"})
    log(f"node facts: {card and card['node_facts']}")


def refusal(log: Log, label: str, need: str, attempt: Any) -> int:
    try:
        attempt()
    except Refused as error:
        log(f"{label} refused: {error.code} {error}")
        return int(error.code == "needs_unmet" and str(error).endswith(need))
    log(f"{label} was not refused")
    return 0


def drafts(pr: str, log: Log, home: Path) -> None:
    waiting = [t for t in CATALOG if t.pr == pr and t.needs]
    refused = 0
    for template in waiting:
        item, need = str(template.folder), f"needs: {', '.join(template.needs)}"
        with EngineService.open(home) as svc:
            svc.drafts.put(item, Bundle.read(PACK / item), 0, caller=OPERATOR)
            log(f"{template.id} draft state {svc.drafts.state(item)}")
            refused += refusal(
                log, f"{template.id} test", need,
                lambda: asyncio.run(svc.tests.run(item, caller=OPERATOR)),  # noqa: B023
            )  # fmt: skip
            refusal(
                log, f"{template.id} publish (untested)", need,
                lambda: svc.versions.publish(item, "0.1.0", caller=OPERATOR),  # noqa: B023
            )  # fmt: skip
            forced = svc.ctx.library.publish(item, drafts_ref(item), "0.1.0", principal="lane")
            refused += refusal(
                log, f"{template.id} enable", need,
                lambda: svc.versions.enable(forced, caller=OPERATOR),  # noqa: B023
            )  # fmt: skip
    calls = 2 * len(waiting)
    log.check(
        f"all {calls} test and enable calls are refused with the right need",
        refused == calls,
        refused,
    )


def money(folders: list[Path], log: Log, home: Path) -> None:
    clean = 0
    for folder in folders:
        definition = json.loads((folder / "definition.json").read_text("utf-8"))
        acts = [p for p in validate(load(folder)) if p.code == "money_act"]
        held = [n["id"] for n in definition["nodes"] if n.get("credentials")]
        refs = [
            p.name
            for p in folder.rglob("*")
            if p.is_file()
            and any(w in p.read_text("utf-8") for w in ("qmn", "qmx/ctrader", "qmx/broker"))
        ]
        log(f"{folder.name}: money acts {acts}, credentials {held}, qmn or broker refs {refs}")
        clean += not (acts or held or refs)
    control = shutil.copytree(T4, home / "t4-control")
    planted = json.loads((control / "definition.json").read_text("utf-8"))
    planted["nodes"][2]["parameters"]["after"] = "close_all_positions"
    (control / "definition.json").write_text(json.dumps(planted), "utf-8")
    caught = [p.message for p in validate(load(control)) if p.code == "money_act"]
    log(f"control with a planted money act: {caught}")
    log.check(
        f"all {len(folders)} folders pass the money lint and the planted act is caught",
        clean == len(folders) and bool(caught),
        {"clean": clean, "folders": len(folders), "control caught": bool(caught)},
    )


def readmes(pr: str, log: Log, home: Path) -> None:
    waiting = [t for t in CATALOG if t.pr == pr and t.needs]
    named = 0
    for template in waiting:
        text = (PACK / str(template.folder) / "README.md").read_text("utf-8").splitlines()
        line = next(x for x in text[1:] if x.strip())
        log(f"{template.id}: {line}")
        named += line.startswith("Waits for") and f"`needs: {', '.join(template.needs)}`" in line
    log.check(
        f"each of the {len(waiting)} draft READMEs names its need in one line",
        named == len(waiting),
        named,
    )


def gw(log: Log, home: Path) -> None:
    folder = PACK / "gw-guard-watchdogs"
    problems = validate(load(folder), publish=True)
    definition = json.loads((folder / "definition.json").read_text("utf-8"))
    kinds = [(n["id"], n["type"]) for n in definition["nodes"]]
    bearing = [n for n, kind in kinds if (k := REGISTRY.kind(kind)) and k.model_bearing]
    log(f"nodes: {kinds}")
    log.check(
        "GW validates for publish and holds no model-bearing node",
        problems == [] and bearing == [],
        {"problems": problems, "model-bearing": bearing},
    )


RUNNABLE: Final = [t for t in CATALOG if not t.needs]
DOC: Final = ENGINE / "docs" / "TEMPLATES.md"


def recorded_port() -> Any:
    """The unit tests' port: every model turn answered from the templates' recorded answers, so
    nothing reaches a provider."""
    sys.path.insert(0, str(ENGINE / "tests"))
    from test_templates import answers  # noqa: PLC0415

    return answers()


async def save_and_test(svc: EngineService, item: str, bundle: Bundle, inputs: Any) -> Any:
    current = current_draft(svc, item)
    revision = 0 if current is None else current.revision
    svc.drafts.put(item, bundle, revision, caller=OPERATOR)
    return await svc.tests.run(item, caller=OPERATOR, inputs=inputs)


async def tested(home: Path, item: str, bundle: Bundle, inputs: Any, *, recorded: bool) -> Any:
    """`bundle` saved as the draft `item` and test-run, on the recorded answers or on real
    models through the home's harness."""
    if recorded:
        with EngineService.open(home, harness=recorded_port()) as svc:
            return await save_and_test(svc, item, bundle, inputs)
    async with harnessed(home) as opened:
        with EngineService.open(
            home, settings=ControlSettings(opened.control), harness=HarnessAdapter(opened.harness)
        ) as svc:
            return await save_and_test(svc, item, bundle, inputs)


def tokens_of(spans: list[Span]) -> dict[str, int]:
    return {k: sum(s.tokens.get(k, 0) for s in spans) for k in ("in", "out", "cache_read")}


def pack_tests(log: Log, home: Path, *, recorded: bool) -> None:
    """Each runnable template test-run once with its catalogue inputs: the wall time of each and
    of the whole pack, and the pack's model spans and tokens (the cost Appendix E asks for)."""
    total_s, spans_n, tokens = 0.0, 0, dict.fromkeys(("in", "out", "cache_read"), 0)
    failing = []
    for template in RUNNABLE:
        folder = PACK / str(template.folder)
        started = time.monotonic()
        report = asyncio.run(
            tested(home, folder.name, Bundle.read(folder), template.test_inputs, recorded=recorded)
        )
        seconds = time.monotonic() - started
        spans = model_spans(home, report.run_id)
        errors = schema_errors(folder, delivered(home, report.run_id))
        if report.status != "passed" or errors:
            failing.append(template.id)
        total_s += seconds
        spans_n += len(spans)
        for name, count in tokens_of(spans).items():
            tokens[name] += count
        log(
            f"{template.id} {report.run_id} {report.status} {report.reason or ''}"
            f" in {seconds:.1f} s, {len(spans)} model spans, tokens {tokens_of(spans)},"
            f" schema errors {errors}"
        )
    log.check(
        f"{len(RUNNABLE) - len(failing)} of {len(RUNNABLE)} runnable templates pass their test run",
        not failing,
        failing,
    )
    kind = "recorded answers, no provider" if recorded else "real models"
    log(f"perf: pack test runs on {kind}: {total_s:.0f} s wall in all ({total_s / 60:.1f} min)")
    log(f"cost: pack test runs on {kind}: {spans_n} model spans, tokens {tokens}")
    if total_s > 3600:
        log("note: a full retest of the pack takes over 60 minutes")


def show(log: Log, lines: list[str], png: str) -> None:
    """`lines` in a console window of their own, tall enough for the whole pack, grabbed with
    ffmpeg as `<png>.png`."""
    text = log.path.parent / f"{log.path.stem}.txt"
    text.write_text("\n".join(lines) + "\n", encoding="utf-8")
    title = f"TP4 {png}"
    viewer = (
        "import ctypes,os,time;"
        f"ctypes.windll.kernel32.SetConsoleTitleW({title!r});"
        f"os.system('mode con: cols=110 lines={len(lines) + 3}');"
        f"print(open({str(text)!r},encoding='utf-8').read(),flush=True);time.sleep(12)"
    )
    subprocess.Popen(["conhost.exe", sys.executable, "-c", viewer])  # noqa: S607
    time.sleep(5)
    shot = log.path.parent / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}{png}.png"
    grab = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "gdigrab"]
    done = subprocess.run([*grab, "-i", f"title={title}", "-frames:v", "1", str(shot)], check=False)
    log(f"screen {shot}: ffmpeg exit {done.returncode}")


def install_recorded(log: Log, home: Path) -> None:
    """`templates install` on a fresh home with every model turn answered from the recorded
    answers, then the pack read back through the engine host's workflow doors, and `templates
    list` shown in a console window grabbed as `tp4-install.png`."""
    from x13_doors import host  # noqa: PLC0415

    with EngineService.open(home, harness=recorded_port()) as svc:
        done = asyncio.run(install_pack(svc))
    for found in done:
        log(f"install: {found.template.id} {found.action}: {found.detail[:160]}")
    actions = [(f.template.id, f.action) for f in done]
    log.check(
        "the install publishes the 9 runnable templates and saves the 22 others as drafts",
        actions == [(t.id, "saved draft" if t.needs else "published") for t in CATALOG],
        actions,
    )
    published, waiting = [], []
    with host(log, home, "tp4-install-host") as (client, _, _):
        for template in CATALOG:
            item = str(template.folder)
            versions = client.get(f"/api/workflows/{item}/versions").json()
            draft = client.get(f"/api/workflows/{item}/draft").json()
            needs = tuple(draft["definition"]["meta"].get("needs", []))
            states = [(v["semver"], v["state"]) for v in versions]
            log(f"host: {template.id} versions {states} draft {draft['state']} needs {needs}")
            if states == [("0.1.0", "published")]:
                published.append(template.id)
            elif not states and draft["state"] == "validated" and needs == template.needs:
                waiting.append(template.id)
    log.check(
        "the host shows 9 published and disabled and 22 drafts, each with its own need",
        published == [t.id for t in RUNNABLE] and waiting == [t.id for t in CATALOG if t.needs],
        {"published": published, "drafts": len(waiting)},
    )
    _, listed = captured(lambda: list_templates(home))
    for line in listed:
        log(f"list: {line}")
    log.check(
        "templates list shows 31 rows: 9 published and disabled, 22 drafts with their need",
        listed[-1] == "31 templates"
        and sum("published, disabled 0.1.0" in line for line in listed) == 9
        and sum("validated draft, needs: " in line for line in listed) == 22,
        listed[-1:],
    )
    show(log, ["templates list (recorded answers, no provider)", *listed], "tp4-install")


def variant(log: Log, home: Path, *, recorded: bool) -> None:
    """RS1 cloned as a variant through `extends` and test-run; once published, the variant names
    RS1's version as the one it is a variant of."""
    inputs = find("RS1").test_inputs
    first = asyncio.run(tested(home, RS1.name, Bundle.read(RS1), inputs, recorded=recorded))
    log(f"RS1 test run {first.run_id} {first.status}")
    item = "rs1-fx-papers"
    with EngineService.open(home) as svc:
        parent = svc.versions.publish(RS1.name, "0.1.0", caller=OPERATOR)
    patch = {"op": "replace", "path": "/settings/timezone", "value": "Europe/London"}
    overlay = {
        "schema": "qmx.workflow/1",
        "id": item,
        "name": "Paper scout for FX papers",
        "extends": {"workflow_item": RS1.name, "object_id": parent, "patches": [patch]},
    }
    report = asyncio.run(tested(home, item, Bundle(overlay, {}), inputs, recorded=recorded))
    log(f"variant test run {report.run_id} {report.status} {report.reason or ''}")
    with EngineService.open(home) as svc:
        published = svc.versions.publish(item, "0.1.0", caller=OPERATOR)
        targets = [edge.to_id for edge in svc.ctx.library.edges(published, "variant-of")]
    log(f"variant {published} variant-of {targets}; parent {parent}")
    log.check(
        "the variant passes its test run and records variant_of RS1's version",
        report.status == "passed" and targets == [parent],
        (report.status, targets, parent),
    )


def doc_rows() -> list[list[str]]:
    """The TEMPLATES.md table as the catalogue and the definitions give it."""
    found = []
    for template in CATALOG:
        definition = json.loads((PACK / str(template.folder) / "definition.json").read_text())
        trigger = next(n for n in definition["nodes"] if n["type"] == "trigger")
        crons = [f"cron `{c.expr}` {c.zone}" for c in template.triggers]
        kinds = [
            "cron (schedule not set yet)" if k == "cron" else k
            for k in trigger["parameters"]["kinds"]
            if k != "cron" or not crons
        ]
        if template.needs:
            status, cost = "draft", "none until it can run"
        else:
            status, cost = "published, disabled", template.test_cost or "not measured yet"
        needs = ", ".join(f"`{n}`" for n in template.needs) or "none"
        found.append([template.id, template.name, status, cost, ", ".join(crons + kinds), needs])
    return found


def doc(log: Log, home: Path) -> None:
    lines = DOC.read_text("utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Id |"))
    table = []
    for line in lines[start + 2 :]:
        if not line.startswith("| "):
            break
        table.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    expected = doc_rows()
    for got, want in zip(table, expected, strict=False):
        if got != want:
            log(f"differs: doc {got} catalogue {want}")
    log.check(
        f"TEMPLATES.md has {len(expected)} rows and each matches the catalogue",
        table == expected,
        {"doc rows": len(table), "catalogue rows": len(expected)},
    )


LANES: Final = {
    "rs1": ("tp1", rs1),
    "t3": ("tp1", t3),
    "install": ("tp1", install),
    "rs4": ("tp2", rs4),
    "a": ("tp2", a),
    "rs0": ("tp2", rs0),
    "rs2": ("tp2", rs2),
    "a-no-captions": ("tp2", a_no_captions),
    "rv": ("tp2", rv),
    "db": ("tp3", db),
    "t4": ("tp3", t4),
    "drafts": ("tp3", partial(drafts, "TP3")),
    "money": ("tp3", partial(money, TP3_FOLDERS)),
    "readmes": ("tp3", partial(readmes, "TP3")),
    "gw": ("tp3", gw),
    "t4-fake": ("tp3", t4_fake),
    "db-fake": ("tp3", db_fake),
    "all": ("tp4", partial(pack_tests, recorded=False)),
    "all-recorded": ("tp4", partial(pack_tests, recorded=True)),
    "install-recorded": ("tp4", install_recorded),
    "drafts-tp4": ("tp4", partial(drafts, "TP4")),
    "readmes-tp4": ("tp4", partial(readmes, "TP4")),
    "doc": ("tp4", doc),
    "variant": ("tp4", partial(variant, recorded=False)),
    "variant-recorded": ("tp4", partial(variant, recorded=True)),
    "money-pack": ("tp4", partial(money, PACK_FOLDERS)),
}
NO_MODEL: Final = frozenset(
    {
        "drafts",
        "money",
        "readmes",
        "gw",
        "t4-fake",
        "db-fake",
        "all-recorded",
        "install-recorded",
        "drafts-tp4",
        "readmes-tp4",
        "doc",
        "variant-recorded",
        "money-pack",
    }
)
"""Lanes that open no harness and add no provider row: they spend nothing."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", help="the PR whose evidence folder the logs go to")
    parser.add_argument("--shared", help="run every lane on one fresh home of this name")
    parser.add_argument("lanes", nargs="*", help=f"any of {', '.join(LANES)}")
    args = parser.parse_args()
    wanted = args.lanes or ["rs1", "t3", "install"]
    unknown = [name for name in wanted if name not in LANES]
    if unknown:
        parser.error(f"unknown lanes: {unknown}")
    prefix = os.environ.get("ENGINE_LOG_PREFIX", "")
    boot()
    shared = openrouter_home(args.pr or "tp2", args.shared) if args.shared else None
    failed = 0
    for name in wanted:
        owner, lane = LANES[name]
        pr = args.pr or owner
        os.environ["ENGINE_LOG_PREFIX"] = prefix  # each lane's harness boot scrubs it again
        log = Log(pr, f"{pr}-{name}")
        home = throwaway_home(pr, name) if name in NO_MODEL else shared or openrouter_home(pr, name)
        log(f"home {home}")
        lane(log, home)
        log(f"OpenRouter spend on this home so far, upper bound: ${relay_usd(home):.4f}")
        failed += log.verdict()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
