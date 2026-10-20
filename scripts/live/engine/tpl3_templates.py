"""TPL3's live lanes: the five new templates on haiku, the panel across three provider rows, the
clipping fed twice, and the menu lanes that prove the crystallise pattern and the digest cursor
without a model.

Run it from `qmx-agents/`: `uv run --no-sync python ../scripts/live/engine/tpl3_templates.py <lane>`.

- `runs` (lane 2): every new template's test run on `claude/haiku` through the ship home's plan login,
  under the lane lock, with the haiku turns counted per template (the perf block). No fail rule on
  the count.
- `panel` (lane 3): the same panel on haiku and the OpenRouter DeepSeek and Kimi rows. The OpenRouter
  row is added to a throwaway control in memory only; the ship home's `settings.toml` is hashed before
  and after and must not change.
- `dedupe` (lane 4): the same clipping fed to two runs on one home: the first lands it, the second
  links to it and summarises nothing.
- `crystallise` (lane 5), `digest` (lane 6), `nest` (lane 7): menu lanes, no model spend.
- `turns` (lane 8): read the haiku turn counts back out of the lane 2 log.

Every lane writes `<store>/evidence/tpl3/owner-<slug>.log`. No lane reads the plan login or a
provider key: the harness and its relay read them in process, as production does.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import SHIP_HOME, boot, lane_lock, live, plan_harness, throwaway_home

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.ports.settings import ControlSettings, StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.templates.catalog import PACK, Template, find
from qmx_engine.templates.install import current_draft

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "tpl3"
HOMES: Final = STORE / "homes"
HAIKU: Final[tuple[str, ...]] = ("claude/haiku",)
BOUND_S: Final = 480.0
DEEPSEEK: Final = "openrouter/deepseek/deepseek-v4.1-flash"
KIMI: Final = "openrouter/moonshotai/kimi-k2.5"
OPENROUTER_ROW: Final[dict[str, Any]] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "moonshotai/kimi-k2.5"),
}
ORDER_KEYS: Final = frozenset({"roles.test_only", "roles.test_order", "roles.live_order"})
WANTED: Final[tuple[str, ...]] = (
    "revolution-loop",
    "ask-the-panel",
    "clippings-into-research",
    "morning-digest",
    "crystallise-a-workflow",
)
PANEL_SETTINGS: Final[dict[str, Any]] = {
    **DEFAULTS,
    "roles.triage": HAIKU,
    "roles.judge": HAIKU,
    "roles.searcher": (DEEPSEEK,),
    "roles.reviewer": (KIMI,),
    "roles.test_only": (DEEPSEEK, KIMI),
}


class Log:
    """`<store>/evidence/tpl3/owner-<slug>.log`, with the PASS/FAIL lines a lane is read for."""

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
    root = HOMES / f"tpl3-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def spans_of(root: Path, run_id: str) -> list[Any]:
    with Reader.open(root) as reader:
        return [span for span in reader.spans(run_id) if span.profile is not None]


def delivered(root: Path, run_id: str, node: str = "deliver") -> Any:
    with Reader.open(root) as reader:
        found = [
            event.data["outputs"]["main"]
            for event in reader.events(run_id)
            if event.kind == "node_finished" and event.data.get("node_id") == node
        ]
    return found[0] if found else None


def plan_settings(control: Any) -> StaticSettings:
    """The ship home's settings with every role mapped to haiku for the lane only."""
    settings: Any = ControlSettings(control)
    return StaticSettings(
        {
            key: HAIKU if key.startswith("roles.") and key not in ORDER_KEYS else value
            for key, value in settings.values().items()
        }
    )


def run_one(svc: EngineService, template: Template, log: Log) -> Any:
    """One template put on the home as a draft and test-run, bounded so a stuck turn cannot hang
    the lane."""
    folder = PACK / template.folder
    current = current_draft(svc, folder.name)
    svc.drafts.put(
        folder.name,
        Bundle.read(folder),
        0 if current is None else current.revision,
        caller=OPERATOR,
    )
    return svc.tests.run(folder.name, caller=OPERATOR, inputs=template.test_inputs)


async def runs(log: Log) -> int:
    """Lane 2: all five new templates on haiku, and the haiku turns each of them took."""
    root = home("runs")
    turns: dict[str, int] = {}
    seconds: dict[str, float] = {}
    failures: list[str] = []
    async with plan_harness(log) as opened:
        settings = plan_settings(opened.control)
        with EngineService.open(
            root, settings=settings, harness=HarnessAdapter(opened.harness)
        ) as svc:
            for name in WANTED:
                template = find(name)
                began = time.monotonic()
                try:
                    report = await asyncio.wait_for(run_one(svc, template, log), timeout=BOUND_S)
                except TimeoutError:
                    failures.append(name)
                    log(f"{name} hung past {BOUND_S:.0f} s with no report")
                    continue
                spans = spans_of(root, report.run_id)
                turns[name] = len(spans)
                seconds[name] = time.monotonic() - began
                card = delivered(root, report.run_id)
                log(
                    f"{name} {report.run_id} {report.status} {report.reason or ''} in"
                    f" {seconds[name]:.0f} s, {len(spans)} haiku turns, card {bool(card)}"
                )
                if report.status != "passed":
                    failures.append(name)
    log.check(
        f"{len(WANTED) - len(failures)} of {len(WANTED)} new templates pass a haiku test run",
        not failures,
        {"turns": turns, "failed": failures},
    )
    log(f"perf lane 2: haiku turns per template {turns}")
    log(f"perf lane 2: wall time per template {seconds}")
    turns_log = Log("turns")
    turns_log(f"haiku turns per template: {json.dumps(turns)}")
    turns_log(f"wall time per template: {json.dumps(seconds)}")
    turns_log.check("the haiku turn count per template is recorded", bool(turns), turns)
    return log.verdict()


