"""B17's live lanes: probe P-PERM rerun on the real engine launch path, and two agent-step runs.

Every chat goes through `HarnessAdapter.start_chat`, the call an `agent` node makes, so the CLI is
launched by the harness with the engine policy, the guard and the Surface's built-ins. Model turns
run on `haiku` through the ship home's plan login under `D:/QMX-worktrees/.engine-lane-lock`
(`scripts/live/engine/common.py` `plan_harness`). No API key is read and nothing is spent.

- `pperm` (lane 2): chat A declares `Write` and `Edit` in its overlay. A1 writes under it, A2
  writes outside it, A3 asks for `echo a3-undeclared` and A3W for a Bash write into the overlay.
  Chat B declares `Bash` too, and B1 writes into its overlay with Bash. PASS when A offers no shell,
  A1 and B1 write, A2 is refused with the policy's reason, and A3 and A3W cannot run.
- `outputs` (lane 3): one agent step declares `result.md` as its only output and is asked to
  write `result.md` and `extra.md`. PASS when only `result.md` commits. Logs the step's seconds.
- `overlay` (lane 4): one agent step is asked to write outside its overlay and to report what
  happened. PASS when the file is absent, the tool call carries the refusal and the step says so.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python packages/qmx-engine/tests/live/p_perm_rerun.py pperm`
Writes `D:/QMX-worktrees/unit-ship/evidence/b17/<B17_LOG_PREFIX>b17-<lane>.log`.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter, Turn
from qmx_engine.runner import Engine
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.zones import RunZone

REPO: Final = Path(__file__).resolve().parents[5]
LIVE_ENGINE: Final = REPO / "scripts" / "live" / "engine"
STORE: Final = Path("D:/QMX-worktrees/unit-ship")
EVIDENCE: Final = STORE / "evidence" / "b17"
HOMES: Final = STORE / "homes"
SHELLS: Final = ("Bash", "PowerShell")
HAIKU: Final = {**DEFAULTS, "roles.reader": ("claude/haiku",)}
TAIL: Final = " Make exactly one tool call. If it is refused, do not retry; reply with the refusal."
OUTSIDE: Final = "is refused: this step writes only under its attempt folder"


def live_common() -> Any:
    """`scripts/live/engine/common.py`, which imports its siblings as top-level modules."""
    sys.path.insert(0, str(LIVE_ENGINE))
    spec = importlib.util.spec_from_file_location("common", LIVE_ENGINE / "common.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"BLOCKED: cannot load {LIVE_ENGINE / 'common.py'}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["common"] = module
    spec.loader.exec_module(module)
    return module


class Log:
    def __init__(self, lane: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        prefix = os.environ.get("B17_LOG_PREFIX", "")
        self.path = EVIDENCE / f"{prefix}b17-{lane}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


def fresh(slug: str) -> Path:
    root = HOMES / f"b17-{slug}"
    if not root.as_posix().startswith("D:/"):
        raise SystemExit(f"BLOCKED: {root} is not on D:")
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


async def ask(adapter: HarnessAdapter, chat: str, say: Log, step: str, prompt: str) -> Turn:
    say(f"{step}: {prompt}")
    await adapter.send(chat, prompt)
    turn = await adapter.wait_turn(chat, timeout=240.0)
    say(f"  tools {[(c.name, c.error) for c in turn.tools]} text {turn.text!r}")
    return turn


def ran(turn: Turn, tool: str) -> bool:
    return any(c.name == tool and c.error is None for c in turn.tools)


async def pperm(say: Log, opened: Any) -> None:
    adapter = HarnessAdapter(opened.harness)
    root_a, root_b = fresh("pperm-a"), fresh("pperm-b")
    overlay_a, overlay_b = root_a / "attempt-1", root_b / "attempt-1"
    exact = "Use the Bash tool to run exactly this command, character for character: "
    write = "Use the Write tool to create "
    chat_a = await adapter.start_chat(
        title="b17:pperm:a",
        profile="claude",
        model="haiku",
        effort=None,
        workspace=overlay_a,
        tools=("Write", "Edit"),
    )
    a1 = await ask(
        adapter, chat_a, say, "A1", f"{write}{overlay_a.as_posix()}/result.txt containing ok.{TAIL}"
    )
    surface = opened.harness.surface(chat_a)
    builtins = tuple(surface.builtins) if surface is not None else ()
    say(f"[a] offered built-ins {builtins}")
    a2 = await ask(
        adapter,
        chat_a,
        say,
        "A2",
        f"{write}{root_a.as_posix()}/outside-write.txt containing x.{TAIL}",
    )
    a3 = await ask(adapter, chat_a, say, "A3", f"{exact}echo a3-undeclared{TAIL}")
    target = f"{overlay_a.as_posix()}/a3.txt"
    a3w = await ask(adapter, chat_a, say, "A3W", f'{exact}echo a3 > "{target}"{TAIL}')
    chat_b = await adapter.start_chat(
        title="b17:pperm:b",
        profile="claude",
        model="haiku",
        effort=None,
        workspace=overlay_b,
        tools=("Bash", "Write", "Edit"),
    )
    b1 = await ask(
        adapter, chat_b, say, "B1", f'{exact}echo b1 > "{overlay_b.as_posix()}/b1.txt"{TAIL}'
    )
    say.check(
        "chat A, declaring Write and Edit, is offered no Bash and no PowerShell",
        bool(builtins) and not set(SHELLS) & set(builtins),
        builtins,
    )
    say.check("A1 a write under the overlay runs", (overlay_a / "result.txt").is_file(), a1.tools)
    refusal = next((c.error for c in a2.tools if c.name == "Write"), None)
    say.check(
        "A2 a write outside the overlay is refused with the policy's reason",
        not (root_a / "outside-write.txt").exists() and OUTSIDE in str(refusal),
        refusal,
    )
    say.check(
        "A3 and A3W cannot run: no shell call ran and a3.txt is absent",
        not any(ran(t, s) for t in (a3, a3w) for s in SHELLS)
        and not (overlay_a / "a3.txt").exists(),
        {"A3": a3.tools, "A3W": a3w.tools},
    )
    say.check("B1 a declared Bash runs", (overlay_b / "b1.txt").is_file(), b1.tools)


def write_flow(root: Path, brief: str, outputs: list[str]) -> Path:
    schema = {
        "type": "object",
        "required": ["report"],
        "properties": {"report": {"type": "string"}},
    }
    step = {
        "id": "write",
        "name": "write",
        "type": "agent",
        "typeVersion": 1,
        "role": "reader",
        "parameters": {
            "brief_ref": "prompts/brief.md",
            "output_schema_ref": "schemas/out.json",
            "tools": ["Write", "Edit"],
        },
        "outputs": {"files": [{"path": path} for path in outputs]},
    }
    document = {
        "schema": "qmx.workflow/1",
        "id": "b17",
        "name": "b17",
        "nodes": [
            {
                "id": "start",
                "name": "start",
                "type": "trigger",
                "typeVersion": 1,
                "parameters": {"kinds": ["manual"]},
            },
            step,
        ],
        "connections": {"start": {"main": [[{"node": "write", "port": "in", "map": "one"}]]}},
    }
    (root / "prompts").mkdir(parents=True)
    (root / "schemas").mkdir()
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    (root / "prompts" / "brief.md").write_text(brief, encoding="utf-8")
    (root / "schemas" / "out.json").write_text(json.dumps(schema), encoding="utf-8")
    return root


async def run_step(say: Log, opened: Any, slug: str, brief: str) -> tuple[Any, Path]:
    root = fresh(slug)
    flow = write_flow(root / "wf", brief, ["result.md"])
    found = checked(flow)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: the lane's workflow does not validate: {found}")
    engine_home = root / "engine"
    started = time.perf_counter()
    with Ledger.open(engine_home) as ledger:
        engine = Engine(engine_home, ledger, settings=HAIKU, harness=HarnessAdapter(opened.harness))
        outcome = await engine.start(flow, found[1], mode="live", inputs=["go"])
    say(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}")
    say(f"seconds for the run with one agent step: {time.perf_counter() - started:.1f}")
    return outcome, engine_home


def events_and_spans(engine_home: Path, run_id: str) -> tuple[list[Any], list[Any]]:
    with Reader.open(engine_home) as reader:
        return reader.events(run_id), reader.spans(run_id)


def seconds(span: Any) -> float | None:
    if span.ended_at is None:
        return None
    return (
        datetime.fromisoformat(span.ended_at) - datetime.fromisoformat(span.started_at)
    ).total_seconds()


async def outputs(say: Log, opened: Any) -> None:
    brief = (
        "In your working folder, use the Write tool twice: create result.md containing the word "
        "answer, then create extra.md containing the word extra. Then reply with the JSON "
        'document {"report": "<what you wrote>"} only.'
    )
    outcome, engine_home = await run_step(say, opened, "outputs", brief)
    events, spans = events_and_spans(engine_home, outcome.run_id)
    work = RunZone.of(engine_home, outcome.run_id).work
    files = sorted(p.name for p in work.iterdir() if p.is_file()) if work.is_dir() else []
    committed = [e.data.get("paths") for e in events if e.kind == "zone_committed"]
    tools = [(s.name, s.error) for s in spans if s.kind == "tool"]
    step = next((s for s in spans if s.kind == "node" and s.node_id == "write"), None)
    say(f"tool spans {tools}")
    say(f"perf: seconds for one agent step that writes: {None if step is None else seconds(step)}")
    say.check("the run passed", outcome.status == "passed", outcome.status)
    say.check("the agent wrote both files", sum(n == "Write" for n, _ in tools) >= 2, tools)
    say.check(
        "only the declared result.md committed",
        files == ["result.md"] and committed == [["result.md"]],
        {"work": files, "zone_committed": committed},
    )


async def overlay(say: Log, opened: Any) -> None:
    outside = HOMES / "b17-overlay" / "outside.md"
    brief = (
        f"Use the Write tool once to create {outside.as_posix()} containing the word x. Do not "
        "retry. Then reply with the JSON document "
        '{"report": "<refused or written, and the reason you were given>"} only.'
    )
    outcome, engine_home = await run_step(say, opened, "overlay", brief)
    events, spans = events_and_spans(engine_home, outcome.run_id)
    tools = [(s.name, s.error) for s in spans if s.kind == "tool"]
    finished = [
        e.data for e in events if e.kind == "node_finished" and e.data["node_id"] == "write"
    ]
    report = json.dumps(finished[0].get("outputs")) if finished else ""
    say(f"tool spans {tools}; step output {report}")
    say.check("the outside file is absent", not outside.exists(), outside.as_posix())
    say.check(
        "the Write call carries the refusal",
        any(n == "Write" and OUTSIDE in str(e) for n, e in tools),
        tools,
    )
    say.check("the step reports the refusal", "refus" in report.lower(), report)


LANES: Final = {"pperm": pperm, "outputs": outputs, "overlay": overlay}


async def main(lane: str) -> int:
    common = live_common()
    say = Log(lane)
    common.boot()
    async with common.plan_harness(say) as opened:
        await LANES[lane](say, opened)
    return say.verdict()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in LANES:
        raise SystemExit(f"usage: p_perm_rerun.py {'|'.join(LANES)}")
    sys.exit(asyncio.run(main(sys.argv[1])))
