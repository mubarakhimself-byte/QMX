"""S18. Working set of one idle and one busy CLI, in MB.

Idle is a connected CLI that has answered one turn and waits. Busy is the peak working
set sampled every half second while the CLI runs a turn with an 8-second Bash call.
"""

from __future__ import annotations

import asyncio
import os

from common import (
    Log,
    bundled_cli,
    cli_pid,
    describe,
    plan_options,
    require_plan_login,
    scrub_process_env,
    working_set_mb,
)

BUSY_PROMPT = "Run this exact Bash command and reply done: sleep 8"


async def main() -> int:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    log = Log("hp0-ram")
    require_plan_login(log, bundled_cli())
    scrub_process_env(os.environ)
    async with ClaudeSDKClient(options=plan_options()) as client:
        pid = cli_pid(client)
        log(f"CLI pid {pid}, after connect: {working_set_mb(pid)} MB")
        for prompt in ("say ok", BUSY_PROMPT):
            samples: list[float] = []

            async def sample(pid: int = pid, samples: list[float] = samples) -> None:
                while True:
                    samples.append(working_set_mb(pid))
                    await asyncio.sleep(0.5)

            sampler = asyncio.create_task(sample())
            log(f"> {prompt}")
            await client.query(prompt)
            async for message in client.receive_response():
                log(describe(message))
            sampler.cancel()
            log(f"samples during '{prompt}': {samples}")
            if prompt == "say ok":
                await asyncio.sleep(3)
                idle = working_set_mb(pid)
                log.row("S18 idle CLI working set", f"{idle} MB", "PASS")
            else:
                log.row("S18 busy CLI peak working set", f"{max(samples)} MB", "PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