def openrouter_control() -> Any:
    """The ship home's control with the OpenRouter row added in memory only, never in its file."""
    from qma.harness.routes import parse_claude_document, parse_environment_document
    from qmx_control.service import ControlService

    class OpenRouterControl(ControlService):
        def settings_get(self, section: Any) -> Any:
            found = super().settings_get(section)
            return {**found, "openrouter": OPENROUTER_ROW} if section == "providers" else found

    return OpenRouterControl(
        SHIP_HOME,
        settings_parsers={
            "claude": parse_claude_document,
            "environment": parse_environment_document,
        },
    )


async def panel(log: Log) -> int:
    """Lane 3: the panel on haiku and the OpenRouter DeepSeek and Kimi rows."""
    import hashlib

    from qma.harness import Harness, QmxHome
    from qmx_engine.ports.router import adopt
    from qmx_host.host import RelayRouter, harness_relay

    settings_file = SHIP_HOME / "settings.toml"
    before = hashlib.sha256(settings_file.read_bytes()).hexdigest()
    root = home("panel")
    control = openrouter_control()
    harness = None
    try:
        with lane_lock(log):
            harness = await Harness.open(QmxHome(SHIP_HOME), control=control)
            adopt(RelayRouter(harness_relay(harness)))
            template = find("ask-the-panel")
            log(f"profiles the harness runs: {sorted(HarnessAdapter(harness).profiles())}")
            with EngineService.open(
                root, settings=StaticSettings(PANEL_SETTINGS), harness=HarnessAdapter(harness)
            ) as svc:
                report = await asyncio.wait_for(run_one(svc, template, log), timeout=BOUND_S)
            adopt(None)
    finally:
        if harness is not None:
            await harness.close()
        control.close()
    card = delivered(root, report.run_id)
    spans = spans_of(root, report.run_id)
    rows = [(span.node_id, span.profile, span.model) for span in spans]
    for row in rows:
        log(f"span {row}")
    after = hashlib.sha256(settings_file.read_bytes()).hexdigest()
    log(f"ship home settings.toml sha256 before {before} after {after}")
    members = card.get("members") if isinstance(card, dict) else None
    families = sorted({str(member["family"]) for member in members or []})
    log(f"panel card: {json.dumps(card)[:2000]}")
    log.check(
        "the panel ran on three provider rows and the spread shows three members",
        report.status == "passed"
        and sorted(row[1] for row in rows)
        == ["claude", "openrouter", "openrouter", "claude"][:0] + sorted(row[1] for row in rows)
        and {(row[1], row[2]) for row in rows}
        >= {("claude", "haiku"), ("openrouter", "deepseek/deepseek-v4.1-flash"),
            ("openrouter", "moonshotai/kimi-k2.5")},
        rows,
    )
    log.check(
        "the spread names three families and marks the judge of a member's family",
        bool(members)
        and len(members) == 3
        and families == ["anthropic", "deepseek", "moonshot"]
        and card.get("judge_same_family_as") == ["macro"],
        {"families": families, "judge_same_family_as": card.get("judge_same_family_as")},
    )
    log.check("the ship home's settings.toml is unchanged", before == after, after)
    return log.verdict()


async def _fake_run(root: Path, folder: str, inputs: Any) -> tuple[str, Any]:
    with EngineService.open(root) as svc:
        current = current_draft(svc, folder)
        svc.drafts.put(
            folder, Bundle.read(PACK / folder), 0 if current is None else current.revision,
            caller=OPERATOR,
        )  # fmt: skip
        report = await svc.tests.run(folder, caller=OPERATOR, inputs=inputs, fake=True)
    return report.run_id, report


