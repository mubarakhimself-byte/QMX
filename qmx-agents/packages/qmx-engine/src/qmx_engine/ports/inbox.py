"""The inbox port (SOLUTION-DESIGN 8.2, 10.4; AD-17 as ruling 77 narrowed it).

Only three kinds of trouble reach the operator, a closed set: a provider failure, a system fault
(a harness-level or engine-level error, or a crash loop: the engine dying mid-run again and
again), and an irreversible external step whose outcome is unknown. A run parked or paused for any
other reason (logic, bad input or output, a stuck agent, a limit he wrote) raises no item; its
state shows in `explain` and the run list. One item stands for every repeat of one failure in one
run: it is keyed by `(run_id, signature)` and counts its repeats. How an item is shown or sent
(toasts, phone, digest) is the UI's design.

His answer to an item is the run's next event: `resolve` records it on the item and hands it to
the engine, which writes `gate_resolved` naming the item's slot and wakes the run, and the core
folds it (AD-17, B-28, B-32). `open_trace` only opens the trace and writes nothing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal, Protocol

from pydantic import JsonValue


class Category(StrEnum):
    PROVIDER_FAILURE = "provider_failure"
    SYSTEM_FAULT = "system_fault"
    IRREVERSIBLE_EXTERNAL = "irreversible_external"


type Severity = Literal["normal", "urgent", "black"]
"""`info` never reaches the inbox; it goes to the daily digest."""
type Action = Literal["retry", "stronger_model", "skip_node", "open_trace", "stop", "resume"]

SEVERITY: Final[Mapping[Category, Severity]] = {
    Category.PROVIDER_FAILURE: "normal",
    Category.SYSTEM_FAULT: "urgent",
    Category.IRREVERSIBLE_EXTERNAL: "urgent",
}
ACTIONS: Final[Mapping[Category, tuple[Action, ...]]] = {
    Category.PROVIDER_FAILURE: ("retry", "stronger_model", "skip_node", "open_trace", "stop"),
    Category.SYSTEM_FAULT: ("retry", "open_trace", "stop", "resume"),
    Category.IRREVERSIBLE_EXTERNAL: ("retry", "skip_node", "open_trace", "stop"),
}
FAILURE_CODES: Final[Mapping[str, Category]] = {
    "auth": Category.PROVIDER_FAILURE,
    "accounts_closed": Category.PROVIDER_FAILURE,
    "harness_error": Category.SYSTEM_FAULT,
    "executor_error": Category.SYSTEM_FAULT,
    "no_executor": Category.SYSTEM_FAULT,
}
"""`node_failed` codes that raise an item: a provider's 401 and a role with every account closed
past `limits.alert_after`, and an error in the harness or in the engine's own code."""


@dataclass(frozen=True, slots=True)
class Raise:
    run_id: str
    signature: str
    category: Category
    title: str
    cause: str
    node_id: str | None = None
    severity: Severity | None = None
    """None takes the category's severity."""
    tried: tuple[str, ...] = ()
    idempotency_key: str | None = None
    blocks_run: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.category, Category):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"an inbox item's category is one of {[c.value for c in Category]}")


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    run_id: str
    signature: str
    category: Category
    severity: Severity
    title: str
    cause: str
    node_id: str | None
    tried: tuple[str, ...]
    idempotency_key: str | None
    blocks_run: bool
    actions: tuple[Action, ...]
    first_raised_at: str
    last_raised_at: str
    count: int
    resolved_by: str | None = None
    resolution: Action | None = None
    resolved_at: str | None = None


class InboxPort(Protocol):
    def raise_item(self, item: Raise, *, at: str) -> str:
        """Open the item, or count one more repeat of it; returns its id."""
        ...

    def resolve(self, item_id: str, action: Action, principal: str, *, at: str) -> Item:
        """Record his answer and hand it to the run."""
        ...

    def list_items(self, *, open_only: bool = True) -> list[Item]: ...


class Answers(Protocol):
    """Where a recorded answer goes: the engine, which writes `gate_resolved` through its one
    ledger writer and wakes the run."""

    def answer(self, item: Item, action: Action, principal: str, *, at: str) -> None: ...


class Recorded(Protocol):
    @property
    def kind(self) -> str: ...
    @property
    def data(self) -> Mapping[str, JsonValue]: ...


SLOT_KEYS: Final = ("node_id", "iteration", "partition", "attempt")


def answered(
    item: Item, action: Action, principal: str, events: Sequence[Recorded]
) -> dict[str, JsonValue]:
    """The `gate_resolved` an answer writes. It names the slot the item stands for: the gate that
    showed the item's idempotency key, else the node's last failure with the item's signature,
    else the node's last event. An item of the whole run names no slot."""
    node = item.node_id
    events = [e for e in events if all(key in e.data for key in SLOT_KEYS)]
    gates = [
        e.data
        for e in events
        if e.kind == "gate_opened" and e.data.get("idempotency_key") == item.idempotency_key
    ]
    failures = [
        e.data
        for e in events
        if e.kind == "node_failed"
        and e.data.get("node_id") == node
        and e.data.get("signature") == item.signature
    ]
    touched = [e.data for e in events if node is not None and e.data.get("node_id") == node]
    found = (gates if item.idempotency_key is not None else []) or failures or touched
    slot = {key: found[-1][key] for key in SLOT_KEYS} if found else {}
    return slot | {"answer": action, "principal": principal, "item_id": item.id}


def raised_by(
    run_id: str, kind: str, data: Mapping[str, JsonValue], tried: tuple[str, ...]
) -> Raise | None:
    """The item a ledger event raises, if any. `tried` is the failed slot's ladder so far."""
    node_id = data.get("node_id")
    node = node_id if isinstance(node_id, str) else None
    match kind:
        case "node_failed":
            code = str(data.get("code"))
            category = FAILURE_CODES.get(code)
            if category is None:
                return None
            return Raise(
                run_id,
                str(data.get("signature")),
                category,
                f"{node} failed: {code}",
                str(data.get("message")),
                node,
                tried=tried,
            )
        case "gate_opened" if data.get("category") == "irreversible_external":
            key = str(data.get("idempotency_key"))
            return Raise(
                run_id,
                key,
                Category.IRREVERSIBLE_EXTERNAL,
                f"{node} may have reached the outside world",
                str(data.get("ask")),
                node,
                tried=tried,
                idempotency_key=key,
                blocks_run=True,
            )
        case "ladder_step" if data.get("step") == "park" and "crash_loop" in data:
            reason = str(data.get("reason"))
            return Raise(
                run_id,
                "crash_loop",
                Category.SYSTEM_FAULT,
                "the engine keeps stopping during this run",
                reason,
                blocks_run=True,
            )
        case _:
            return None
