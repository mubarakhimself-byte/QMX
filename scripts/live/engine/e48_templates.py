"""E48: the template pack holds at one head. Every catalogue row is put on a throwaway home as a
draft: a runnable template runs its test case on haiku through the ship home's plan login and must
pass, and a draft must be refused by the name of the need it waits for. The renamed ids resolve, the
perf line counts the haiku turns and the wall time of the whole pack, and two cheap lanes sit beside
it: `--intake` runs template A on a 20-video playlist fixture on the fake provider (no model), and
`--alias` installs a template by an id it used before TPL1.

Run it from `qmx-agents/`: `uv run --no-sync python ../scripts/live/engine/e48_templates.py`.
The plan lane opens the harness on the ship home only while it holds the lane lock, as
`common.plan_harness` does; the engine itself runs on a throwaway home under the store's homes/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import boot, plan_harness

from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import ControlSettings, StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.templates.catalog import ALIASES, CATALOG, PACK, find
from qmx_engine.templates.install import current_draft, install

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "tpl1"
HOMES: Final = STORE / "homes"
HAIKU: Final = ("claude/haiku",)
BOUND_S: Final = 420.0
"""One template's test run is bounded, so one stuck turn cannot stall the whole lane."""
ORDER_KEYS: Final = frozenset({"roles.test_only", "roles.test_order", "roles.live_order"})


class Log:
    """`<store>/evidence/tpl1/owner-<slug>.log`, with the PASS/FAIL lines a lane is read for."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"owner-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> bool:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= bool(ok)
        return bool(ok)

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


def home(slug: str) -> Path:
    root = HOMES / f"tpl1-{slug}"
    import shutil  # noqa: PLC0415

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def spans_of(root: Path, run_id: str) -> list[Any]:
    with Reader.open(root) as reader:
        return [s for s in reader.spans(run_id) if s.profile is not None]


def delivered(root: Path, run_id: str) -> Any:
    with Reader.open(root) as reader:
        found = [
            e.data["outputs"]["main"]
            for e in reader.events(run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "deliver"
        ]
    return found[0] if found else None


def tokens_of(spans: list[Any]) -> dict[str, int]:
    return {k: sum(s.tokens.get(k, 0) for s in spans) for k in ("in", "out", "cache_read")}


def plan_settings(control: Any) -> StaticSettings:
    """The ship home's settings with every role mapped to haiku for this lane only."""
    settings: Any = ControlSettings(control)
    return StaticSettings(
        {
            key: HAIKU if key.startswith("roles.") and key not in ORDER_KEYS else value
            for key, value in settings.values().items()
        }
    )


