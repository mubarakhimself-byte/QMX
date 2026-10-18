"""HYG0 lane 3 (E9 under ruling 105): in test mode every default role resolves the plan's
`claude/haiku` first, one haiku turn answers, and a role whose first candidate is unavailable takes
the next.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e09_roles.py`
Writes `evidence/ep10/<ENGINE_LOG_PREFIX>ep10-e09.log`. Everything runs on the ship home under the
lane lock, as it is. Resolution is timed three times over all roles (HYG0's perf probe). A
`writer` list that names the OpenRouter row first resolves past it, because the ship home has no
OpenRouter profile; no OpenRouter call is made here (the provider proof is `llm_lanes.py`).
No lane edits the ship home's config; its `settings.toml` is hashed before and after and must not
change. Plan turns: at most one meter turn (HG2) and one haiku turn.
"""

from __future__ import annotations

import asyncio
import hashlib
import time

from common import SHIP_HOME, Log, boot, plan_harness, throwaway_home
from llm_lanes import KIMI_ROW, PR, describe, folder, model_spans, run
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.roles import Candidate, order, resolve
from qmx_engine.settings import DEFAULTS

ORDER_KEYS = frozenset({"roles.test_only", "roles.test_order", "roles.live_order"})
ROLES = tuple(
    k.removeprefix("roles.") for k in DEFAULTS if k.startswith("roles.") and k not in ORDER_KEYS
)
NAMED = {**DEFAULTS, "roles.writer": (KIMI_ROW, *DEFAULTS["roles.writer"])}  # type: ignore[misc]
SHIP_SETTINGS = SHIP_HOME / "settings.toml"


def sha(text: bytes) -> str:
    return hashlib.sha256(text).hexdigest()


def first_of_every_role(profiles: frozenset[str]) -> dict[str, Candidate | str]:
    return {role: resolve(order(DEFAULTS, role, "test"), profiles, None) for role in ROLES}


async def main() -> int:
    log = Log(PR, "ep10-e09")
    boot()
    before = sha(SHIP_SETTINGS.read_bytes())
    log(f"ship home settings.toml sha256 before: {before}")
    async with plan_harness(log) as found:
        profiles = HarnessAdapter(found.harness).profiles()
        log(f"ship home profiles, read only: {sorted(profiles)}")
        timings = []
        for _ in range(3):
            began = time.perf_counter()
            firsts = first_of_every_role(profiles)
            timings.append((time.perf_counter() - began) * 1000)
        for role, chosen in firsts.items():
            log(f"role {role}: first resolved {getattr(chosen, 'name', chosen)}")
        log(f"perf: resolution of {len(ROLES)} roles, ms per pass: {[f'{t:.3f}' for t in timings]}")
        named = order(NAMED, "writer", "test")
        skipped = resolve(named, profiles, None)
        log(f"writer naming {KIMI_ROW} first: candidates {[c.name for c in named]}")
        outcome, _, spans, _ = await run(
            throwaway_home(PR, "e09-engine"), folder("e09", role="writer"), found.harness, DEFAULTS
        )
    log(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}")
    after = sha(SHIP_SETTINGS.read_bytes())
    log(f"ship home settings.toml sha256 after: {after}")
    turns = model_spans(spans)
    for span in turns:
        log(f"span {describe(span)}")
    log.check(
        "every default role resolves claude/haiku on the plan profile first in test mode",
        all(
            isinstance(c, Candidate) and (c.profile, c.model) == ("claude", "haiku")
            for c in firsts.values()
        )
        and len(firsts) == 13,
        {r: getattr(c, "name", c) for r, c in firsts.items()},
    )
    log.check(
        "one haiku turn answers on the plan for the default writer list",
        outcome.status == "passed"
        and [(s.profile, s.model, s.status) for s in turns] == [("claude", "haiku", "ok")],
        [(s.profile, s.model, s.status, s.tokens) for s in turns],
    )
    log.check(
        "with the named OpenRouter row unavailable the writer resolves the plan candidate",
        isinstance(skipped, Candidate) and skipped.name == "claude/haiku",
        getattr(skipped, "name", skipped),
    )
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
