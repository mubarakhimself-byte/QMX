"""EP10 lane 3 (E9): a role's first candidate runs; once it is unavailable, the next run takes the
second.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e09_roles.py`
Writes `evidence/ep10/<ENGINE_LOG_PREFIX>ep10-e09.log`. `writer` lists the OpenRouter row first and
the plan's `claude/haiku` second. Under the lane lock on the ship home, the OpenRouter row is added
to `[providers]` and one test run of a `writer` node goes; then the row is taken out again, which
makes that candidate unavailable, and a second run goes. `[providers]` is put back as found. The
engine's own ledger lives on a throwaway home. Plan turns: at most one meter turn (HG2) and one or
two haiku turns.
"""

from __future__ import annotations

import asyncio

from common import Log, boot, plan_harness, throwaway_home
from llm_lanes import KIMI, KIMI_ROW, OPENROUTER_ROW, PR, describe, folder, model_spans, run
from qmx_engine.settings import DEFAULTS

SETTINGS = {**DEFAULTS, "roles.writer": (KIMI_ROW, "claude/haiku")}


async def main() -> int:
    log = Log(PR, "ep10-e09")
    boot()
    workflow = folder("e09", role="writer")
    engine_home = throwaway_home(PR, "e09")
    async with plan_harness(log) as found:
        control = found.control
        rows = dict(control.settings_get("providers"))
        log(f"ship home [providers] as found: {sorted(rows)}")
        try:
            control.settings_put("providers", rows | {"openrouter": OPENROUTER_ROW})
            first, _, first_spans, _ = await run(engine_home, workflow, found.harness, SETTINGS)
            log(f"run 1 {first.run_id}: {first.status} {first.reason or ''}")
            control.settings_put("providers", {k: v for k, v in rows.items() if k != "openrouter"})
            log(f"run 2 with [providers] {sorted(control.settings_get('providers'))}")
            second, _, second_spans, _ = await run(engine_home, workflow, found.harness, SETTINGS)
            log(f"run 2 {second.run_id}: {second.status} {second.reason or ''}")
        finally:
            control.settings_put("providers", rows)
            log(f"ship home [providers] restored: {sorted(control.settings_get('providers'))}")
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
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
