"""TP1's template lanes: RS1 and T3 test-run on real models, and the pack installed twice.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/t_templates.py [rs1|t3|install ...]`
None named runs all three, in order. Each lane writes
`evidence/tp1/<ENGINE_LOG_PREFIX>tp1-<lane>.log` on its own throwaway home whose only provider row
is OpenRouter's, and the script exits 1 if any lane failed. No lane touches the plan login or the
ship home.

- `rs1` (lane 2): RS1 is saved as a draft and test-run on its fixture papers through each role's
  test candidates (the test-only Kimi row first). Pass when the run passes, the test report binds
  to the draft's content hash, and the delivered note validates against `schemas/output.json`.
- `t3` (lane 3): T3 is test-run on its quiet fixture day, then its surprise day. Pass when the
  quiet run passes with no model span and no relayed model call, and the surprise run passes with
  one `scanner` note.
- `install` (lane 4): `templates install` runs twice on a fresh home. Pass when the first run
  publishes RS1 and T3 at 0.1.0 with their cron triggers disabled and lists the other 29 as not
  yet built, and the second run changes nothing in the Library, the ledger or the triggers.

Spend is the relay journals' upper bound at the Kimi row's list prices.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import ENGINE_STORE, Log, boot, throwaway_home

os.environ.setdefault("QMA_LIVE_SCRATCH", str(ENGINE_STORE / "homes" / "tp1-scratch"))

from jsonschema import Draft202012Validator
from llm_lanes import OPENROUTER_ROW, harnessed, relay_usd
from qmx_engine.__main__ import install_templates, list_templates
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.templates.catalog import PACK
from qmx_engine.templates.install import current_draft
from qmx_engine.triggers import rows

PR: Final = "tp1"
RS1: Final = PACK / "rs1-paper-scout"
T3: Final = PACK / "t3-news-calendar-watch"


def openrouter_home(slug: str) -> Path:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home(PR, slug)
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


def model_spans(home: Path, run_id: str) -> list[Span]:
    with Reader.open(home) as reader:
        return [s for s in reader.spans(run_id) if s.profile is not None]


def log_spans(log: Log, spans: list[Span]) -> None:
    for span in spans:
        log(
            f"span {span.node_id} partition {span.partition} attempt {span.attempt} {span.status}: "
            f"{span.role} on {span.profile}/{span.model} tokens {span.tokens}"
        )


def schema(folder: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads((folder / "schemas" / "output.json").read_text("utf-8")))


async def test_run(home: Path, folder: Path, inputs: Any) -> tuple[Any, float, str]:
    """A draft saved from `folder`, test-run with `inputs`; the report, its seconds, and the
    draft's state after."""
    async with harnessed(home) as opened:
        with EngineService.open(
            home, settings=ControlSettings(opened.control), harness=HarnessAdapter(opened.harness)
        ) as svc:
            item = folder.name
            current = current_draft(svc, item)
            revision = 0 if current is None else current.revision
            svc.drafts.put(item, Bundle.read(folder), revision, caller=OPERATOR)
            started = time.monotonic()
            report = await svc.tests.run(item, caller=OPERATOR, inputs=inputs)
            seconds = time.monotonic() - started
            return report, seconds, svc.drafts.state(item)


def rs1(log: Log) -> None:
    home = openrouter_home("rs1")
    report, seconds, state = asyncio.run(test_run(home, RS1, {"fixture": True}))
    spans = model_spans(home, report.run_id)
    log_spans(log, spans)
    log(f"test run {report.run_id} {report.status} {report.reason or ''} in {seconds:.0f} s")
    log.check(
        "the RS1 test run passes on real models and the draft reads tested",
        (report.status, state) == ("passed", "tested"),
        (report.status, report.reason, state),
    )
    log.check(
        "the test report binds to the draft's content hash",
        report.content_hash == Bundle.read(RS1).content_hash() and not report.stale,
        (report.content_hash, report.stale),
    )
    note = delivered(home, report.run_id)
    errors = [e.message for e in schema(RS1).iter_errors(note)] if note is not None else ["none"]
    log(f"note: {json.dumps(note)[:1500]}")
    log.check("the delivered note validates against schemas/output.json", errors == [], errors[:3])
    roles = sorted({(s.node_id, s.role, s.model) for s in spans}, key=str)
    log(f"roles and models: {roles}")
    tokens = {k: sum(s.tokens.get(k, 0) for s in spans) for k in ("in", "out", "cache_read")}
    log(f"perf: RS1 test run {seconds:.0f} s, {len(spans)} model spans, tokens {tokens}")
    log(f"OpenRouter spend on this home, upper bound: ${relay_usd(home):.4f}")


def t3(log: Log) -> None:
    home = openrouter_home("t3")
    quiet, seconds, _ = asyncio.run(test_run(home, T3, {"fixture": "quiet"}))
    strip = delivered(home, quiet.run_id)
    log(f"quiet day {quiet.run_id} {quiet.status} in {seconds:.1f} s: {json.dumps(strip)[:800]}")
    spans, calls = model_spans(home, quiet.run_id), model_calls(home)
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
        and not list(schema(T3).iter_errors(strip)),
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
    log(f"OpenRouter spend on this home, upper bound: ${relay_usd(home):.4f}")


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


def install(log: Log) -> None:
    home = openrouter_home("install")
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
            log.check(
                "the first install publishes RS1 and T3 disabled at 0.1.0; 29 are not yet built",
                code == 0
                and [line.split()[0] for line in published] == ["RS1", "T3"]
                and sum(line.endswith("not yet built") for line in listed) == 29
                and listed[-1] == "31 templates",
                (code, published, listed[-1] if listed else None),
            )
            log.check(
                "each published template has its cron trigger, disabled",
                [(t[0], t[1], t[2]) for t in before[2]]
                == [("rs1-paper-scout", "cron", False), ("t3-news-calendar-watch", "cron", False)],
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
    log(f"OpenRouter spend on this home, upper bound: ${relay_usd(home):.4f}")


LANES: Final = {"rs1": rs1, "t3": t3, "install": install}


def main() -> int:
    wanted = sys.argv[1:] or list(LANES)
    prefix = os.environ.get("ENGINE_LOG_PREFIX", "")
    boot()
    os.environ["ENGINE_LOG_PREFIX"] = prefix  # the boot scrub drops it
    failed = 0
    for name in wanted:
        log = Log(PR, f"tp1-{name}")
        LANES[name](log)
        failed += log.verdict()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