async def pack(log: Log, root: Path, only: tuple[str, ...] = ()) -> None:
    """Every catalogue row through a test run on haiku, or its declared need's refusal."""
    ran, refused, turns, failures = [], [], 0, []
    wall = 0.0
    wanted = [t for t in CATALOG if not only or t.id in only]
    async with plan_harness(log) as opened:
        settings = plan_settings(opened.control)
        adapter = HarnessAdapter(opened.harness)
        with EngineService.open(root, settings=settings, harness=adapter) as svc:
            for template in wanted:
                folder = PACK / template.folder
                current = current_draft(svc, folder.name)
                svc.drafts.put(
                    folder.name,
                    Bundle.read(folder),
                    0 if current is None else current.revision,
                    caller=OPERATOR,
                )
                model_turns = 0
                started = time.monotonic()
                if template.needs:
                    try:
                        await asyncio.wait_for(
                            svc.tests.run(folder.name, caller=OPERATOR), timeout=BOUND_S
                        )
                    except TimeoutError:
                        failures.append(template.id)
                        log(f"{template.id} hung past {BOUND_S:.0f} s with no report")
                        continue
                    except Refused as why:
                        seconds = time.monotonic() - started
                        wall += seconds
                        expected = f"needs: {', '.join(template.needs)}"
                        refused.append(template.id)
                        log(
                            f"{template.id} refused {why.code}: {why} in {seconds:.1f} s;"
                            f" expected {expected}"
                        )
                        if why.code != "needs_unmet" or not str(why).endswith(expected):
                            failures.append(template.id)
                        continue
                    failures.append(template.id)
                    log(f"{template.id} ran a test it had to be refused")
                    continue
                try:
                    report = await asyncio.wait_for(
                        svc.tests.run(folder.name, caller=OPERATOR, inputs=template.test_inputs),
                        timeout=BOUND_S,
                    )
                except TimeoutError:
                    failures.append(template.id)
                    log(f"{template.id} hung past {BOUND_S:.0f} s with no report")
                    continue
                seconds = time.monotonic() - started
                wall += seconds
                spans = spans_of(root, report.run_id)
                model_turns += len(spans)
                turns += len(spans)
                ran.append(template.id)
                errors = _schema_errors(folder, delivered(root, report.run_id))
                log(
                    f"{template.id} {report.run_id} {report.status} {report.reason or ''} in"
                    f" {seconds:.1f} s, {len(spans)} haiku turns, tokens {tokens_of(spans)},"
                    f" schema errors {errors}"
                )
                if report.status != "passed" or errors:
                    failures.append(template.id)
    runnable = sum(1 for t in wanted if not t.needs)
    log.check(
        f"{len(ran)} of {runnable} runnable templates pass a real haiku test run",
        len(ran) == runnable and not failures,
        {"ran": len(ran), "failed": failures},
    )
    log.check(
        f"{len(refused)} of {sum(1 for t in wanted if t.needs)} drafts are refused by the name of"
        " the need they wait for",
        len(refused) == sum(1 for t in wanted if t.needs),
        {"refused": len(refused), "failed": failures},
    )
    log(
        f"perf lane 2: {turns} haiku turns over {len(ran)} real test runs and"
        f" {len(refused)} refusals, {wall:.0f} s wall in all ({wall / 60:.1f} min)"
    )
    turns_log = Log("tpl1-turns")
    turns_log(f"lane 2 haiku turns: {turns}")
    turns_log(f"lane 2 real test runs: {len(ran)}")
    turns_log(f"lane 2 refusals: {len(refused)}")
    turns_log(f"lane 2 wall: {wall:.0f} s ({wall / 60:.1f} min)")
    turns_log(f"lane 2 templates: {len(ran) + len(refused)}")
    turns_log.check("the haiku turn count for Appendix E is recorded", turns > 0, turns)


def _schema_errors(folder: Path, value: Any) -> list[str]:
    from jsonschema import Draft202012Validator  # noqa: PLC0415

    if value is None:
        return ["nothing was delivered"]
    schema = json.loads((folder / "schemas" / "output.json").read_text(encoding="utf-8"))
    return [e.message for e in Draft202012Validator(schema).iter_errors(value)][:3]


def renamed_ids(log: Log) -> None:
    """Every id the pack used before TPL1 finds its template, and every id is a plain phrase."""
    wrong = [old for old, new in ALIASES.items() if find(old).id != new]
    log.check(f"{len(ALIASES)} old ids resolve to their renamed template", not wrong, wrong[:5])
    log.check(
        "every catalogue id is a plain phrase the shelf can show",
        all(t.id == t.id.casefold() and " " not in t.id for t in CATALOG)
        and find("RS1") is find("paper-scout-to-research-note")
        and find("a-fill-the-library") is find("video-to-strategy-ideas"),
        [t.id for t in CATALOG][:3],
    )


