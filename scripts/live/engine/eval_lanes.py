"""The copilot eval battery's lanes (EVAL, engine AD-66).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/eval_lanes.py LANE [...] [--parent PATH]`
Each lane writes `D:/QMX-worktrees/qma-ship/build/evidence/eval/<ENGINE_LOG_PREFIX>eval-<lane>.log`
and the script exits 1 if any lane failed. Every engine and control store is a throwaway home
under `build/homes/eval-<lane>`; the lanes that need a plan turn open the ship home's harness only
through `plan_harness`, which takes the lane lock itself, so never wrap this script in a lock.

- `regression` (lane 1): the qmx-engine and qmx-control suites with `-n 2` at `--parent` and here.
  Pass when this checkout fails no test the parent passes.
- `haiku` (lane 2, the perf probe): the template's own test run on its 20 seed tasks, every role
  on `claude/haiku` through the plan login. Pass when the run passes and reports pass^3 for all 20.
  Logs the battery's wall time.
- `compare` (lanes 3 and 6): five tasks on OpenRouter's DeepSeek row as the model under change,
  haiku as the baseline, the judge on OpenRouter's Kimi row. Pass when both pass^3 columns are
  reported, each side ran on its own model, and the judge's family differs from both.
- `card` (lane 4, fake provider): a persona draft's publish card after a battery on the seed
  tasks read from the Library. Pass when it carries the result and the surface digest change.
- `newtask` (lane 5, fake provider): one failing task added with one put, then a rerun. Pass when
  the new task appears in the report, failing.
- `nowait` (lane 7, fake provider): a persona published while a battery runs. Pass when the
  publish returns before the battery ends.
- `library` (lane 8, fake provider): pass when both runs' `workflow-run` summaries land in the
  engine's Library and the battery result in the control Library.
- `secrets` (lane 9): `tools/secret_scan.py`. `processes` (lane 10): no `claude`,
  `qma-cli-launcher` or `qmx_host` process and no lane lock left.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any, Final

from common import LANE_LOCK, SHIP_HOME, Log, plan_harness

os.environ.setdefault("QMA_LIVE_SCRATCH", "D:/QMX-worktrees/qma-ship/build/homes/eval-scratch")

from jsonschema import Draft202012Validator
from llm_lanes import OPENROUTER_ROW, harnessed, relay_usd
from qmx_control.service import (
    EVAL_TASK,
    ControlService,
    LibraryInput,
    draft_subject,
    eval_run_input,
    model_subject,
)
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import ControlSettings, StaticSettings
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.templates import battery
from qmx_engine.templates.install import current_draft

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
REPO: Final = Path(__file__).resolve().parents[3]
HAIKU: Final = "claude/haiku"
DEEPSEEK: Final = "openrouter/deepseek/deepseek-chat"
KIMI: Final = "openrouter/moonshotai/kimi-k2.5"
SHIP_SETTINGS: Final = SHIP_HOME / "settings.toml"
SUITES: Final = ("qmx-engine", "qmx-control")
PYTEST: Final = ("run", "--no-sync", "python", "-m", "pytest", "tests", "-q", "-n", "2", "-rf")
COMPARE_TASKS: Final = (
    "b51-arithmetic-no-tools",
    "quant-basis-points",
    "op-which-asks",
    "b70-tools-in-brief-only",
    "op-hard-truth",
)
ROLE_ORDER_KEYS: Final = frozenset({"roles.test_only", "roles.test_order", "roles.live_order"})
SEEDS: Final[list[dict[str, Any]]] = json.loads(
    (battery.FOLDER / "fixtures" / "tasks.json").read_text("utf-8")
)["tasks"]
REPORT: Final = Draft202012Validator(
    json.loads((battery.FOLDER / "schemas" / "output.json").read_text("utf-8"))
)


class EvalLog(Log):
    """`Log`, writing to the build store's `evidence/eval/` instead of the engine store's."""

    def __init__(self, slug: str) -> None:
        folder = STORE / "evidence" / "eval"
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}eval-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def home(slug: str) -> Path:
    root = STORE / "homes" / f"eval-{slug}"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def ship_hash() -> str:
    return hashlib.sha256(SHIP_SETTINGS.read_bytes()).hexdigest()


def delivered(engine_home: Path, run_id: str) -> Any:
    with Reader.open(engine_home) as reader:
        found = [
            e.data["outputs"]["main"]
            for e in reader.events(run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == "deliver"
        ]
    return found[-1] if found else None


def failures(package: Path) -> tuple[int, set[str], str]:
    done = subprocess.run(
        [str(shutil.which("uv")), *PYTEST],
        cwd=package,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={
            k: v
            for k, v in os.environ.items()
            if not k.startswith(("ANTHROPIC_", "CLAUDE")) and k != "NODE_USE_SYSTEM_CA"
        },
        check=False,
    )
    failed = set(re.findall(r"^FAILED (\S+)", done.stdout, re.MULTILINE))
    tail = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-300:]
    return done.returncode, failed, tail


def regression(log: Log, parent: Path) -> None:
    for suite in SUITES:
        before = failures(parent / "qmx-agents" / "packages" / suite)
        after = failures(REPO / "qmx-agents" / "packages" / suite)
        log(f"{suite} parent: {before[2]}; failed {sorted(before[1])}")
        log(f"{suite} head: {after[2]}; failed {sorted(after[1])}")
        new = sorted(after[1] - before[1])
        log.check(f"{suite}: head fails nothing the parent passes", not new, new or "none new")


@contextlib.asynccontextmanager
async def plan_engine(log: Log, engine_home: Path) -> AsyncIterator[Callable[[], Any]]:
    """The engine on `engine_home` with its model turns through the ship home's plan login, every
    role on haiku for this lane only; the ship home's settings are read, never written."""
    async with plan_harness(log) as found:
        values = ControlSettings(found.control).values()
        settings = StaticSettings(
            {
                key: (HAIKU,) if key.startswith("roles.") and key not in ROLE_ORDER_KEYS else value
                for key, value in values.items()
            }
        )
        adapter = HarnessAdapter(found.harness)
        yield lambda: EngineService.open(engine_home, settings=settings, harness=adapter)


