"""HP10 perf: wall time of `GET /api/usage` with 1,000 `model_call` rows in the journals (ten
chats of 100 plan turns each), over loopback HTTP to the real routes in this process. Twenty
timed requests after one warm-up. Trunk has no usage route, so there is no trunk number.

PASS when the p95 is at most 200 ms.

    usage_perf.py
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path

from approval_lane import Host
from common import Log, Session, boot, throwaway_home, use_fake_home

CHATS = 10
TURNS = 100
REQUESTS = 20
LIMIT_MS = 200.0


def seed(root: Path) -> int:
    from qma.harness.project import TurnUsage  # noqa: PLC0415
    from qma.harness.usage import Totals, plan_row  # noqa: PLC0415
    from qmx_ledger.journal import RunJournal  # noqa: PLC0415

    rows = 0
    for chat in range(CHATS):
        run = f"perf-{chat:02d}"
        with RunJournal(root / "runs" / run / "journal.jsonl", run) as journal:
            totals = Totals()
            for n in range(1, TURNS + 1):
                turn = TurnUsage(
                    session_id=run,
                    model_usage={
                        "claude-haiku-5-5": {
                            "inputTokens": 3 * n,
                            "outputTokens": 40 * n,
                            "cacheReadInputTokens": 20_000 * n,
                            "cacheCreationInputTokens": 900 * n,
                        }
                    },
                    total_cost_usd=0.0004 * n,
                    num_turns=1,
                )
                payload, totals = plan_row(turn, totals)
                if payload is not None:
                    journal.append("model_call", payload)
                    rows += 1
    return rows


async def run(log: Log) -> None:
    root = throwaway_home("hp10-perf")
    rows = seed(root)
    log(f"seeded {rows} model_call rows in {CHATS} journals")
    session = await Session.start(
        root, model="haiku", workspace=throwaway_home("hp10-perf-ws"), title="perf"
    )
    try:
        async with Host(session) as host:
            warm = await host.http.get("/api/usage")
            log(f"warm-up {warm.status_code}: tokens {warm.json()['tokens']}")
            took: list[float] = []
            for _ in range(REQUESTS):
                start = time.perf_counter()
                reply = await host.http.get("/api/usage")
                took.append((time.perf_counter() - start) * 1000)
                reply.raise_for_status()
        took.sort()
        p95 = took[int(0.95 * len(took)) - 1]
        log(f"ms per request, sorted: {[round(t, 1) for t in took]}")
        log(f"median {statistics.median(took):.1f} ms, p95 {p95:.1f} ms, max {took[-1]:.1f} ms")
        calls = warm.json()["tokens"]["claude"]["calls"]
        log.check("the page counted every seeded row", calls == rows, calls)
        log.check(f"p95 at most {LIMIT_MS:.0f} ms", p95 <= LIMIT_MS, f"{p95:.1f} ms")
    finally:
        await session.harness.close()


def main() -> int:
    log = Log("hp10-perf")
    boot()
    use_fake_home()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
