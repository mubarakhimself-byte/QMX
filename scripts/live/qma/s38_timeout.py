"""S38, the gate fails closed on timeout, and the perf lane. Key chats on the fake model in
bypass mode.

Part 1. A test build whose gate callback sleeps past `GATE_TIMEOUT_S`. The fake model makes a
Bash call that would create a marker file and an Edit of a workspace file. PASS when both are
blocked with an error naming the timeout, the marker does not exist, and the file is unchanged.

Part 2. The real gate with three chats streaming at once on one harness: 201 scripted Bash
calls in all. Each callback's time from hook input to output is recorded. PASS when every call
went through the gate and p99 is at most 50 ms. Trunk has no gate on this path.

    s38_timeout.py
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from typing import Any

from common import (
    SCRATCH,
    Log,
    Session,
    boot,
    throwaway_home,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import FakeModel, Turn, tool_use
from money_lane import Call, direct_row, run_calls

P99_LIMIT_MS = 50.0
CALLS = 201


async def timeout_part(log: Log) -> None:
    from qma.harness import (  # noqa: PLC0415
        TestMode,
        guard,
    )
    from qma.harness.launch import GATE_TIMEOUT_S  # noqa: PLC0415

    workspace = SCRATCH / "hp8-s38-ws"
    workspace.mkdir(parents=True, exist_ok=True)
    marker = workspace / "s38-ran.txt"
    marker.unlink(missing_ok=True)
    target = workspace / "notes.txt"
    target.write_text("before\n", encoding="utf-8")
    real = guard.pre_tool_use

    def sleepy(rules: Any) -> Any:
        async def callback(*args: Any) -> Any:
            await asyncio.sleep(GATE_TIMEOUT_S + 5)
            return {}

        return callback

    guard.pre_tool_use = sleepy
    calls = [
        Call(
            "Bash past the timeout",
            "Bash",
            {"command": f"echo ran > {marker.as_posix()}", "description": "write"},
        ),
        Call("Read before the Edit", "Read", {"file_path": target.as_posix()}),
        Call(
            "Edit past the timeout",
            "Edit",
            {"file_path": target.as_posix(), "old_string": "before", "new_string": "after"},
        ),
    ]
    log(
        f"--- part 1: the gate sleeps {GATE_TIMEOUT_S + 5:.0f} s, "
        f"past GATE_TIMEOUT_S={GATE_TIMEOUT_S}"
    )
    try:
        session, fake, outcomes = await run_calls(
            log,
            throwaway_home("hp8-s38"),
            calls,
            test=TestMode(deny_rules=False, loopback_http_provider=True),
            mode="bypassPermissions",
            tools=["Bash", "Read", "Edit"],
            title="s38 timeout",
            workspace=workspace,
        )
    finally:
        guard.pre_tool_use = real
    try:
        for call in (calls[0], calls[2]):
            kind, said = outcomes[call.label]
            log.check(f"{call.label} is blocked naming the timeout", kind == "timeout", said)
        log.check("the Bash call did not run", not marker.exists(), marker.exists())
        log.check(
            "the file is unchanged",
            target.read_text(encoding="utf-8") == "before\n",
            target.read_text(encoding="utf-8"),
        )
    finally:
        await session.harness.close()
        fake.stop()


async def perf_part(log: Log) -> None:
    from qma.harness import (  # noqa: PLC0415
        NewChat,
        OperatorText,
        TestMode,
        guard,
    )

    timings: list[float] = []
    real = guard.pre_tool_use

    def timed(rules: Any) -> Any:
        inner = real(rules)

        async def callback(*args: Any) -> Any:
            start = time.perf_counter()
            found = await inner(*args)
            timings.append((time.perf_counter() - start) * 1000)
            return found

        return callback

    guard.pre_tool_use = timed
    fake = FakeModel(
        [
            Turn([tool_use("Bash", {"command": f"echo s38 {n}", "description": "echo"})])
            for n in range(CALLS)
        ]
    ).start()
    root = throwaway_home("hp8-s38-perf")
    from common import put_providers  # noqa: PLC0415

    put_providers(root, {"fake": direct_row(fake.url)})
    log(f"--- part 2: {CALLS} scripted Bash calls over three chats streaming at once")
    session = await Session.start(
        root,
        model="opus",
        workspace=SCRATCH / "hp8-s38-ws",
        title="s38 perf 1",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="bypassPermissions",
        tools=["Bash"],
    )
    try:
        chats = [session.chat]
        for index in (2, 3):
            chats.append(
                await session.harness.start_chat(
                    NewChat(
                        title=f"s38 perf {index}",
                        model="opus",
                        workspace=SCRATCH / "hp8-s38-ws",
                        profile="fake",
                        mode="bypassPermissions",
                    )
                )
            )
        started = time.perf_counter()
        await asyncio.gather(
            *(session.harness.send(chat, OperatorText("Run the echo checks.")) for chat in chats)
        )
        records = await asyncio.gather(*(wait_turn(session.home, chat, 600) for chat in chats))
        wall = time.perf_counter() - started
        log(f"turns: {[record.turn for record in records]} in {wall:.1f} s")
        ordered = sorted(timings)
        p50 = statistics.median(ordered)
        p99 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.99))]
        log(
            f"trunk: no gate on this path; head gate calls={len(ordered)} "
            f"p50={p50:.3f} ms p99={p99:.3f} ms max={ordered[-1]:.3f} ms"
        )
        log.check("every scripted call went through the gate", len(ordered) >= CALLS, len(ordered))
        log.check(f"p99 at most {P99_LIMIT_MS} ms", p99 <= P99_LIMIT_MS, f"{p99:.3f} ms")
    finally:
        guard.pre_tool_use = real
        await session.harness.close()
        fake.stop()


async def run(log: Log, parts: set[str]) -> None:
    if "timeout" in parts:
        await timeout_part(log)
    if "perf" in parts:
        await perf_part(log)


def main() -> int:
    parts = set(sys.argv[1:]) or {"timeout", "perf"}
    log = Log("hp8-s38" if parts == {"timeout", "perf"} else f"hp8-s38-{'-'.join(sorted(parts))}")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log, parts))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