def dedupe(log: Log) -> int:
    """Lane 4: the same clipping fed twice. The first run lands it; the second links to it."""
    root = home("dedupe")
    first_run, first = asyncio.run(_fake_run(root, "clippings-into-research", {"fixture": True}))
    first_card = delivered(root, first_run)
    second_run, second = asyncio.run(_fake_run(root, "clippings-into-research", {"fixture": True}))
    second_card = delivered(root, second_run)
    log(f"first run {first_run} {first.status}: {json.dumps(first_card)[:900]}")
    log(f"second run {second_run} {second.status}: {json.dumps(second_card)[:900]}")
    log.check(
        "the first run lands both clippings as new",
        first.status == "passed"
        and (first_card["figures"]["new"], first_card["figures"]["seen"]) == (2, 0),
        first_card.get("figures") if isinstance(first_card, dict) else first_card,
    )
    held = second_card.get("held") or []
    log.check(
        "the same clipping fed twice runs once and the second links to the first",
        second.status == "passed"
        and (second_card["figures"]["new"], second_card["figures"]["seen"]) == (0, 2)
        and all(item["linked_to"] for item in held),
        [item.get("linked_to") for item in held],
    )
    return log.verdict()


def crystallise(log: Log) -> int:
    """Lane 5: the crystallise pattern on the twenty recorded replays."""
    root = home("crystallise")
    run_id, report = asyncio.run(_fake_run(root, "crystallise-a-workflow", {"fixture": True}))
    card = delivered(root, run_id)
    log(f"run {run_id} {report.status}: {json.dumps(card)[:1500]}")
    log.check(
        "the equivalence check passes on twenty replays and the sampling rate is set",
        report.status == "passed"
        and card["equivalent"]
        and card["figures"]["replays"] == 20
        and card["figures"]["agreeing"] == 20
        and card["sampling"] == {"one_in": 10},
        {"figures": card.get("figures"), "sampling": card.get("sampling")},
    )
    log.check(
        "the script labels the batch and sends only what it cannot label back to the agent",
        card["figures"]["batch"] == 24 and card["figures"]["sampled"] == 3
        and (card["figures"]["fallbacks"] > 0)
        and card["agreement"] == 1.0,
        {"figures": card.get("figures"), "agreement": card.get("agreement")},
    )
    return log.verdict()


def digest(log: Log) -> int:
    """Lane 6: the digest twice, on one home, around one item that lands between them."""
    root = home("digest")
    with LibraryFake.open(root) as library:
        library.put_artifact(
            b'{"landed": "first"}', "clipping", {"title": "first"}, run_id="seed",
            principal="run:seed", intent_key="first",
        )  # fmt: skip
    first_run, first = asyncio.run(_fake_run(root, "morning-digest", {"fixture": True}))
    first_card = delivered(root, first_run, "advance")
    with LibraryFake.open(root) as library:
        library.put_artifact(
            b'{"landed": "second"}', "clipping", {"title": "second"}, run_id="seed",
            principal="run:seed", intent_key="second",
        )  # fmt: skip
    second_run, second = asyncio.run(_fake_run(root, "morning-digest", {"fixture": True}))
    second_card = delivered(root, second_run, "advance")
    log(f"first digest {first_run} {first.status}: {json.dumps(first_card)[:900]}")
    log(f"second digest {second_run} {second.status}: {json.dumps(second_card)[:900]}")
    log.check(
        "the first digest reads what landed and leaves the cursor on it",
        first.status == "passed"
        and len(first_card["landed"]) == 1
        and first_card["read_from"] == 0
        and first_card["cursor_to"] == 1,
        {k: first_card.get(k) for k in ("landed", "read_from", "cursor_to")},
    )
    log.check(
        "the second digest shows only what landed since the first",
        second.status == "passed"
        and bool(second_card["landed"])
        and second_card["read_from"] == first_card["cursor_to"]
        and not {
            item["object_id"] for item in second_card["landed"]
        } & {item["object_id"] for item in first_card["landed"]},
        {k: second_card.get(k) for k in ("landed", "read_from", "cursor_to")},
    )
    return log.verdict()


def nest(log: Log) -> int:
    """Lane 7: the revolution loop validates, with a loop over a child that holds its own loop."""
    found = checked(PACK / "revolution-loop")
    codes = [problem.code for problem in found] if isinstance(found, list) else []
    log(f"checked: {codes or 'no problems'}")
    log.check("the revolution loop validates", not isinstance(found, list), codes)
    return log.verdict()


def turns(log: Log) -> int:
    """Lane 8: the perf block's number, read back out of the lane 2 log."""
    path = EVIDENCE / "owner-turns.log"
    log(f"lane 2 log: {path}")
    log(path.read_text("utf-8") if path.exists() else "the lane 2 log does not exist yet")
    log.check("the haiku turn count per template is recorded", path.exists(), str(path))
    return log.verdict()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lane",
        choices=("runs", "panel", "dedupe", "crystallise", "digest", "nest", "turns"),
        default="runs",
    )
    args = parser.parse_args()
    boot()
    if args.lane == "runs":
        return asyncio.run(runs(Log("runs")))
    if args.lane == "panel":
        return asyncio.run(panel(Log("panel")))
    if args.lane == "dedupe":
        return dedupe(Log("dedupe"))
    if args.lane == "crystallise":
        return crystallise(Log("crystallise"))
    if args.lane == "digest":
        return digest(Log("digest"))
    if args.lane == "nest":
        return nest(Log("nest"))
    return turns(Log("turns-read"))


if __name__ == "__main__":
    sys.exit(main())
