"""Every engine default, in one place (ENGINE-PLAN Appendix H).

Each value is Claude's default, not the operator's, and every one is editable from the UI. Keys
are dotted Settings paths. `*` in a `pool.accounts` key stands for any account. Durations are in
seconds, fractions are of a model's context window or of an account's plan window, and a role's
candidates are `profile/model` rows in the order they are tried. `generated` builds those lists from
the model registry's rows (RTR5, AD-13, AD-39): one list per role from its class, key rows first
with the Chinese models leading every tier (ruling 107), then GPT, then the plan, and no list names
Fable. The tables below are the bundled registry's example rows, so the defaults document
SOLUTION-DESIGN section 9 until a host has a registry to generate from; a row with no model id
(`glm`, `qwen`, `gpt`) keeps its place and is never resolved until the registry names its model.
`roles.live_order` is the class order a live run sorts by. `roles.test_order` is how a test run
builds its list: test-only rows the role names itself (a provider-proof lane), then the plan's
cheap end `claude/haiku` (ruling 105), then the role's other rows from the cheap end.

QMX sets no usage limit of its own (ruling 106, AD-40): there is no runaway guard, no turn,
tool-call or run-time ceiling and no background share here. `timeout.*` and `loop.*` feed the stuck
detector, which asks whether an attempt still moves, never how much it used. `placement.pc.*_slots`
are machine capacity per resource class (AD-58); chat slots and the Interactive reserve live in the
harness slot table, the only chat-slot counter, under `[budgets]`.

`autonomy.paused` is the local "pause everything" flag (AD-65): while it is set no fire is claimed
and no live run starts a node; OPS2 makes the Hub's copy authoritative. `triggers.rerun_delays`
are the spend-neutral re-runs after a failed fire, counted from its first failure.
`triggers.precheck_timeout` bounds a trigger's own check script, which is not a node. The
`market_open` precheck holds a fire on weekends and `market.holidays` in the trigger's zone.

The place list (AD-30, AD-72) is `pc`, built in, plus every name he gives a `placement.<name>.*`
row. No other row ships here: a place is one he adds, under whatever name he typed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

from qmx_router import agents

from qmx_engine.ports.router import Row

type Setting = int | float | str | tuple[int, ...] | tuple[str, ...] | None

PC: Final = "pc"
"""This PC: the one built-in place, always in the list and the default of every choice."""


def place_of(key: str) -> str | None:
    """The place a `placement.<name>.<field>` key belongs to, or None for any other key."""
    parts = key.split(".")
    if len(parts) == 3 and parts[0] == "placement" and parts[1] and parts[2]:
        return parts[1]
    return None


def can_run(settings: Mapping[str, object], name: str) -> bool:
    """Whether the place `name` can run work: its `placement.<name>.can` holds `run`. A row that
    names no `can` runs, as every row did before storages joined the list (design 06 section 4);
    a storage's row says `can = ["keep"]`."""
    can = settings.get(f"placement.{name}.can")
    if can is None:
        return True
    if isinstance(can, str):
        return can == "run"
    return isinstance(can, list | tuple) and "run" in can


def places(settings: Mapping[str, object]) -> dict[str, str]:
    """The places work can run at, as `name -> id`: This PC, then every name with a
    `placement.<name>.*` row that can run. A row's stable `id` is its `placement.<name>.id`, so
    renaming a place keeps its history; a row that names none is known by its name."""
    found = {PC: PC}
    for key in settings:
        name = place_of(key)
        if name is not None and can_run(settings, name):
            stable = settings.get(f"placement.{name}.id")
            found.setdefault(name, stable if isinstance(stable, str) and stable else name)
    return found


ROLE_TIERS: Final[Mapping[str, str]] = MappingProxyType(
    {**agents.ROLE_TIERS, "memory_extractor": "mid"}
)
"""Each role's class, from the router, which owns the table its sub-agents are generated from,
plus `memory_extractor`: Hindsight's own extraction and reflection calls (AD-18, §28.6), an
engine role with no sub-agent, whose grant goes through the router's key lane so the memory
engine never holds a provider key."""
CHINESE: Final = frozenset({"kimi", "moonshot", "deepseek", "glm", "zai", "qwen", "minimax"})
"""The profiles whose models lead every tier (ruling 107)."""
BUNDLED_ROWS: Final = (
    Row("kimi/k2.7-code", "kimi", "k2.7-code", "cheap", 256_000),
    Row("deepseek", "deepseek", "", "cheap", 128_000),
    Row("minimax/MiniMax-M2.7-highspeed", "minimax", "MiniMax-M2.7-highspeed", "cheap", 200_000),
    Row("qwen", "qwen", "", "cheap", 200_000),
    Row("gpt", "gpt", "", "cheap"),
    Row("claude/haiku", "claude", "haiku", "cheap"),
    Row("glm", "glm", "", "mid"),
    Row("qwen", "qwen", "", "mid"),
    Row("deepseek", "deepseek", "", "mid"),
    Row("kimi", "kimi", "", "mid"),
    Row("gpt", "gpt", "", "mid"),
    Row("claude/sonnet", "claude", "sonnet", "mid"),
    Row("kimi/k3", "kimi", "k3", "strong", 1_000_000),
    Row("deepseek/deepseek-v4-pro", "deepseek", "deepseek-v4-pro", "strong", 256_000),
    Row("glm", "glm", "", "strong"),
    Row("qwen", "qwen", "", "strong"),
    Row("gpt", "gpt", "", "strong"),
    Row("claude/opus", "claude", "opus", "strong"),
)
"""The bundled registry's example rows, by class, in SOLUTION-DESIGN section 9's order."""


