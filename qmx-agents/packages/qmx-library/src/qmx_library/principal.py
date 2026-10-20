"""Who is writing, and which refs each writer owns (Library AD-7).

A principal is derived once at the door and carried on every call. Each principal advances only
the refs it owns; `main` moves only by the operator's put of a record, by a merge (publishing)
or by the engine's landing rule (AD-18). An act names how a ref moves, because ownership differs
by act: an agent may merge into `refs/drafts/<item>` but never put onto it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from qmx_library.port import LibraryRefused

type Who = Literal["operator", "agent", "run", "engine", "hub", "migrator"]
type Act = Literal["put", "merge", "land", "state"]
"""`put` writes a new head; `merge` publishes or merges one ref into another; `land` is the
engine's standing-rule landing of a run's objects; `state` archives or restores an item."""

MAIN: Final = "main"
BARE: Final = frozenset({"operator", "hub", "migrator"})
NAMED: Final = frozenset({"agent", "run", "engine"})


@dataclass(frozen=True, slots=True)
class Principal:
    who: Who
    id: str | None = None

    @classmethod
    def parse(cls, text: str) -> Principal:
        """`operator | agent:<session_id> | run:<run_id> | engine:<store> | hub | migrator`."""
        who, sep, name = text.partition(":")
        if who in BARE and not sep:
            return cls(who)  # pyright: ignore[reportArgumentType]
        if who in NAMED and name and "/" not in name:
            return cls(who, name)  # pyright: ignore[reportArgumentType]
        raise LibraryRefused("ref_not_owned", f"{text!r} is not a principal")

    def __str__(self) -> str:
        return self.who if self.id is None else f"{self.who}:{self.id}"


def agent_ref(session_id: str, item: str) -> str:
    return f"refs/agents/{session_id}/{item}"


def drafts_ref(item: str) -> str:
    return f"refs/drafts/{item}"


def runs_ref(run_id: str) -> str:
    return f"refs/runs/{run_id}"


def sessions_ref(session_id: str) -> str:
    """Where the host's session recorder writes a chat's `session` item before landing it."""
    return f"refs/sessions/{session_id}"


def state_ref(item: str) -> str:
    return f"refs/items/{item}/state"


def may_advance(principal: Principal, ref: str, act: Act, *, store: str) -> bool:
    """Whether `principal` may move `ref` by `act` on the store named `store`."""
    who, name = principal.who, principal.id
    engine = who == "engine" and name == store
    parts = ref.split("/")
    if ref == MAIN:
        return (
            who == "operator" or (engine and act == "land") or (who == "agent" and act == "merge")
        )
    if len(parts) < 3 or parts[0] != "refs":
        return False
    space, rest = parts[1], parts[2:]
    match space:
        case "drafts" if len(rest) == 1:
            return (
                who == "operator"
                or (engine and act == "land")
                or (who == "agent" and act == "merge")
            )
        case "variants" if len(rest) == 1:
            return who == "operator"
        case "items" if len(rest) == 2 and rest[1] == "state":
            return act == "state" and (who == "operator" or engine)
        case "agents" if len(rest) == 2:
            return who == "agent" and rest[0] == name
        case "runs" if len(rest) == 1:
            return who == "run" and rest[0] == name
        case "sessions" if len(rest) == 1:
            return engine
        case "memory" | "champions" | "challengers":
            return engine
        case "hub":
            return who == "hub"
        case _:
            return False


def own_ref(principal: Principal, item: str, ref: str) -> str:
    """The ref `principal` writes its working copy of `item` to when it checks out `ref`: its
    own agent or run ref, or `ref` itself for the operator and the engine."""
    match principal.who:
        case "agent":
            return agent_ref(str(principal.id), item)
        case "run":
            return runs_ref(str(principal.id))
        case _:
            return ref
