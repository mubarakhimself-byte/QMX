"""S37, effort change, on the fake model. An Interactive key chat starts at effort `low`; a Python
`Stop` hook added to every launch records `effort.level` from each turn's hook input, as HP0
measured it. After one turn, effort is quoted to `high` and applied.

PASS when the quote's only step is `set_effort`, apply sends `/effort high` into the same CLI
(no second launch), and the turn after the change reports `high` in its hook input and in the
model request's `output_config.effort`, where the turn before reported `low`.

    s37_effort.py
"""

from __future__ import annotations

import asyncio
import dataclasses
import sys
from typing import Any

from common import Log, boot, use_fake_home, use_fake_key
from switch_lane import apply, fake_pair, quote


def record_effort(levels: list[str | None]) -> None:
    """Every launch from now on carries a `Stop` hook that appends the turn's effort level."""
    import qma.harness.chat as chat_module  # noqa: PLC0415
    from claude_agent_sdk import HookMatcher  # noqa: PLC0415

    async def stop(input_data: Any, _tool_use_id: Any, _context: Any) -> dict[str, Any]:
        effort = input_data.get("effort")
        levels.append(effort.get("level") if isinstance(effort, dict) else None)
        return {}

    base = chat_module.ClaudeSDKClient

    class Hooked(base):
        def __init__(self, options: Any) -> None:
            hooks = dict(options.hooks or {})
            hooks["Stop"] = [*hooks.get("Stop", []), HookMatcher(matcher=None, hooks=[stop])]
            super().__init__(dataclasses.replace(options, hooks=hooks))

    chat_module.ClaudeSDKClient = Hooked


async def run(log: Log) -> None:
    levels: list[str | None] = []
    record_effort(levels)
    fake, session, launched = await fake_pair(log, "hp12-s37", [], tools=[], effort="low")
    try:
        await session.turn(log, "Say first.")
        before = list(levels)
        found = await quote(log, session, effort="high")
        log.check(
            "the quote's only step is set_effort",
            [step.value for step in found.steps] == ["set_effort"],
            [step.value for step in found.steps],
        )
        await apply(log, session, found.id)
        log(f"effort levels at Stop so far: {levels}")
        await session.turn(log, "Say second.")
        after = levels[len(before) :]
        log(f"Stop effort before the change {before}, after it {after}")
        log.check("one CLI launch, no relaunch", len(launched) == 1, len(launched))
        log.check(
            "the turn before reported low and the next turn reports high",
            before[-1:] == ["low"] and after[-1:] == ["high"],
            (before, after),
        )
        sent = [
            seen.json.get("output_config", {}).get("effort")
            for seen in fake.requests
            if seen.path == "/v1/messages"
        ]
        log(f"output_config.effort per model request: {sent}")
        log.check(
            "the model request after the change carries effort high",
            sent[:1] == ["low"] and sent[-1:] == ["high"],
            sent,
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp12-s37")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
