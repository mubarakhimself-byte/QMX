"""EP10 lane 3 (E9): a role's first candidate runs; where it is unavailable, the run takes the
second.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e09_roles.py`
Writes `evidence/ep10/<ENGINE_LOG_PREFIX>ep10-e09.log`. `writer` lists the OpenRouter row first and
the plan's `claude/haiku` second, in test mode. Run 1 goes on a throwaway home that has the
OpenRouter row, and its span must record it. Run 2 goes on the ship home under the lane lock, as it
is: it has no OpenRouter profile, so that candidate is unavailable and the span must record
`claude/haiku`.
No lane edits the ship home's config; its `settings.toml` is hashed before and after and must not
change. Plan turns: at most one meter turn (HG2) and one or two haiku turns.
"""

from __future__ import annotations

import asyncio
import hashlib

from common import SHIP_HOME, Log, boot, plan_harness, throwaway_home
from llm_lanes import (
    KIMI,
    KIMI_ROW,
    PR,
    describe,
    folder,
    harnessed,
    model_spans,
    openrouter_home,
    relay_usd,
    run,
)
from qmx_engine.settings import DEFAULTS

SETTINGS = {**DEFAULTS, "roles.writer": (KIMI_ROW, "claude/haiku")}
SHIP_SETTINGS = SHIP_HOME / "settings.toml"


def sha(text: bytes) -> str:
    return hashlib.sha256(text).hexdigest()


async def main() -> int:
    log = Log(PR, "ep10-e09")
    boot()
    before = sha(SHIP_SETTINGS.read_bytes())
    log(f"ship home settings.toml sha256 before: {before}")
    workflow = folder("e09", role="writer")
    keyed = openrouter_home("e09-openrouter")
    async with harnessed(keyed) as found:
        log(f"throwaway home [providers]: {sorted(found.control.settings_get('providers'))}")
        first, _, first_spans, _ = await run(
            throwaway_home(PR, "e09-engine-1"), workflow, found.harness, SETTINGS
        )
    log(f"run 1 {first.run_id}: {first.status} {first.reason or ''}")
    async with plan_harness(log) as found:
        log(f"ship home [providers], read only: {sorted(found.control.settings_get('providers'))}")
        second, _, second_spans, _ = await run(
            throwaway_home(PR, "e09-engine-2"), workflow, found.harness, SETTINGS
        )
    log(f"run 2 {second.run_id}: {second.status} {second.reason or ''}")
    after = sha(SHIP_SETTINGS.read_bytes())
    log(f"ship home settings.toml sha256 after: {after}")
    one, two = model_spans(first_spans), model_spans(second_spans)
    for span in (*one, *two):
        log(f"span {describe(span)}")
    log.check(
        "the first run's span records the OpenRouter row",
        first.status == "passed" and [(s.profile, s.model) for s in one] == [("openrouter", KIMI)],
        [(s.profile, s.model, s.status) for s in one],
    )
    log.check(
        "with the OpenRouter row unavailable the next run records the plan candidate",
        second.status == "passed" and [(s.profile, s.model) for s in two] == [("claude", "haiku")],
        [(s.profile, s.model, s.status) for s in two],
    )
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(keyed):.4f}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
