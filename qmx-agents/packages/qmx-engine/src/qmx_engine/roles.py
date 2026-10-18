"""Roles, not models (AD-13, SOLUTION-DESIGN 9): a role's candidates in the order a run tries them.

A Settings row is `profile/model`, optionally `@effort`: `claude/haiku`,
`openrouter/moonshotai/kimi-k2.5`, `claude/opus@high`. A row with no model, such as `gpt`, names
no model the harness can run, so it is never resolved. `roles.test_only` lists the rows only a test
run may use, and only when the role names one itself: that is a provider-proof lane (ruling 105).
A test run builds its list by `roles.test_order`: those named test-only rows, then the plan's cheap
end (the role's own haiku row, else `claude/haiku`), then the role's other rows from the cheap end.
A live run sorts the role's rows by `roles.live_order` (key rows, then GPT, then the plan; ruling
107), keeping the role's order inside a class, and never takes a test-only row.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Final, Literal

from pydantic import JsonValue

from qmx_engine.settings import DEFAULTS

PLAN: Final = "claude"
"""The harness's plan profile."""
GPT: Final = "gpt"
"""The GPT plan lane's profile."""
EFFORTS: Final = frozenset({"low", "medium", "high", "xhigh", "max"})
CHEAPNESS: Final = ("haiku", "sonnet", "opus", "fable")
"""The plan's own tiers, cheapest first; any other model keeps its place after them."""
DEFAULT_WINDOW: Final = 200_000

type Mode = Literal["live", "test"]


@dataclass(frozen=True, slots=True)
class Candidate:
    profile: str
    model: str
    effort: str | None
    context_window: int
    test_only: bool

    @property
    def name(self) -> str:
        """The Settings row this candidate came from, as the run records it."""
        row = f"{self.profile}/{self.model}"
        return f"{row}@{self.effort}" if self.effort is not None else row

    def started(self, role: str) -> dict[str, JsonValue]:
        """What `node_started` records, so the attempt's span names the resolved candidate."""
        return {
            "role": role,
            "profile": self.profile,
            "model": self.model,
            "effort": self.effort,
            "candidate": self.name,
            "test_only": self.test_only,
        }


def parse(row: str, *, test_only: bool, window: int) -> Candidate | None:
    body, _, effort = row.partition("@")
    profile, _, model = body.partition("/")
    if not profile or not model or (effort and effort not in EFFORTS):
        return None
    return Candidate(profile, model, effort or None, window, test_only)


def _rows(settings: Mapping[str, object], key: str) -> tuple[str, ...]:
    found = settings.get(key)
    if isinstance(found, tuple | list):
        return tuple(r for r in found if isinstance(r, str))  # pyright: ignore[reportUnknownVariableType]
    return ()


def _cheapness(candidate: Candidate) -> int:
    tier = candidate.model.split("-")[0]
    return CHEAPNESS.index(tier) if tier in CHEAPNESS else len(CHEAPNESS)


def _steps(settings: Mapping[str, object], key: str) -> tuple[str, ...]:
    return _rows(settings, key) if key in settings else _rows(DEFAULTS, key)


def _live_class(candidate: Candidate) -> str:
    if candidate.profile == PLAN:
        return "plan"
    return "gpt" if candidate.profile == GPT else "key"


def order(settings: Mapping[str, object], role: str, mode: Mode) -> tuple[Candidate, ...]:
    """The role's candidates for a run in `mode`, in the order they are tried."""
    window = settings.get("context_window")
    window = window if isinstance(window, int) else DEFAULT_WINDOW
    flagged = set(_rows(settings, "roles.test_only"))
    rows = dict.fromkeys(_rows(settings, f"roles.{role}"))
    parsed = [parse(r, test_only=r in flagged, window=window) for r in rows]
    found = [c for c in parsed if c is not None]
    if mode == "live":
        classes = _steps(settings, "roles.live_order")
        rank = {name: i for i, name in enumerate(classes)}
        kept = (c for c in found if not c.test_only)
        return tuple(sorted(kept, key=lambda c: rank.get(_live_class(c), len(classes))))
    rest = sorted((c for c in found if not c.test_only), key=_cheapness)
    own = next((c for c in rest if c.profile == PLAN and _cheapness(c) == 0), None)
    plan_cheap = own or Candidate(PLAN, CHEAPNESS[0], None, window, test_only=False)
    steps = {
        "test_only": [c for c in found if c.test_only],
        "plan_cheap": [plan_cheap],
        "cheap": [c for c in rest if c is not own],
    }
    return tuple(c for step in _steps(settings, "roles.test_order") for c in steps.get(step, ()))


def resolve(
    candidates: tuple[Candidate, ...],
    profiles: Collection[str],
    ladder: Mapping[str, JsonValue] | None,
) -> Candidate | str:
    """The candidate an attempt runs on, or why there is none. The failure ladder's model rung
    names its candidate; otherwise the first whose profile the harness has. Under a runaway
    degrade the cheapest available one is taken."""
    ready = [c for c in candidates if c.profile in profiles]
    named = ladder.get("candidate") if ladder is not None else None
    if isinstance(named, str):
        chosen = next((c for c in candidates if c.name == named), None)
        if chosen is None:
            return f"the ladder's candidate {named} is not one of the role's candidates"
        if chosen.profile not in profiles:
            return f"the ladder's candidate {named} has no profile in the harness"
        return chosen
    if not ready:
        listed = ", ".join(c.name for c in candidates) or "none"
        return f"no candidate has a profile in the harness (candidates: {listed})"
    if ladder is not None and ladder.get("degrade") is True:
        return min(ready, key=_cheapness)
    return ready[0]
