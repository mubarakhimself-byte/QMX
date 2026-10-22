"""`inbox.list` and `inbox.resolve` (SOLUTION-DESIGN 13). Listing is a read for every caller;
resolving is the operator's, from the UI, so an agent or a workflow is refused.

The merged read and the forwarded answer are AD-65's: this home's items and every owned instance's
arrive in one list, each naming its `home_engine`, and an answer for a node's item travels to the
node, whose own ledger folds it. This home never resolves another home's item itself.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from pydantic import JsonValue

from qmx_engine.ports.clock import Clock
from qmx_engine.ports.inbox import Action, InboxPort, Item
from qmx_engine.service.context import Caller, Refused
from qmx_engine.service.forward import Forwarder, ForwardRefused, Homerow, homerowed, plain


class Inbox:
    def __init__(
        self,
        port: InboxPort,
        clock: Clock,
        *,
        name: str = "pc",
        forwarders: Sequence[Forwarder] = (),
    ) -> None:
        self.port = port
        self.clock = clock
        self.name = name
        self.forwarders = tuple(forwarders)

    def list(self, *, open_only: bool = True) -> list[Item]:
        return self.port.list_items(open_only=open_only)

    def merged(self, *, open_only: bool = True) -> list[Homerow]:
        """This home's items and every owned instance's, each row naming its `home_engine`."""
        rows = [
            homerowed(self.name, cast("Mapping[str, JsonValue]", plain(item)))
            for item in self.list(open_only=open_only)
        ]
        for forwarder in self.forwarders:
            rows += forwarder.rows("inbox.list", {"open_only": open_only})
        return rows

    def resolve(self, item_id: str, action: Action, *, caller: Caller) -> Item:
        if caller.kind != "user":
            raise Refused("ui_only", "only the operator resolves an inbox item")
        return self.port.resolve(item_id, action, caller.principal, at=self.clock.now().isoformat())

    def answer_forwarded(self, item_id: str, action: Action, *, caller: Caller) -> JsonValue:
        """His answer to an item an owned node raised: that node's ledger folds it (AD-65)."""
        if caller.kind != "user":
            raise Refused("ui_only", "only the operator resolves an inbox item")
        for forwarder in self.forwarders:
            try:
                return forwarder.answer(item_id, action)
            except ForwardRefused as refused:
                if refused.code != "unknown_item":
                    raise Refused(refused.code, str(refused)) from refused
        raise Refused("unknown_item", f"no item {item_id} on any owned node")

    def incident(self, trigger_id: str) -> Homerow | None:
        """The open incident of one trigger, here or on the node whose engine fires it."""
        found = getattr(self.port, "open_incident", None)
        local = None if found is None else found(trigger_id)
        if local is not None:
            return homerowed(self.name, cast("Mapping[str, JsonValue]", plain(local)))
        for forwarder in self.forwarders:
            rows = forwarder.rows("incidents", {"trigger_id": trigger_id})
            if rows and not rows[0].stale and rows[0].row.get("id") is not None:
                return rows[0]
        return None
