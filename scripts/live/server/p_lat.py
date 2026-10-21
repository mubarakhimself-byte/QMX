"""P-LAT: Library read and write p95 over the tailnet (LIB4 lane 5, the perf block).

Run from `qmx-agents/` with the agents venv:

    uv run --no-sync python ../scripts/live/server/p_lat.py

The Hub runs on the server; this process is the PC. It writes 20 `note` objects and reads them
back 100 times each way through the Hub, and records p50 and p95 against the plan's lines: read
p95 at most 300 ms, write p95 at most 1,500 ms. A miss is a latency bug for the backlog, not a
block, so the lane exits 0 either way and prints `MISS` (ADR-19's own rule: never keep the PC
primary for latency).

Writes `<LIB4_EVIDENCE>/<LIB4_LOG_PREFIX>lib4-plat.log`.
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Sequence
from typing import Final

from e67_claims import (
    HOMES,
    Log,
    health,
    prepare_server,
    start_hub,
    stop_hub,
    write_home,
)

READ_LINE_MS: Final = 300.0
WRITE_LINE_MS: Final = 1_500.0
WRITES: Final = 20
READS: Final = 100
LANE_ID: Final = "plat"


def percentile(values: list[float], share: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(share * (len(ordered) - 1))))
    return ordered[index]


def main(argv: Sequence[str] | None = None) -> int:
    from qmx_library.client import HubClient  # noqa: PLC0415
    from qmx_library.port import Draft  # noqa: PLC0415

    log = Log("lib4-plat")
    hub_url = ""
    try:
        log.say(f"lane p-lat at {time.strftime('%Y-%m-%dT%H:%M:%S')}")
        prepare_server(LANE_ID)
        hub_url, key = start_hub(LANE_ID)
        write_home(HOMES / f"lib4-{LANE_ID}", hub_url, key)
        log.check(health(hub_url, key).get("ok") is True, f"hub answers at {hub_url}")
        client = HubClient(hub_url, key, "operator")

        writes: list[float] = []
        written = []
        for index in range(WRITES):
            started = time.perf_counter()
            done = client.put(
                Draft(
                    "note",
                    f"plat-{index}",
                    title=f"p-lat {index}",
                    fields={"index": index},
                ),
                on="main",
                expected_head=client.call("head", item=f"plat-{index}", ref="main"),
            )
            writes.append((time.perf_counter() - started) * 1000.0)
            written.append(done.object_id)

        reads: list[float] = []
        for index in range(READS):
            object_id = written[index % len(written)]
            started = time.perf_counter()
            client.get(object_id)
            reads.append((time.perf_counter() - started) * 1000.0)

        read_p95 = percentile(reads, 0.95)
        write_p95 = percentile(writes, 0.95)
        log.say(f"read  p50={statistics.median(reads):.1f}ms p95={read_p95:.1f}ms n={len(reads)}")
        log.say(
            f"write p50={statistics.median(writes):.1f}ms p95={write_p95:.1f}ms n={len(writes)}"
        )
        read_ok = read_p95 <= READ_LINE_MS
        write_ok = write_p95 <= WRITE_LINE_MS
        log.say(
            f"{'PASS' if read_ok else 'MISS'} read p95 {read_p95:.1f}ms "
            f"against {READ_LINE_MS:.0f}ms"
        )
        log.say(
            f"{'PASS' if write_ok else 'MISS'} write p95 {write_p95:.1f}ms against "
            f"{WRITE_LINE_MS:.0f}ms"
        )
        log.say(
            f"P-LAT read_p95_ms={read_p95:.1f} write_p95_ms={write_p95:.1f} "
            f"against read={READ_LINE_MS:.0f} write={WRITE_LINE_MS:.0f}"
        )
    except Exception as error:
        log.check(False, f"lane aborted: {error}")
    finally:
        if hub_url:
            stop_hub(LANE_ID)
    return log.close()


if __name__ == "__main__":
    raise SystemExit(main())