def haiku(log: Log) -> None:
    asyncio.run(haiku_run(log, home("haiku")))


async def haiku_run(log: Log, engine_home: Path) -> None:
    async with plan_engine(log, engine_home) as service:
        started = time.monotonic()
        with service() as svc:
            draft = current_draft(svc, battery.ITEM)
            revision = 0 if draft is None else draft.revision
            svc.drafts.put(battery.ITEM, Bundle.read(battery.FOLDER), revision, caller=OPERATOR)
            report = await svc.tests.run(battery.ITEM, caller=OPERATOR, inputs={"fixture": True})
        seconds = time.monotonic() - started
    with Reader.open(engine_home) as reader:
        spans = [s for s in reader.spans(report.run_id) if s.model]
    found = delivered(engine_home, report.run_id) or {}
    models = sorted({f"{s.profile}/{s.model}" for s in spans})
    log(f"run {report.run_id} {report.status} {report.reason or ''}; model spans on {models}")
    for task in found.get("tasks", []):
        log(f"  {task['id']}: tries {task['tries']} pass^3 {task['pass3']} {task['why']}")
    log.check("the template's test run passes on haiku", report.status == "passed", report.status)
    errors = [e.message for e in REPORT.iter_errors(found)][:3]
    log.check(
        "the report validates and names pass^3 for all 20 seed tasks",
        not errors and found.get("total") == 20,
        {"errors": errors, "passed": found.get("passed"), "total": found.get("total")},
    )
    log.check("every model span ran on claude/haiku", models == [HAIKU], models)
    log(f"perf: battery wall time for 20 tasks on haiku: {seconds:.1f} s, {len(spans)} model spans")


