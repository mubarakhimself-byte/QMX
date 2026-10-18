"""CAPE lane 2 (E41): the stuck detector on the real runner, with no model and no ship home.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e41_stuck.py`
Writes `D:/QMX-worktrees/qma-ship/build/evidence/cape/<ENGINE_LOG_PREFIX>cape-e41.log`.

Each case is one run of a one-agent (or one-script) workflow on a scripted harness port, the fake
provider: its turns show tool calls the way the session blocks do, and nothing reaches a model.
The windows are the defaults scaled 1:100 (idle 3 s for 300 s, grace 1.2 s for 120 s), so a case
takes seconds; the scale is the same for every case and changes no rule.

- loop: the same Read with the same result, again and again. Pass when it ends `stalled(loop)`
  with its summary as the output and the run parks.
- flailing fixer: a new edit each turn and the same two failing tests. Pass when the attempt ends
  `stalled(no_convergence)` and the ladder walks on (account, model, doctor, park).
- converging fixer (5, then 3, then 1 failed), a pager over new rows, a first-token wait of 1.33
  idle windows (400 s at full scale) and a CPU-busy script past its idle window: each passes.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Final

from agent_lanes import edge, node
from common import Log

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import Activity, PlanUse, ToolStep, Turn
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS

BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
PR: Final = "cape"
SCALE: Final = 100
SETTINGS: Final = {
    **DEFAULTS,
    "timeout.agent.idle": 3,
    "timeout.script.idle": 3,
    "timeout.grace": 1.2,
    "scheduler.tick": 0.1,
    "retry.backoff": (0, 0, 0),
}
CARD: Final = '{"seen": 2}'
SUMMARY: Final = "I kept doing the same thing and it did not change."
OPEN: Final = PlanUse(0.1, "2026-10-18T12:00:00+00:00", None, None)
BRIEF: Final = "Count the items you are given."
SCHEMA: Final = {
    "type": "object",
    "required": ["seen"],
    "properties": {"seen": {"type": "integer"}},
}

type Answer = Callable[["Port", str], Awaitable[Turn]] | str


class BuildLog(Log):
    """The engine lanes' log, written to the build program's store instead of the engine's."""

    def __init__(self, slug: str) -> None:
        folder = BUILD / "evidence" / PR
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def build_home(slug: str) -> Path:
    """A fresh folder under the build store's `homes/cape-<slug>`, for a lane that needs no model."""
    root = BUILD / "homes" / f"{PR}-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


class Port:
    """A harness port with no model: each turn is answered by the next answer in the list."""

    def __init__(self, *answers: Answer) -> None:
        self.answers = list(answers)
        self.chats = 0
        self.sent: list[tuple[str, str]] = []
        self.interrupted: list[str] = []
        self.activities: dict[str, Activity] = {}
        self.halts: dict[str, asyncio.Event] = {}

    def profiles(self) -> frozenset[str]:
        return frozenset({"claude", "openrouter"})

    async def plan_use(self) -> PlanUse:
        return OPEN

    async def start_chat(self, **_: Any) -> str:
        self.chats += 1
        return f"chat-{self.chats}"

    async def send(self, chat: str, text: str) -> None:
        self.sent.append((chat, text))

    async def wait_turn(
        self, chat: str, *, timeout: float | None = None, idle: float | None = None
    ) -> Turn:
        found = self.answers.pop(0)
        if isinstance(found, str):
            return Turn(found, {"in": 10, "out": 5})
        return await found(self, chat)

    async def interrupt(self, chat: str) -> None:
        self.interrupted.append(chat)
        self.halted(chat).set()

    def halted(self, chat: str) -> asyncio.Event:
        return self.halts.setdefault(chat, asyncio.Event())

    def context(self, chat: str) -> int | None:
        return None

    def activity(self, chat: str) -> Activity:
        return self.activities.get(chat, Activity(0, running=True))


def pytest_result(failed: list[str], seconds: float) -> str:
    lines = [f"FAILED tests/test_fix.py::test_{name} - assert 1 == 2" for name in failed]
    return "\n".join([*lines, f"== {len(failed)} failed, 9 passed in {seconds:.2f}s =="])


def steps_of(turns: list[list[tuple[str, Any, str, bool]]]) -> tuple[ToolStep, ...]:
    flat = [step for turn in turns for step in turn]
    return tuple(
        ToolStep(f"t{n}", name, arguments, result, error)
        for n, (name, arguments, result, error) in enumerate(flat)
    )


def playing(
    turns: list[list[tuple[str, Any, str, bool]]], *, answer: str | None
) -> Callable[[Port, str], Awaitable[Turn]]:
    """A turn that shows `turns` one by one, every 0.3 s, then answers, or, with no answer,
    waits to be interrupted."""

    async def play(port: Port, chat: str) -> Turn:
        for count in range(1, len(turns) + 1):
            port.activities[chat] = Activity(count, steps_of(turns[:count]), running=True)
            halted = port.halted(chat)
            try:
                await asyncio.wait_for(halted.wait(), 0.3)
                return Turn(None)
            except TimeoutError:
                continue
        if answer is not None:
            return Turn(answer, {"in": 10, "out": 5})
        await port.halted(chat).wait()
        return Turn(None)

    return play


def edit(n: int) -> tuple[str, Any, str, bool]:
    return ("Edit", {"file_path": "src/fix.py", "new_string": f"attempt {n}"}, "ok", False)


def tests(failed: list[str], n: int) -> tuple[str, Any, str, bool]:
    return ("Bash", {"command": "uv run pytest -q"}, pytest_result(failed, 0.4 + n / 10), True)


