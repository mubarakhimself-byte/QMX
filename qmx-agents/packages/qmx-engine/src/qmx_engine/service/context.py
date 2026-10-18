"""What every service call shares: the caller, the refusal, the AD-11 lifecycle table and the ports.

A caller is `user | agent | workflow` and writes to the Library as `operator`, `agent:<sid>` or
`run:<run_id>` (27b S17). The lifecycle is `draft -> validated -> tested -> published -> enabled <->
disabled -> archived` (SOLUTION-DESIGN 6.1). States are derived on every call, never stored: a
draft's from its validation and its test reports, a version's from its Library annotations.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from qmx_engine.definition.validate import NOT_ROLES
from qmx_engine.ports.clock import Clock
from qmx_engine.ports.inbox import InboxPort
from qmx_engine.ports.library import LibraryPort
from qmx_engine.ports.settings import SettingsPort
from qmx_engine.runner import Engine

type CallerKind = Literal["user", "agent", "workflow"]
type State = Literal["draft", "validated", "tested", "published", "enabled", "disabled", "archived"]
type Act = Literal["edit", "validate", "test", "publish", "enable", "disable", "archive", "run"]

DRAFT_STATES: Final = frozenset({"draft", "validated", "tested"})
ALLOWED: Final[Mapping[State, frozenset[Act]]] = {
    "draft": frozenset({"edit", "validate", "test"}),
    "validated": frozenset({"edit", "validate", "test"}),
    "tested": frozenset({"edit", "validate", "test", "publish"}),
    "published": frozenset({"enable", "archive", "run"}),
    "enabled": frozenset({"disable", "run"}),
    "disabled": frozenset({"enable", "archive", "run"}),
    "archived": frozenset(),
}
"""What each state allows. A live run (`run`) takes published versions only (AD-11)."""


class Refused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def require(state: State, act: Act, what: str) -> None:
    if act not in ALLOWED[state]:
        raise Refused(f"{act}_refused", f"{what} is {state}; {act} is not allowed from {state}")


@dataclass(frozen=True, slots=True)
class Caller:
    kind: CallerKind
    id: str | None = None
    """The session id of an agent, the run id of a workflow."""

    @property
    def principal(self) -> str:
        match self.kind:
            case "user":
                return "operator"
            case "agent":
                return f"agent:{self.id}"
            case "workflow":
                return f"run:{self.id}"


OPERATOR: Final = Caller("user")


@dataclass(frozen=True, slots=True)
class Context:
    home: Path
    library: LibraryPort
    inbox: InboxPort
    settings: SettingsPort
    clock: Clock
    engine: Engine

    def at(self) -> str:
        return self.clock.now().isoformat()

    def roles(self) -> frozenset[str]:
        return frozenset(
            role
            for key in self.settings.values()
            if key.startswith("roles.") and (role := key.removeprefix("roles.")) not in NOT_ROLES
        )