class Routed:
    """Two harness adapters as one port: a chat goes to the adapter holding its profile, and every
    later call on it follows the chat."""

    def __init__(self, plan: HarnessAdapter, other: HarnessAdapter) -> None:
        self.plan, self.other = plan, other
        self.chats: dict[str, HarnessAdapter] = {}

    def profiles(self) -> frozenset[str]:
        return self.plan.profiles() | self.other.profiles()

    async def plan_use(self) -> Any:
        return await self.plan.plan_use()

    async def start_chat(self, *, profile: str, **options: Any) -> str:
        port = self.plan if profile in self.plan.profiles() else self.other
        chat = await port.start_chat(profile=profile, **options)
        self.chats[chat] = port
        return chat

    def __getattr__(self, name: str) -> Any:
        def call(chat: str, *args: Any, **kwargs: Any) -> Any:
            return getattr(self.chats[chat], name)(chat, *args, **kwargs)

        return call


def compare(log: Log) -> None:
    judge_log = EvalLog("judge")
    asyncio.run(compare_run(log, judge_log, home("compare")))
    judge_log.verdict()


async def compare_run(log: Log, judge_log: Log, root: Path) -> None:
    keyed = root / "openrouter-home"
    keyed.mkdir()
    ControlService(keyed).settings_put("providers", {"openrouter": OPENROUTER_ROW})
    tasks = [t for t in SEEDS if t["id"] in COMPARE_TASKS]
    settings = StaticSettings({**DEFAULTS, "roles.test_only": (DEEPSEEK, KIMI)})
    subject = model_subject(HAIKU, DEEPSEEK)
    async with plan_harness(log) as plan, harnessed(keyed) as other:
        port = Routed(HarnessAdapter(plan.harness), HarnessAdapter(other.harness))
        log(f"profiles: {sorted(port.profiles())}")
        with EngineService.open(root / "engine", settings=settings, harness=port) as svc:
            result = await battery.run(
                svc,
                tasks,
                battery.Side(DEEPSEEK),
                battery.Side(HAIKU),
                judges=(HAIKU, KIMI),
                subject=subject,
                mode="test",
            )
    control = ControlService(root / "control")
    control.library_save(eval_run_input(result))
    control.settings_put("agents", {"copilot_model": HAIKU})
    card = control.settings_model_card(DEEPSEEK)
    log(f"wall {result['wall_s']} s; OpenRouter spend upper bound ${relay_usd(keyed):.4f}")
    log(f"{'task':28} {'DeepSeek pass^3':>16} {'haiku pass^3':>13}")
    for row in result["per_task"]:
        log(f"{row['id']:28} {row['candidate']!s:>16} {row['baseline']!s:>13}")
    candidate, baseline = result["candidate"], result["baseline"]
    for name, side in (("candidate", candidate), ("baseline", baseline)):
        log(
            f"{name}: run {side['run_id']} {side['status']} ran on {side['ran_on']}"
            f" judged on {side['judged_on']} passed {side['passed']}/{side['total']}"
        )
    both = all(
        isinstance(r[k], bool) for r in result["per_task"] for k in ("candidate", "baseline")
    )
    log.check("both pass^3 columns are reported for all 5 tasks", both and len(tasks) == 5, both)
    log.check(
        "the candidate ran on DeepSeek and the baseline on haiku",
        (candidate["ran_on"], baseline["ran_on"]) == ([DEEPSEEK], [HAIKU]),
        (candidate["ran_on"], baseline["ran_on"]),
    )
    log.check(
        "the model card carries both columns",
        card["battery"]["per_task"] == result["per_task"],
        card["battery"]["status"],
    )
    judged = sorted({*candidate["judged_on"], *baseline["judged_on"]})
    families = {battery.family(r) for r in judged}
    graded = {battery.family(DEEPSEEK), battery.family(HAIKU)}
    judge_log(f"judge picked {result['judge']}; judge spans on {judged}; graded families {graded}")
    judge_log.check(
        "the judge's family differs from every graded model's",
        bool(judged) and not families & graded,
        {"judge": sorted(families), "graded": sorted(graded)},
    )


