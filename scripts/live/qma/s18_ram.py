"""S18, memory per session, on a harness plan chat. The CLI's pid comes from the chat's pid file,
which the launcher writes. Idle is the CLI three seconds after its first turn; busy is the peak
sampled every half second while it runs an 8-second Bash call.

PASS when both are recorded and each working set is within 25% of HP0's bare-CLI figures
(184.1 MB idle, 194.1 MB busy). Private commit, what a job
memory limit counts, is logged beside it.

    s18_ram.py
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import psutil
from common import SHIP_HOME, Log, Session, boot, chat_args, require_login, use_fake_home

HP0_MB = {"idle": 184.1, "busy": 194.1}
BUSY = "Run this exact Bash command, then reply done: sleep 8"


def memory_mb(pid: int) -> tuple[float, float]:
    info: Any = psutil.Process(pid).memory_info()
    return round(info.rss / 2**20, 1), round(info.private / 2**20, 1)


async def run(log: Log) -> None:
    from qma.launcher import pid_path, read_pid_record  # noqa: PLC0415

    args = chat_args(__doc__).parse_args()
    require_login(log)
    session = await Session.start(
        SHIP_HOME,
        model=args.model,
        workspace=args.workspace,
        title="hp10 s18",
        mode="bypassPermissions",
        tools=["Bash"],
    )
    try:
        await session.turn(log, "Reply with the single word ok.")
        record = read_pid_record(pid_path(session.home.procs_dir, session.chat))
        if record is None:
            log.check("the chat has a pid file", False, None)
            return
        log(f"pid file: launcher {record.launcher_pid}, CLI {record.cli_pid}")
        await asyncio.sleep(3)
        idle = memory_mb(record.cli_pid)
        log(f"idle: working set {idle[0]} MB, private commit {idle[1]} MB")
        samples: list[tuple[float, float]] = []

        async def sample() -> None:
            while True:
                samples.append(memory_mb(record.cli_pid))
                await asyncio.sleep(0.5)

        sampler = asyncio.create_task(sample())
        await session.turn(log, BUSY)
        sampler.cancel()
        busy = (max(s[0] for s in samples), max(s[1] for s in samples))
        log(f"busy peak over {len(samples)} samples: working set {busy[0]} MB, commit {busy[1]} MB")
        for name, seen in (("idle", idle[0]), ("busy", busy[0])):
            ratio = seen / HP0_MB[name]
            log.check(
                f"{name} working set within 25% of HP0",
                0.75 <= ratio <= 1.25,
                f"{seen} MB against {HP0_MB[name]} MB ({ratio:.2f}x)",
            )
    finally:
        await session.harness.close()


def main() -> int:
    log = Log("hp10-s18")
    boot()
    use_fake_home()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
