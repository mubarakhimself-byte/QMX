"""S19 prototype. A plan turn with a Bash call under `reduced_env()`, then with a fake key.

The fake `ANTHROPIC_API_KEY` is not a credential. Were it to reach the CLI, the request
would fail with an auth error and bill nothing. The control run proves that: it skips
the scrub, so the CLI sees the fake key.
"""

from __future__ import annotations

import asyncio
import os
import sys

from claude_agent_sdk import Message, RateLimitEvent
from common import (
    Log,
    bundled_cli,
    is_ok,
    plan_options,
    reduced_env,
    require_plan_login,
    run_turns,
    scrub_process_env,
)

FAKE_KEY = "sk-ant-api03-hp0-probe-fake-key-not-a-credential"
BASH_PROMPT = "Run this exact Bash command and reply with its output only: env | cut -d= -f1 | sort"
BANNED = ("ANTHROPIC_API_KEY", "HTTPS_PROXY", "NODE_EXTRA_CA_CERTS", "CLAUDE_CODE_USE_BEDROCK")


def saw_rate_limit(messages: list[Message]) -> bool:
    return any(isinstance(m, RateLimitEvent) for m in messages)


async def main() -> int:
    log = Log("hp0-env")
    require_plan_login(log, bundled_cli())
    original = dict(os.environ)

    removed = scrub_process_env(os.environ)
    log(f"run 1 removed names: {removed}")
    run1 = await run_turns(log, plan_options(), [BASH_PROMPT])
    seen = " ".join(map(str, run1))
    leaked = [name for name in BANNED if name in seen]
    ok1 = is_ok(run1)
    log.row(
        "S19 Bash runs under reduced env",
        f"ok={ok1} banned names seen={leaked}",
        "PASS" if ok1 and not leaked else "FAIL",
    )

    os.environ.clear()
    os.environ.update(original | {"ANTHROPIC_API_KEY": FAKE_KEY})
    removed = scrub_process_env(os.environ)
    log(f"run 2 removed names: {removed}")
    run2 = await run_turns(log, plan_options(), ["say ok"])
    plan2, ok2 = saw_rate_limit(run2), is_ok(run2)
    log.row(
        "S19 fake key in parent env, scrubbed",
        f"RateLimitEvent={plan2} ok={ok2}",
        "PASS" if plan2 and ok2 else "FAIL",
    )

    if "--no-control" not in sys.argv:
        os.environ.clear()
        os.environ.update(reduced_env(original) | {"ANTHROPIC_API_KEY": FAKE_KEY})
        log("control: fake key left in the env the SDK merges")
        run3 = await run_turns(log, plan_options(), ["say ok"])
        plan3, ok3 = saw_rate_limit(run3), is_ok(run3)
        log.row(
            "S19 control, fake key not scrubbed",
            f"RateLimitEvent={plan3} ok={ok3}",
            "PASS" if not ok3 else "FAIL",
        )

    os.environ.clear()
    os.environ.update(original)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
