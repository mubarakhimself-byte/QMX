"""DLG lanes: `delegate` v2 live, on the plan login and on the fake model.

    p5_delegate.py p5     a haiku copilot on the ship home's plan login starts three helpers on
                          the OpenRouter rows (Kimi, DeepSeek, Qwen), keeps talking while they
                          run, and a host restart afterwards delivers each answer exactly once.
    p5_delegate.py perf   the milliseconds from a `delegate` start to its handle, against the
                          parent's blocking delegate, on the cheapest OpenRouter row.
    p5_delegate.py stall  a helper on the fake model that repeats one tool call, so the stuck
                          rules stop it; the parent goes on.

`p5` and `perf` run on a throwaway home whose plan chats use the ship home's plan login, so
nothing in the ship home changes; whoever runs them holds the engine lane lock
(`mkdir D:/QMX-worktrees/.engine-lane-lock`) and this script never takes it. The OpenRouter
rows are billed to the lane's own spend ledger, a probe bound that says so in the log.

Logs go to `<QMA_EVIDENCE_DIR>/owner-dlg-<lane>.log`.
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Final

from common import (
    EVIDENCE,
    SCRATCH,
    SHIP_HOME,
    Log,
    boot,
    fake_row,
    put_providers,
    session_blocks,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel, Turn, text, tool_use
from spend import Ledger, Prices, key_usage, openrouter_key

LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
TURN_S: Final = 300.0
COMPLETION_S: Final = 240.0
BUDGET_USD: Final = float(os.environ.get("DLG_SPEND_BUDGET", "0.30"))
"""A probe bound on this lane's own OpenRouter spend, not a QMX limit. The lane says so in its
log and in the ledger's first row."""
KIMI: Final = "moonshotai/kimi-k2.5"
DEEPSEEK: Final = "deepseek/deepseek-v4.1-flash"
QWEN: Final = "qwen/qwen3.6-plus"
OPENROUTER_ROW: Final = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": {"opus": KIMI, "sonnet": DEEPSEEK, "haiku": QWEN, "fable": DEEPSEEK},
}
KIMI_PRICES: Final = Prices(KIMI, 0.5e-6, 2.5e-6)
"""The dearest of the three rows, so the guard's worst case covers every one of them."""
DONE_WORDS: Final = "DONE"


def require_lock() -> None:
    if not LOCK.is_dir():
        raise SystemExit(f"plan lanes run only while holding {LOCK}")


def spend_guard() -> Ledger:
    secret = openrouter_key()
    if secret is None:
        raise SystemExit("BLOCKED: keyring qmx/openrouter is empty")
    if not EVIDENCE:
        raise SystemExit("set QMA_EVIDENCE_DIR, e.g. D:/QMX-worktrees/qma-ship/build/evidence/dlg")
    ledger = Path(EVIDENCE) / "dlg-openrouter-spend.tsv"
    return Ledger(ledger, BUDGET_USD, KIMI_PRICES, key_usage(secret))


def lane_home(slug: str, *, fresh: bool = True) -> Any:
    """A throwaway QMX home. Its plan chats read the ship home's plan login, so its rows can hold
    the OpenRouter profiles without touching the ship home's settings. `fresh=False` reopens the
    same home, which is how this lane restarts its host."""
    from qma.harness import QmxHome  # noqa: PLC0415

    class LaneHome(QmxHome):
        @property
        def plan_dir(self) -> Path:
            return SHIP_HOME / "claude"

    root = throwaway_home(slug) if fresh else Path(SCRATCH) / "homes" / slug
    return LaneHome(root)


async def open_lane(slug: str, *, fresh: bool = True) -> tuple[Any, Any, Any]:
    from qma.harness import Harness  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    home = lane_home(slug, fresh=fresh)
    put_providers(
        home.root,
        {
            "openrouter": OPENROUTER_ROW,
            "delegate_targets": ["claude", "openrouter"],
        },
    )
    control = control_service(home)
    harness = await Harness.open(home, control=control)
    return harness, home, control


