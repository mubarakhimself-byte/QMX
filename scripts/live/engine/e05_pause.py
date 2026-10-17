"""EP11 lane 3 (E5), EP12 lane 1: a used-up plan window pauses the run, and the scheduler's
ticker resumes it alone after the reset.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e05_pause.py`
Writes `evidence/ep11/<ENGINE_LOG_PREFIX>ep11-e05.log`, or the log `main` is given. No plan
turn and no provider spend: a throwaway home, the fake model on a key row. A rejected five-hour
reading that resets in `RESET_IN_S` seconds is fed to the harness's plan watch as a CLI
`rate_limit_event`, the way EP0's `p_limits` does. The workflow runs an `llm` node on
`claude/haiku` beside a slow script, and a second `llm` node after the script. At the reset the
lane feeds a fresh 10% reading, which is what the CLI reports once a window opens again. Since
EP12 the run returns `waiting` at the pause and the ticker (`Scheduler.serve`, ticking every
second) wakes it.

The engine's admission reads the real `Harness.usage()`. Only the chat itself is routed: the plan
profile has no login on a throwaway home, so `Routed` starts each chat on the fake key row, and the
span still names the plan candidate the engine resolved.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from agent_lanes import PR, edge, node, read, workflow
from common import Log, boot, live, opened, throwaway_home
from qma.harness import ChatHooks
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter, HarnessPort
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.runner import Outcome
from qmx_engine.service.api import EngineService
from qmx_engine.settings import DEFAULTS, Setting
from qmx_engine.triggers.ticker import Scheduler

RESET_IN_S = 15
SLACK_S = 2
ANSWER = '{"country": "France", "capital": "Paris"}'
SCHEMA = {
    "type": "object",
    "required": ["country", "capital"],
    "properties": {"country": {"type": "string"}, "capital": {"type": "string"}},
}
SLOW = "import json, time\ntime.sleep(3)\nprint(json.dumps('scripted'))\n"


def fact(info: dict[str, Any]) -> Any:
    """EP0 `p_limits.fact`: a `rate_limit_event` parsed by the SDK and projected by the harness."""
    from claude_agent_sdk._internal.message_parser import parse_message  # noqa: PLC0415
    from qma.harness.project import project  # noqa: PLC0415

    message = parse_message(
        {"type": "rate_limit_event", "rate_limit_info": info, "uuid": "u", "session_id": "s"}
    )
    (found,) = project(message)
    return found


class Routed(HarnessAdapter):
    async def start_chat(
        self,
        *,
        title: str,
        profile: str,
        model: str,
        effort: str | None,
        workspace: Path,
        compact_at: float | None = None,
        hooks: ChatHooks | None = None,
    ) -> str:
        return await super().start_chat(
            title=title,
            profile="fake",
            model="fake-model",
            effort=None,
            workspace=workspace,
            compact_at=compact_at,
            hooks=hooks,
        )


async def woken(
    engine_home: Path, root: Path, port: HarnessPort, settings: dict[str, Setting]
) -> tuple[Outcome, int]:
    """Start the run, then serve the ticker until the run finishes; the start's outcome and how
    many wakes the ticker made."""
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: {root} does not validate: {found}")
    with EngineService.open(engine_home, settings=StaticSettings(settings), harness=port) as svc:
        first = await svc.ctx.engine.start(root, found[1], mode="live", inputs=None)
        ticker = Scheduler(svc.ctx)
        stop = asyncio.Event()
        wakes = 0

        async def watch() -> None:
            nonlocal wakes
            deadline = time.monotonic() + RESET_IN_S + 60
            while time.monotonic() < deadline:
                with Reader.open(engine_home) as reader:
                    events = reader.events(first.run_id)
                wakes = sum(
                    1 for e in events if e.kind == "run_resumed" and e.data["reason"] == "limit"
                )
                if events[-1].kind == "run_finished":
                    break
                await asyncio.sleep(0.5)
            stop.set()

        await asyncio.gather(ticker.serve(stop), watch())
    return first, wakes


async def main(log: Log | None = None, pr: str = PR) -> int:
    from fake_model import FakeModel, Turn, text  # noqa: PLC0415
    from qma.harness import TestMode  # noqa: PLC0415

    log = log or Log(PR, "ep11-e05")
    boot()
    live.use_fake_key()
    fake = FakeModel([Turn([text(ANSWER)]) for _ in range(8)]).start()
    home = throwaway_home(pr, "e05")
    live.put_providers(home, {"fake": live.fake_row(fake.url)})
    root = workflow(
        "pause",
        [
            node("start", "trigger"),
            node("first", "llm", "triage", prompt_ref="p.md", schema_ref="s.json"),
            node("slow", "script", script="slow.py"),
            node("after", "llm", "triage", prompt_ref="p.md", schema_ref="s.json"),
        ],
        {"start": {"main": [edge("first"), edge("slow")]}, "slow": {"main": [edge("after")]}},
        {"p.md": "Name the capital of France.", "s.json": json.dumps(SCHEMA), "slow.py": SLOW},
    )
    resets = int(time.time()) + RESET_IN_S
    expected = (datetime.fromtimestamp(resets, UTC) + timedelta(seconds=SLACK_S)).isoformat()
    settings: dict[str, Setting] = {**DEFAULTS, "limits.slack": SLACK_S, "scheduler.tick": 1}
    try:
        async with opened(home, test=TestMode(loopback_http_provider=True)) as h:
            h.harness._deps.on_plan_limits(
                fact(
                    {
                        "status": "rejected",
                        "rateLimitType": "five_hour",
                        "overageStatus": "rejected",
                        "isUsingOverage": False,
                        "resetsAt": resets,
                    }
                )
            )
            log(f"fed a rejected five-hour reading; reset {datetime.fromtimestamp(resets, UTC)}")

            async def reset() -> None:
                await asyncio.sleep(max(resets - time.time(), 0) + 0.5)
                h.harness._deps.on_plan_limits(
                    fact(
                        {
                            "status": "allowed",
                            "rateLimitType": "five_hour",
                            "utilization": 0.1,
                            "resetsAt": int(time.time()) + 3600,
                        }
                    )
                )
                log("the window reset: fed a 10% five-hour reading")

            feeder = asyncio.create_task(reset())
            started = time.monotonic()
            engine_home = throwaway_home(pr, "e05-engine")
            first, wakes = await woken(engine_home, root, Routed(h.harness), settings)
            took = time.monotonic() - started
            events, spans = read(engine_home, first.run_id)
            await feeder
            needs = [
                b["content"]
                for chat in h.home.chats_dir.glob("*.json")
                for b in h.blocks(chat.stem)
                if b["type"] == "needs_you"
            ]
    finally:
        fake.stop()
    for event in events:
        if event.kind in (
            "node_waiting",
            "run_paused",
            "run_resumed",
            "node_finished",
            "run_finished",
        ):
            shown = {k: event.data.get(k) for k in ("node_id", "attempt", "reason", "resume_at")}
            log(f"{event.at} {event.kind} {json.dumps(shown)}")
    for span in spans:
        if span.profile is not None:
            log(
                f"span {span.node_id} attempt {span.attempt} {span.status} "
                f"{span.profile}/{span.model}"
            )
    finished = events[-1].data.get("status") if events[-1].kind == "run_finished" else None
    log(
        f"run {first.run_id}: start returned {first.status}, ticker wakes {wakes}, finished "
        f"{finished} after {took:.1f} s; needs_you blocks: {needs}"
    )
    index = {e.seq: e for e in events}
    kinds = [(e.seq, e.kind, e.data.get("node_id")) for e in index.values()]
    waited = [e.data for e in events if e.kind == "node_waiting"]
    paused = [s for s, k, _ in kinds if k == "run_paused"]
    resumed = [s for s, k, _ in kinds if k == "run_resumed"]
    slow_done = [s for s, k, n in kinds if k == "node_finished" and n == "slow"]
    after_start = [s for s, k, n in kinds if k == "node_scheduled" and n == "after"]
    log.check(
        "the model node waits on the limit with resume_at at the reset plus slack",
        [(w.get("node_id"), w.get("reason"), w.get("resume_at")) for w in waited]
        == [("first", "limit", expected)],
        waited,
    )
    log.check("no needs_you block appeared", needs == [], needs)
    log.check(
        "the script finished while the run drained, and the next model node started only after "
        "the resume",
        bool(slow_done and paused and resumed and after_start)
        and slow_done[0] < paused[0] < resumed[0] < after_start[0],
        {"slow": slow_done, "paused": paused, "resumed": resumed, "after": after_start},
    )
    log.check(
        "the start returned waiting and the ticker resumed the run alone after the reset; it "
        "passed",
        first.status == "waiting" and wakes >= 1 and finished == "passed" and took >= RESET_IN_S,
        {"start": first.status, "wakes": wakes, "finished": finished, "seconds": round(took, 1)},
    )
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
