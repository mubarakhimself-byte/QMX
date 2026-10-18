"""The inbox port (SOLUTION-DESIGN 8.2, 10.4; AD-17 as ruling 77 narrowed it).

Only three kinds of trouble reach the operator, a closed set: a provider failure, a system fault
(a harness-level or engine-level error), and an irreversible external step whose outcome is
unknown. A run parked for any other reason (logic, bad input or output, a runaway pause) raises no
item; its state shows in `explain` and the run list. One item stands for every repeat of one
failure in one run: it is keyed by `(run_id, signature)` and counts its repeats. How an item is
shown or sent (toasts, phone, digest) is the UI's design.
"""

from __future__ import annotations

from collections.abc import Mapping
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

    def resolve(self, item_id: str, action: Action, principal: str, *, at: str) -> Item: ...

    def list_items(self, *, open_only: bool = True) -> list[Item]: ...


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
        case _:
            return None
