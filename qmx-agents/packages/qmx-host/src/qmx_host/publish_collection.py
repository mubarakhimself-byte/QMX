"""`POST /api/library/collections/<id>/publish`: his one click publishes every item of a
collection (Part A LC-A1-14, slice A12), so the 239 ported dictionary drafts need one click, not
239.

Each member's draft goes through the Library's own per-item publish, `library_merge` of its
draft ref into `main`, the call his single publish makes, with its kind checks and its event. A
member whose `main` already holds its draft is left alone, so a second click publishes nothing
and writes nothing. A member that does not publish is named with its refusal, and the others
still publish. Only his own door may call it: every other principal, a chat's agent, a
workflow's run, the MCP client, an observer and a call no door named, is refused before
anything is read.
"""

from __future__ import annotations

from typing import Final, cast

from fastapi import APIRouter, HTTPException
from qmx_control.models import ControlError
from qmx_control.service import ControlService
from qmx_engine.control_door import PRINCIPAL
from qmx_library.port import LibraryRefused
from qmx_library.principal import MAIN, Principal, drafts_ref

OPERATOR: Final = Principal("operator")
COLLECTION: Final = "collection"
ROUTE: Final = "/api/library/collections/{collection_id}/publish"


def publish_collection(control: ControlService, collection_id: str) -> dict[str, object]:
    """Publish each member of the collection `collection_id` (its item or an object of it) in
    turn, and say which published, which `main` held already and which were refused."""
    store = control.library.store
    head = store.head(collection_id, MAIN)
    try:
        view = store.get(OPERATOR, collection_id if head is None else head[0])
    except LibraryRefused as error:
        raise HTTPException(404, f"no collection {collection_id}: {error}") from None
    if view.kind != COLLECTION:
        raise HTTPException(409, f"{collection_id} is a {view.kind}, not a collection")
    published: list[str] = []
    already: list[str] = []
    refused: list[dict[str, str]] = []
    for member in cast(list[object], view.fields.get("items") or []):
        item = str(member)
        draft, main = store.head(item, drafts_ref(item)), store.head(item, MAIN)
        if draft is None or (main is not None and main[0] == draft[0]):
            if main is None:
                refused.append({"item": item, "code": "no_draft", "message": "no draft to publish"})
            else:
                already.append(item)
            continue
        try:
            merged = control.library_merge(draft[0], from_ref=drafts_ref(item), into=MAIN)
        except ControlError as error:
            refused.append({"item": item, "code": error.code, "message": str(error)})
            continue
        if merged["outcome"] == "conflict":
            refused.append({"item": item, "code": "conflict", "message": "main moved past it"})
        else:
            published.append(item)
    return {
        "collection": view.item,
        "counts": {"published": len(published), "already": len(already), "refused": len(refused)},
        "published": published,
        "already": already,
        "refused": refused,
    }


def publish_collection_router(control: ControlService) -> APIRouter:
    router = APIRouter()

    @router.post(ROUTE)
    def publish(collection_id: str) -> dict[str, object]:
        caller = PRINCIPAL.get().principal
        if caller != OPERATOR.who:
            raise HTTPException(
                403,
                {
                    "refused": "principal",
                    "context": {
                        "why": "a collection publishes only by his click",
                        "caller": caller,
                    },
                },
            )
        return publish_collection(control, collection_id)

    _ = publish
    return router
