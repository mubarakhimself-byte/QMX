"""`inbox.list` and `inbox.resolve` (SOLUTION-DESIGN 13). Listing is a read for every caller;
resolving is the operator's, from the UI, so an agent or a workflow is refused."""

from __future__ import annotations

from qmx_engine.ports.clock import Clock
from qmx_engine.ports.inbox import Action, InboxPort, Item
from qmx_engine.service.context import Caller, Refused


class Inbox:
    def __init__(self, port: InboxPort, clock: Clock) -> None:
        self.port = port
        self.clock = clock

    def list(self, *, open_only: bool = True) -> list[Item]:
        return self.port.list_items(open_only=open_only)

    def resolve(self, item_id: str, action: Action, *, caller: Caller) -> Item:
        if caller.kind != "user":
            raise Refused("ui_only", "only the operator resolves an inbox item")
        return self.port.resolve(item_id, action, caller.principal, at=self.clock.now().isoformat())