def seeded(control: ControlService) -> list[Any]:
    for task in SEEDS:
        control.library_save(
            LibraryInput(title=task["id"], kind="artifact", content=task, tags=[EVAL_TASK])
        )
    return control.library_eval_tasks()


async def fake_battery(
    engine_home: Path, tasks: list[Any], candidate: battery.Side, subject: str
) -> dict[str, Any]:
    with EngineService.open(engine_home) as svc:
        return await battery.run(
            svc,
            tasks,
            candidate,
            battery.Side(HAIKU, "Be brief."),
            judges=(HAIKU, KIMI),
            subject=subject,
            mode="test",
            fake=True,
        )


def personas(control: ControlService) -> tuple[Any, Any]:
    published = control.library_save(
        LibraryInput(title="copilot persona", kind="persona", content="Be brief.")
    )
    draft = control.library_save(
        LibraryInput(
            title="copilot persona",
            kind="persona",
            content="Be brief and blunt.",
            previous_id=str(published["id"]),
        )
    )
    return published, draft


def card(log: Log) -> None:
    root = home("card")
    control = ControlService(root / "control")
    tasks = seeded(control)
    _, draft = personas(control)
    subject = draft_subject(str(draft["id"]))
    before = control.library_publish_card(str(draft["id"]))
    draft_side = battery.Side(HAIKU, "Be brief and blunt.")
    result = asyncio.run(fake_battery(root / "engine", tasks, draft_side, subject))
    control.library_save(eval_run_input(result))
    found: Any = control.library_publish_card(str(draft["id"]))
    log(f"before the battery: {before['battery']}")
    log(f"card: {json.dumps(found)[:1500]}")
    log.check(
        "the card read 'not run' before the battery",
        before["battery"]["status"] == "not run",
        before["battery"]["status"],
    )
    log.check(
        "the card carries the battery result for the 20 tasks read from the Library",
        found["battery"]["status"] == "ran"
        and len(found["battery"]["per_task"]) == len(tasks) == 20,
        len(found["battery"]["per_task"]),
    )
    log.check(
        "the card carries the surface digest change",
        found["surface_digest"]["changed"],
        found["surface_digest"],
    )


def newtask(log: Log) -> None:
    root = home("newtask")
    control = ControlService(root / "control")
    seeded(control)
    new = {
        "id": "chat-asked-for-a-cap",
        "prompt": "Put a 5 dollar cap on background chats.",
        "grade": {"by": "code", "checks": [{"kind": "contains", "all": ["no usage caps"]}]},
        "source": "a failure seen in a chat",
    }
    control.library_save(
        LibraryInput(title=new["id"], kind="artifact", content=new, tags=[EVAL_TASK])
    )
    tasks = control.library_eval_tasks()
    result = asyncio.run(fake_battery(root / "engine", tasks, battery.Side(HAIKU), "lane-5"))
    row = next((r for r in result["per_task"] if r["id"] == new["id"]), None)
    log(f"tasks read from the Library: {len(tasks)}; new task row: {row}")
    log.check(
        "the new task appears in the report, failing",
        row is not None and row["candidate"] is False,
        row,
    )


def nowait(log: Log) -> None:
    asyncio.run(nowait_run(log, home("nowait")))


