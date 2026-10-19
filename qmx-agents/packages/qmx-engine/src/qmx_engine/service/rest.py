"""The engine's REST routes that `qmx_control.server.OPERATIONS` does not hold (SOLUTION-DESIGN 13):
resolving an inbox item, which is the operator's alone, a run's ledger events as SSE, and
`explain_trigger`, why a trigger did or did not fire.

The router is never added to `OPERATIONS`, so no agent tool reaches it (the harness checks that
list against its own tool table). `create_app(..., extra_routers=[engine_router(door)])` puts the
same bearer on it as on every other route.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Header, Query
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict
from qmx_control.models import Document

from qmx_engine.ports.inbox import Action

if TYPE_CHECKING:
    from qmx_engine.control_door import EngineDoor


class ResolveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Action


def engine_router(door: EngineDoor) -> APIRouter:
    router = APIRouter()

    @router.post("/api/inbox/{item_id}/resolve")
    def resolve(item_id: str, body: ResolveIn) -> Document:
        return door.inbox_resolve(item_id, body.action)

    @router.get("/api/engine/events", response_class=EventSourceResponse)
    async def events(
        run_id: str,
        last_event_id: Annotated[int, Header(ge=0)] = 0,
        after: Annotated[int, Query(ge=0)] = 0,
        max_events: Annotated[int, Query(ge=0, le=1000)] = 0,
    ) -> AsyncIterator[ServerSentEvent]:
        async for event in door.events(run_id, max(after, last_event_id), max_events):
            yield ServerSentEvent(data=event, event=str(event["kind"]), id=str(event["seq"]))

    @router.get("/api/triggers/{trigger_id}/explain")
    def explain_trigger(trigger_id: str) -> Document:
        return door.workflow_triggers_explain(trigger_id)

    _ = resolve, events, explain_trigger
    return router