def _lane(row: Row) -> tuple[int, int]:
    """Key rows before GPT before the plan, Chinese rows first inside a lane, registry order
    inside a group (ruling 107)."""
    lane = {"claude": 2, "gpt": 1}.get(row.profile, 0)
    return lane, 0 if row.profile in CHINESE else 1


def generated(rows: Sequence[Row]) -> Mapping[str, tuple[str, ...]]:
    """Every role's candidate rows, from the registry's rows by class: his configured providers,
    key rows first with the Chinese rows leading every tier, then GPT, then the plan. A
    provider-proof row is never generated; only a role that names it may use it."""
    found: dict[str, tuple[str, ...]] = {}
    for role, tier in ROLE_TIERS.items():
        chosen = sorted(
            (row for row in rows if row.class_ == tier and not row.test_only), key=_lane
        )
        found[f"roles.{role}"] = tuple(dict.fromkeys(row.qmx_id for row in chosen))
    return found


_BUNDLED: Final = generated(BUNDLED_ROWS)
_CHEAP: Final = _BUNDLED["roles.triage"]
_MID: Final = _BUNDLED["roles.reader"]
_STRONG: Final = _BUNDLED["roles.planner"]

DEFAULTS: Final[Mapping[str, Setting]] = MappingProxyType(
    {
        "scheduler.tick": 60,  # Claude's default, UI-editable
        "scheduler.lease_seconds": 300,  # Claude's default, UI-editable
        "scheduler.heartbeat": 60,  # Claude's default, UI-editable
        "scheduler.grace": 900,  # Claude's default, UI-editable
        "autonomy.paused": 0,  # Claude's default, UI-editable; 1 or true pauses every fire
        "triggers.rerun_delays": (300, 900, 1_800),  # Claude's default, UI-editable
        "triggers.ready_by_window": 3_600,  # Claude's default, UI-editable
        "triggers.precheck_timeout": 600,  # Claude's default, UI-editable; a check, not a node
        "triggers.webhook_home": PC,  # Claude's default, UI-editable; any place in the list
        "market.holidays": (),  # Claude's default, UI-editable; local dates, YYYY-MM-DD
        "limits.slack": 60,  # Claude's default, UI-editable
        "limits.alert_after": 21_600,  # Claude's default, UI-editable
        "chunk.size": 10,  # Claude's default, UI-editable
        "chunk.fill": 0.3,  # Claude's default, UI-editable
        "agent.compact_at": 0.4,  # Claude's default, UI-editable
        "pool.accounts.*.ceiling": None,  # Claude's default, UI-editable
        "pool.accounts.*.cooldown": 300,  # Claude's default, UI-editable
        "pool.strategy": "least_used",  # Claude's default, UI-editable
        "retry.max_tries": 3,  # Claude's default, UI-editable
        "retry.backoff": (30, 120, 600),  # Claude's default, UI-editable
        "timeout.agent.idle": 300,  # Claude's default, UI-editable
        "timeout.script.idle": 600,  # Claude's default, UI-editable
        "timeout.in_tool": 1_200,  # Claude's default, UI-editable
        "timeout.grace": 120,  # Claude's default, UI-editable
        "timeout.warn_at": 0.8,  # Claude's default, UI-editable
        "loop.repeat": 5,  # Claude's default, UI-editable
        "loop.window": 8,  # Claude's default, UI-editable
        "loop.no_convergence": 6,  # Claude's default, UI-editable
        "crash_loop.restarts": 3,  # Claude's default, UI-editable
        "subworkflow.max_depth": 3,  # Claude's default, UI-editable
        "inline_limit_bytes": 65_536,  # Claude's default, UI-editable
        "placement.pc.cpu_slots": None,  # Claude's default, UI-editable; unset is cores minus one
        "placement.pc.container_slots": 3,  # Claude's default, UI-editable
        "placement.pc.gpu_slots": 1,  # Claude's default, UI-editable; the one Quadro T1000 (DR13)
        "context_window": 200_000,  # Claude's default, UI-editable
        "roles.triage": _CHEAP,  # Claude's default, UI-editable
        "roles.clarifier": _CHEAP,  # Claude's default, UI-editable
        "roles.scanner": _CHEAP,  # Claude's default, UI-editable
        "roles.doctor": _CHEAP,  # Claude's default, UI-editable
        "roles.judge": _CHEAP,  # Claude's default, UI-editable
        "roles.reader": _MID,  # Claude's default, UI-editable
        "roles.searcher": _MID,  # Claude's default, UI-editable
        "roles.writer": _MID,  # Claude's default, UI-editable
        "roles.extractor": _MID,  # Claude's default, UI-editable
        "roles.memory_extractor": _MID,  # Claude's default, UI-editable; Hindsight's extractor
        "roles.planner": _STRONG,  # Claude's default, UI-editable
        "roles.synthesiser": _STRONG,  # Claude's default, UI-editable
        "roles.builder": _STRONG,  # Claude's default, UI-editable
        "roles.reviewer": _STRONG,  # Claude's default, UI-editable
        "roles.test_only": ("openrouter/moonshotai/kimi-k2.5",),  # Claude's default, UI-editable
        "roles.test_order": ("test_only", "plan_cheap", "cheap"),  # Claude's default, UI-editable
        "roles.live_order": ("key", "gpt", "plan"),  # Claude's default, UI-editable
    }
)