def folder(root: Path, name: str) -> Path:
    found = root / "workspaces" / name
    found.mkdir(parents=True, exist_ok=True)
    return found


async def operator_turn(
    harness: Any, home: Any, chat: str, words: str, log: Log
) -> tuple[Any, str]:
    from qma.harness import OperatorText  # noqa: PLC0415

    handle = await harness.run_turn(chat, OperatorText(words))
    done = await asyncio.wait_for(handle.result(), TURN_S)
    log(f"operator turn ended: status={done.status} text={(done.text or '')[:120]!r}")
    return done, done.text or ""


def completions(control: Any, parent: str) -> list[dict[str, Any]]:
    return list(control.delegate_completions_all(parent))


async def wait_completions(
    control: Any, parent: str, wanted: int, seconds: float = COMPLETION_S
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = completions(control, parent)
        if len(found) >= wanted:
            return found
        await asyncio.sleep(0.5)
    return completions(control, parent)


def helper_calls(prompt: str) -> list[dict[str, Any]]:
    return [
        {"task": prompt, "profile": "openrouter", "model": KIMI, "group": "p5"},
        {"task": prompt, "profile": "openrouter", "model": DEEPSEEK, "group": "p5"},
        {"task": prompt, "profile": "openrouter", "model": QWEN, "group": "p5"},
    ]


COPILOT_ASK: Final = (
    "Start three helpers with the mcp__qmx_delegate__run tool. Call it three times, in this "
    "order, with exactly these arguments and nothing else in them:\n"
    '1. {"task": "Reply with the single word ALPHA and nothing else.", "profile": "openrouter", '
    f'"model": "{KIMI}"}}\n'
    '2. {"task": "Reply with the single word BETA and nothing else.", "profile": "openrouter", '
    f'"model": "{DEEPSEEK}"}}\n'
    '3. {"task": "Reply with the single word GAMMA and nothing else.", "profile": "openrouter", '
    f'"model": "{QWEN}"}}\n'
    "The three calls return at once with a handle; do not wait for their answers. Then reply "
    f"with the single word {DONE_WORDS}."
)


async def p5(log: Log) -> None:
    from qma.harness import Interactive, NewChat  # noqa: PLC0415

    require_lock()
    guard = spend_guard()
    log(f"OpenRouter spend guard: budget USD {BUDGET_USD} (a probe bound, not a QMX limit)")
    harness, home, control = await open_lane("dlg-p5")
    parent = await harness.start_chat(
        NewChat(
            title="dlg copilot",
            model="haiku",
            workspace=folder(home.root, "copilot"),
            kind=Interactive(),
        )
    )
    log(f"copilot: {parent} on claude/haiku through the ship home's plan login")
    stopped: list[dict[str, Any]] = []
    try:

        async def start_three() -> tuple[Any, str]:
            return await operator_turn(harness, home, parent, COPILOT_ASK, log)

        done, said = await guard.spend("p5 copilot asks for three helpers", 4, 4096, start_three)
        log(f"copilot turn: {done.status}; the copilot said {said[:80]!r}")
        listed = control.delegate_completions_all(parent)
        helpers = answer_list(await harness._delegate(parent, "delegate_list", "{}"))  # pyright: ignore[reportPrivateUsage]
        log(f"helpers after the copilot's turn: {helpers}")
        started_by_model = [
            row for row in helpers if str(row.get("state")) in {"queued", "running"}
        ]
        log.check(
            "the copilot started its helpers through the delegate tool",
            len(started_by_model) >= 1,
            [row.get("handle") for row in started_by_model],
        )
        log(f"completions stored so far: {len(listed)}")
        still_running = [row for row in helpers if row.get("state") == "running"]
        kept, kept_said = await guard.spend(
            "p5 the copilot keeps talking",
            2,
            1024,
            lambda: operator_turn(
                harness, home, parent, "Reply with the word WORKING and nothing else.", log
            ),
        )
        log.check(
            "the copilot kept talking while helpers ran",
            kept.status == "ok" and bool(kept_said),
            {"running_when_asked": len(still_running), "said": kept_said[:40]},
        )
        found = await wait_completions(control, parent, 3)
        for row in found:
            summary = str(row["summary"])[:140]
            log(f"completion {row['handle']}: state={row['state']} summary={summary!r}")
        log.check(
            "three answers were stored before any was announced",
            len(found) == 3
            and all(row["state"] == "done" for row in found)
            and all(row["delivered_at"] is None for row in found),
            [(row["handle"], row["state"], row["delivered_at"]) for row in found],
        )
        await harness.close()
        harness, home, control = await open_lane("dlg-p5", fresh=False)
        log("host restarted: a second harness opened the same home")
        await guard.spend(
            "p5 the restarted host delivers",
            2,
            1024,
            lambda: operator_turn(harness, home, parent, "What did the helpers find?", log),
        )
        carried = carried_report(control, parent)
        log(f"report carried to the model: {carried[:220]!r}")
        stored = completions(control, parent)
        log(
            "completions after the restart: "
            + json.dumps([(r["handle"], r["state"], r["delivered_at"] is not None) for r in stored])
        )
        log.check(
            "a restart delivers every stored answer exactly once",
            len(stored) == 3
            and all(row["delivered_at"] is not None for row in stored)
            and carried.startswith("Helper reports")
            and all(str(row["handle"]) in carried for row in stored),
            [row["handle"] for row in stored],
        )
        await guard.spend(
            "p5 a second turn carries nothing",
            2,
            1024,
            lambda: operator_turn(harness, home, parent, "Say SECOND and nothing else.", log),
        )
        again = carried_report(control, parent)
        log.check(
            "a second turn carries no answer again",
            not again.startswith("Helper reports") and again.startswith("Say SECOND"),
            again[:80],
        )
        stopped = stored
    finally:
        await harness.close()
    log.check(
        "every helper's child chat closed with its handle",
        all(row["state"] in {"done", "failed", "stalled", "stopped"} for row in stopped),
        [row["state"] for row in stopped],
    )


def answer_list(reply: str) -> list[dict[str, Any]]:
    found = json.loads(reply)
    return list(found.get("helpers", []))


def carried_report(control: Any, parent: str) -> str:
    """The prompt the parent's CLI last received: the CLI replays a user message as a block, so
    the report a turn carried is readable there."""
    said = [
        str(block["content"].get("text", ""))
        for block in session_blocks(control, parent)
        if block["type"] == "user"
    ]
    return said[-1] if said else ""


async def perf(log: Log) -> None:
    from qma.harness import Child, InjectedText, Interactive, NewChat  # noqa: PLC0415

    require_lock()
    guard = spend_guard()
    harness, home, control = await open_lane("dlg-perf")
    parent = await harness.start_chat(
        NewChat(
            title="dlg perf parent",
            model="haiku",
            workspace=folder(home.root, "perf"),
            kind=Interactive(),
        )
    )
    task = "Reply with the single word OK and nothing else."
    head: list[float] = []
    base: list[float] = []
    try:
        for index in range(3):
            arguments = json.dumps(
                {"task": task, "profile": "openrouter", "model": DEEPSEEK, "group": "perf"}
            )

            async def start(body: str = arguments) -> str:
                return await harness._delegate(parent, "delegate_run", body)  # pyright: ignore[reportPrivateUsage]

            started = time.perf_counter()
            await guard.spend(f"perf head {index}", 2, 512, start)
            took = (time.perf_counter() - started) * 1000
            head.append(took)
            log(f"head call {index}: handle in {took:.1f} ms")
        await wait_completions(control, parent, 3)
        for index in range(3):

            async def blocking(step: int = index) -> str:
                child = await harness.start_chat(
                    NewChat(
                        title=f"perf baseline {step}",
                        model=DEEPSEEK,
                        profile="openrouter",
                        kind=Child(parent, unattended=False),
                        workspace=folder(home.root, "perf-baseline"),
                    )
                )
                try:
                    handle = await harness.run_turn(child, InjectedText(task))
                    await handle.result()
                finally:
                    await harness.close_chat(child)
                return ""

            started = time.perf_counter()
            await guard.spend(f"perf baseline {index}", 2, 512, blocking)
            took = (time.perf_counter() - started) * 1000
            base.append(took)
            log(f"baseline call {index}: the parent had no handle for {took:.1f} ms")
    finally:
        await harness.close()
    head_median, base_median = statistics.median(head), statistics.median(base)
    log(f"PERF median from delegate to the handle: {head_median:.1f} ms")
    log(f"PERF median of the parent's blocking delegate: {base_median:.1f} ms")
    log(f"PERF three head calls: {[round(one, 1) for one in head]}")
    log(f"PERF three baseline calls: {[round(one, 1) for one in base]}")
    log.check(
        "the median from delegate to the handle is at most 1,000 ms",
        head_median <= 1000,
        head_median,
    )


async def stall(log: Log) -> None:
    from qma.harness import Harness, InjectedText, NewChat  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home("dlg-stall")
    fake = FakeModel(
        [
            Turn([tool_use("mcp__qmx_delegate__run", {"task": "loop", "profile": "fake"})]),
            Turn([text("started")]),
            *[Turn([tool_use("mcp__qmx_library__search", {"query": "same"})]) for _ in range(7)],
            Turn([text("never reached")]),
        ]
    ).start()
    put_providers(root, {"fake": fake_row(fake.url), "delegate_targets": ["fake"]})
    from qma.harness import QmxHome, TestMode  # noqa: PLC0415

    home = QmxHome(root)
    control = control_service(home)
    harness = await Harness.open(home, control=control, test=TestMode(loopback_http_provider=True))
    try:
        from qma.harness import Background  # noqa: PLC0415

        parent = await harness.start_chat(
            NewChat(
                title="dlg stall parent",
                model="opus",
                profile="fake",
                mode="bypassPermissions",
                workspace=folder(home.root, "stall"),
                kind=Background(),
            )
        )
        handle = await harness.run_turn(parent, InjectedText("start a looping helper"))
        done = await asyncio.wait_for(handle.result(), TURN_S)
        log(f"parent turn: status={done.status} text={(done.text or '')[:80]!r}")
        found = await wait_completions(control, parent, 1, seconds=120)
        for row in found:
            log(f"completion {row['handle']}: state={row['state']} {str(row['summary'])[:160]!r}")
        log.check(
            "the stuck rules stopped the looping helper",
            bool(found) and found[0]["state"] == "stalled",
            [row["state"] for row in found],
        )
        after = await harness.run_turn(parent, InjectedText("carry on"))
        ended = await asyncio.wait_for(after.result(), TURN_S)
        log(f"parent turn after the stall: status={ended.status} text={(ended.text or '')[:60]!r}")
        log.check(
            "the parent continued after its helper stalled",
            done.status == "ok" and ended.status == "ok",
            {"first": done.status, "after": ended.status},
        )
    finally:
        await harness.close()
        fake.stop()


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    lanes = ("p5", "perf", "stall")
    if lane not in lanes:
        raise SystemExit(f"usage: p5_delegate.py {{{','.join(lanes)}}}")
    log = Log(f"owner-dlg-{lane}")
    boot()
    use_fake_home()
    use_fake_key()
    runs = {"p5": p5, "perf": perf, "stall": stall}
    try:
        asyncio.run(runs[lane](log))
    except SystemExit:
        raise
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