def agent_folder(home: Path, slug: str) -> Path:
    root = home / f"wf-{slug}"
    (root / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "schemas").mkdir(exist_ok=True)
    (root / "prompts" / "brief.md").write_text(BRIEF, "utf-8")
    (root / "schemas" / "out.json").write_text(json.dumps(SCHEMA), "utf-8")
    document = {
        "schema": "qmx.workflow/1",
        "id": slug,
        "name": slug,
        "nodes": [
            node("start", "trigger"),
            node(
                "fix",
                "agent",
                "reader",
                brief_ref="prompts/brief.md",
                output_schema_ref="schemas/out.json",
                tools=["Read", "Edit", "Bash"],
            ),
        ],
        "connections": {"start": {"main": [[edge("fix")]]}},
    }
    (root / "definition.json").write_text(json.dumps(document, indent=2), "utf-8")
    return root


def script_folder(home: Path, seconds: float) -> Path:
    root = home / "wf-busy"
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    spin = f"import json, time\nend = time.time() + {seconds}\nwhile time.time() < end:\n    pass\n"
    (root / "scripts" / "busy.py").write_text(spin + "print(json.dumps(1))\n", "utf-8")
    document = {
        "schema": "qmx.workflow/1",
        "id": "busy",
        "name": "busy",
        "nodes": [node("start", "trigger"), node("busy", "script", script="scripts/busy.py")],
        "connections": {"start": {"main": [[edge("busy")]]}},
    }
    (root / "definition.json").write_text(json.dumps(document, indent=2), "utf-8")
    return root


async def drive(root: Path, port: Port | None) -> tuple[Outcome, list[Event]]:
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: {root} does not validate: {found}")
    home = root.parent / f"engine-{root.name}"
    with Ledger.open(home) as ledger:
        engine = Engine(home, ledger, settings=SETTINGS, harness=port)
        outcome = await engine.start(root, found[1], mode="test", inputs=[1, 2])
    with Reader.open(home) as reader:
        return outcome, reader.events(outcome.run_id)


def failures(events: list[Event]) -> list[tuple[Any, Any]]:
    return [(e.data.get("code"), e.data.get("stalled")) for e in events if e.kind == "node_failed"]


def steps(events: list[Event]) -> list[Any]:
    return [e.data.get("step") for e in events if e.kind == "ladder_step"]


async def loop(log: Log, home: Path) -> None:
    same = ("Read", {"file_path": "notes.txt"}, "the same notes", False)
    port = Port(playing([[same]] * 8, answer=None), SUMMARY)
    outcome, events = await drive(agent_folder(home, "loop"), port)
    failed = [e.data for e in events if e.kind == "node_failed"]
    log(f"loop: {outcome.status} {outcome.reason}; failures {failures(events)}")
    log.check(
        "the looping agent ends stalled(loop) with its summary as output and the run parks",
        outcome.status == "failed"
        and [(f.get("code"), f.get("stalled"), f.get("output")) for f in failed]
        == [("stalled", "loop", SUMMARY)]
        and steps(events) == ["park"],
        {"failures": failures(events), "steps": steps(events)},
    )


async def flailing(log: Log, home: Path) -> None:
    turns = [[edit(n), tests(["a", "b"], n)] for n in range(8)]
    port = Port(*[a for _ in range(3) for a in (playing(turns, answer=None), SUMMARY)])
    outcome, events = await drive(agent_folder(home, "flailing"), port)
    log(f"flailing: {outcome.status} {outcome.reason}; failures {failures(events)}")
    log(f"flailing ladder: {steps(events)}")
    log.check(
        "the flailing fixer ends stalled(no_convergence) and walks the ladder",
        failures(events)[:1] == [("stalled", "no_convergence")]
        and steps(events)[:1] == ["account"]
        and "model" in steps(events)
        and steps(events)[-1] == "park",
        {"failures": failures(events), "steps": steps(events)},
    )


async def passes(log: Log, home: Path, name: str, root: Path, port: Port | None) -> None:
    outcome, events = await drive(root, port)
    warned = [e.data["line"] for e in events if e.kind == "log" and e.data.get("level") == "warn"]
    log(f"{name}: {outcome.status} {outcome.reason or ''}; failures {failures(events)}")
    log.check(
        f"the {name} ends passed with no stall",
        outcome.status == "passed" and failures(events) == [] and warned == [],
        {"status": outcome.status, "failures": failures(events), "warnings": warned},
    )


async def first_token(port: Port, chat: str) -> Turn:
    port.activities[chat] = Activity(0, running=True)
    await asyncio.sleep(4.0)
    return Turn(CARD, {"in": 10, "out": 5})


async def main() -> int:
    log = BuildLog("cape-e41")
    home = build_home("e41")
    log(f"scale 1:{SCALE}: idle 3 s, grace 1.2 s, tick 0.1 s; home {home}")
    await loop(log, home)
    await flailing(log, home)
    converging = [
        [edit(0), tests(["a", "b", "c", "d", "e"], 0)],
        [edit(1), tests(["a", "b", "c"], 1)],
        [edit(2), tests(["a"], 2)],
        [edit(3), ("Bash", {"command": "uv run pytest -q"}, "== 14 passed in 0.5s ==", False)],
    ]
    pages = [
        [("Bash", {"command": f"sql page {n}"}, f"rows {n * 50} to {n * 50 + 49}", False)]
        for n in range(12)
    ]
    cases: list[tuple[str, Path, Port | None]] = [
        (
            "converging fixer",
            agent_folder(home, "converging"),
            Port(playing(converging, answer=CARD)),
        ),
        ("pager", agent_folder(home, "pager"), Port(playing(pages, answer=CARD))),
        ("first-token wait of 1.33 idle windows", agent_folder(home, "prefill"), Port(first_token)),
        ("CPU-busy script past its idle window", script_folder(home, 6.0), None),
    ]
    for name, root, port in cases:
        await passes(log, home, name, root, port)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