def intake(log: Log) -> None:
    """Lane 4: template A takes one playlist URL and the run fans out over all 20 videos."""
    sys.path.insert(0, str(PACK.parents[2] / "tests"))
    from test_templates import answers  # noqa: PLC0415

    root = home("intake")
    folder = PACK / "a-fill-the-library"

    async def run() -> Any:
        with EngineService.open(root, harness=answers()) as svc:
            svc.drafts.put(folder.name, Bundle.read(folder), 0, caller=OPERATOR)
            return await svc.tests.run(
                folder.name, caller=OPERATOR, inputs={"fixture": "playlist"}, fake=True
            )

    report = asyncio.run(run())
    with Reader.open(root) as reader:
        events = reader.events(report.run_id)
    took = [
        e.data["outputs"]["main"]
        for e in events
        if e.kind == "node_finished" and e.data.get("node_id") == "intake"
    ]
    expanded = took[0] if took else {}
    rows = expanded.get("inventory") or []
    collections = expanded.get("collections") or []
    playlist = "https://youtube.com/playlist?list=qmxFixturePlaylist"
    log(f"test run {report.run_id} {report.status} {report.reason or ''}")
    log(f"collections: {collections}")
    log(f"inventory: {len(rows)} rows, first {rows[0] if rows else None}")
    log.check(
        "one playlist URL expands into its 20 videos without asking",
        len(rows) == 20
        and collections
        and collections[0].get("items") == 20
        and collections[0].get("expanded_by") == "fixture"
        and all(playlist in row["provenance"] for row in rows),
        {"rows": len(rows), "collections": collections},
    )
    plans = [
        e.data["plan"]
        for e in events
        if e.kind == "node_scheduled" and e.data.get("node_id") == "triage"
    ]
    spans_of_items = [plan.get("chunk", {}).get("items") for plan in plans]
    log(
        f"triage plans: {len(plans)}, over {plans[0].get('of') if plans else None},"
        f" spans {spans_of_items[:3]}...{spans_of_items[-1:]}"
    )
    log.check(
        "the chunked triage edge fans out over all 20 expanded items",
        len(plans) == 20
        and all(plan.get("of") == 20 for plan in plans)
        and spans_of_items == [[index, index + 1] for index in range(20)],
        {"plans": len(plans), "last": spans_of_items[-1:]},
    )


def alias(log: Log) -> None:
    """Lane 5: install a template by an id it used before TPL1, and the renamed one is installed."""
    root = home("alias")

    async def run() -> list[Any]:
        with EngineService.open(root) as svc:
            return await install(svc, [find("B")], caller=OPERATOR)

    done = asyncio.run(run())
    found = [(i.template.id, i.template.name, i.action, i.detail) for i in done]
    log(f"installed by the old id B: {found}")
    log.check(
        "installing by the old id B installs the renamed template",
        found
        and found[0][0] == "strategy-idea-to-paper-tested"
        and found[0][2] == "saved draft"
        and "needs: qmb-door" in found[0][3],
        found,
    )


def cost(log: Log) -> None:
    """Lane 6: every runnable row's test cost names its cache tokens and no longer reads "0k in"."""
    measured = [(t.id, t.test_cost) for t in CATALOG if not t.needs and t.test_cost]
    for name, line in measured:
        log(f"{name}: {line}")
    wrong = [name for name, line in measured if "cache read" not in line or "0k in" in line]
    log.check(
        f'{len(measured)} test cost strings name their cache tokens and none reads "0k in"',
        not wrong,
        wrong,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lane", choices=("pack", "renamed", "intake", "alias", "cost"), default="pack"
    )
    parser.add_argument("--only", default="", help="comma-separated catalogue ids for this run")
    args = parser.parse_args()
    boot()
    if args.lane == "renamed":
        log = Log("tpl1-e48")
        renamed_ids(log)
        return log.verdict()
    if args.lane == "intake":
        log = Log("tpl1-intake")
        intake(log)
        return log.verdict()
    if args.lane == "alias":
        log = Log("tpl1-alias")
        alias(log)
        return log.verdict()
    if args.lane == "cost":
        log = Log("tpl1-cost")
        cost(log)
        return log.verdict()
    log = Log("tpl1-e48")
    renamed_ids(log)
    asyncio.run(pack(log, home("e48"), tuple(found for found in args.only.split(",") if found)))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
