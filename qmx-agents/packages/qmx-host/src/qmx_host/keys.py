"""The write-only key route (design 06 section 9, UI handoff section 26 gap 3): he types a key
once, QMX puts it in Credential Manager under its `qmx/` name, and nothing ever reads it back.

`PUT /api/keys/{name}` writes one `qmx/` name and answers 204; any other name answers 400 and
touches no credential, so the route cannot overwrite another program's entry. The names QMX makes
itself and the names a probe files (`qmx/read/`, `qmx/data/`, `qmx/token/`) are refused too, so a
key that can trade is never filed past its probe. `GET /api/keys` lists which names are set,
never a value: the declared registry `KEY_NAMES`, every `qmx/` name a place row refers to, and
every name this route wrote since the host started.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterable
from typing import Final

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from qmx_broker.credentials import CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, KeyStore
from qmx_home.rclone import CONFIG_KEY

KEY_NAMES: Final = (
    CTRADER_CLIENT_ID,
    CTRADER_CLIENT_SECRET,
    "qmx/firecrawl",
    "qmx/modal-token-id",
    "qmx/modal-token-secret",
    "qmx/e2b",
    "qmx/ctrader-mcp",
)
"""The keys he types, each a card of some kind: the cTrader app's id and secret, a provider's
key, the cTrader Remote MCP token. A storage's key is named by its place row (`credential_ref`)
or by the card that asks."""
MADE_BY_QMX: Final = frozenset({CONFIG_KEY, "qmx/control-token", "qmx/chatgpt"})
FILED: Final = ("qmx/read/", "qmx/data/", "qmx/token/")
NAME: Final = re.compile(r"qmx(/[A-Za-z0-9][A-Za-z0-9._-]{0,127}){1,4}")


class Value(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)


def refusal(name: str) -> str | None:
    """Why `name` may not be written through the route, or None."""
    if not NAME.fullmatch(name):
        return (
            f"{name!r} is not a key name QMX writes: use a qmx/ name such as "
            "qmx/ctrader-client-id; nothing was written"
        )
    if name in MADE_BY_QMX:
        return f"{name} is a key QMX makes and keeps itself; nothing was written"
    if name.startswith(FILED):
        return (
            f"{name} is filed only by its connection's check, which proves the key cannot trade; "
            "add the connection in Settings instead; nothing was written"
        )
    return None


def keys_router(store: KeyStore, referred: Callable[[], Iterable[str]] = tuple) -> APIRouter:
    """The key routes over `store`. `referred` names the `qmx/` keys the place rows refer to.
    The host's REST app puts both routes behind the bearer."""
    router = APIRouter(prefix="/api/keys")
    written: set[str] = set()
    lock = threading.Lock()

    def put(name: str, body: Value) -> Response:
        refused = refusal(name)
        if refused is not None:
            raise HTTPException(400, refused)
        store.replace(name, body.value)
        with lock:
            written.add(name)
        return Response(status_code=204)

    def listed() -> dict[str, object]:
        with lock:
            known = {*KEY_NAMES, *referred(), *written}
        names = sorted(n for n in known if NAME.fullmatch(n) and store.read(n) is not None)
        return {"set": names}

    router.add_api_route("/{name:path}", put, methods=["PUT"], status_code=204)
    router.add_api_route("", listed, methods=["GET"])
    return router