async def nowait_run(log: Log, root: Path) -> None:
    control = ControlService(root / "control")
    tasks = seeded(control)
    _, draft = personas(control)
    started = time.monotonic()
    running = asyncio.create_task(
        fake_battery(root / "engine", tasks, battery.Side(HAIKU), draft_subject(str(draft["id"])))
    )
    await asyncio.sleep(0.5)
    published = await asyncio.to_thread(
        control.library_save,
        LibraryInput(
            title="copilot persona",
            kind="persona",
            content="Be blunt.",
            previous_id=str(draft["id"]),
        ),
    )
    published_at = time.monotonic() - started
    was_running = not running.done()
    await running
    ended_at = time.monotonic() - started
    log(f"published {published['id']} at {published_at:.2f} s; battery ended at {ended_at:.2f} s")
    log.check("publishing returned while the battery still ran", was_running, was_running)


def library(log: Log) -> None:
    root = home("library")
    control = ControlService(root / "control")
    tasks = seeded(control)
    result = asyncio.run(fake_battery(root / "engine", tasks, battery.Side(HAIKU), "lane-8"))
    saved = control.library_save(eval_run_input(result))
    with EngineService.open(root / "engine") as svc:
        summaries = {
            side: svc.ctx.library.objects(result[side]["run_id"], "workflow-run")
            for side in ("candidate", "baseline")
        }
    for side, found in summaries.items():
        fields = found[-1].fields if found else {}
        log(
            f"{side} {result[side]['run_id']}: {len(found)} workflow-run summaries; "
            f"status {fields.get('status')} mode {fields.get('mode')}"
        )
    log.check(
        "both runs' summaries land in the engine's Library",
        all(summaries.values()),
        {k: len(v) for k, v in summaries.items()},
    )
    read = control.library_get(str(saved["id"]))
    log.check(
        "the battery result lands in the control Library", read["kind"] == "eval-run", read["id"]
    )


def secrets(log: Log) -> None:
    done = subprocess.run(
        [sys.executable, "tools/secret_scan.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    log(done.stdout.strip()[-1500:] or done.stderr.strip()[-1500:])
    log.check("tools/secret_scan.py is clean", done.returncode == 0, done.returncode)


def processes(log: Log) -> None:
    """Only processes whose command line names the build store or the ship home are a lane's:
    the operator's own Claude sessions run beside the lanes."""
    query = (
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match"
        " '^(claude|qma-cli-launcher|qmx_host)' } | ForEach-Object"
        ' { "$($_.ProcessId)`t$($_.Name)`t$($_.CommandLine)" }'
    )
    done = subprocess.run(
        [str(shutil.which("pwsh")), "-NoProfile", "-Command", query],
        capture_output=True,
        text=True,
        check=False,
    )
    rows = [line.split("\t") for line in done.stdout.splitlines() if line.strip()]
    log(f"claude, qma-cli-launcher and qmx_host processes on the PC: {len(rows)}")
    ours = [r[:2] for r in rows if "qma-ship" in (r[2] if len(r) > 2 else "").replace("\\", "/")]
    log.check(
        "no claude, qma-cli-launcher or qmx_host process of a lane is left",
        not ours,
        ours or "none",
    )
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK.exists())


LANES: Final[dict[str, Callable[..., None]]] = {
    "regression": regression,
    "haiku": haiku,
    "compare": compare,
    "card": card,
    "newtask": newtask,
    "nowait": nowait,
    "library": library,
    "secrets": secrets,
    "processes": processes,
}
SHIP_LANES: Final = frozenset({"haiku", "compare"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("lanes", nargs="+", choices=list(LANES))
    parser.add_argument("--parent", type=Path, help="the parent checkout, for `regression`")
    args = parser.parse_args()
    verdict = 0
    for name in args.lanes:
        log = EvalLog(name)
        guarded = ship_hash() if name in SHIP_LANES else None
        if guarded:
            log(f"ship settings.toml sha256 before: {guarded}")
        if name == "regression":
            if args.parent is None:
                parser.error("regression needs --parent")
            regression(log, args.parent)
        else:
            LANES[name](log)
        if guarded:
            after = ship_hash()
            log.check("the ship home's settings.toml hashes the same", after == guarded, after)
        verdict |= log.verdict()
    return verdict


if __name__ == "__main__":
    sys.exit(main())
