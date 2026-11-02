"""The ported dictionary in the Library (Part A A12, AD-114, LC-A1-14): a start lands its 239
drafts in one collection once per store, and only his click publishes the collection, each item
through the per-item publish. Every folder is in pytest's tmp folder; no host process starts."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import JsonValue
from qmx_control.models import ControlError
from qmx_control.service import ControlService
from qmx_engine.control_door import PRINCIPAL, UNNAMED
from qmx_engine.service.context import Caller
from qmx_home import resolve
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store
from qmx_tools.functions import write_entry_statuses
from qmx_tools.gather import template
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_host.first_start import PORT_SEED, land_port
from qmx_host.host import land_ported_dictionary, open_store, register_checkers
from qmx_host.publish_collection import publish_collection_router

OPERATOR = Principal("operator")
PORT = cast(dict[str, Any], json.loads((PORT_SEED / "port.json").read_text("utf-8")))
COLLECTION = str(PORT["collection"]["item"])
ITEMS = [str(d["item"]) for d in PORT["drafts"]]


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as opened:
        register_checkers(opened)
        yield opened


def as_caller(app: ASGIApp, caller: Caller) -> ASGIApp:
    """The app as a door that named `caller` serves it."""

    async def served(scope: Scope, receive: Receive, send: Send) -> None:
        token = PRINCIPAL.set(caller)
        try:
            await app(scope, receive, send)
        finally:
            PRINCIPAL.reset(token)

    return served


def on_main(store: Store) -> int:
    return sum(store.head(item, MAIN) is not None for item in ITEMS)


def test_a_start_lands_the_239_drafts_in_one_collection_once(store: Store) -> None:
    land_ported_dictionary(store)
    before = store.refs()
    land_ported_dictionary(store)

    collection = store.get(OPERATOR, cast(tuple[str, int], store.head(COLLECTION, MAIN))[0])
    statuses = [c.annotation()["value"] for _, _, c in write_entry_statuses(store)]
    assert (collection.kind, len(cast(list[str], collection.fields["items"]))) == (
        "collection",
        239,
    )
    assert (store.refs() == before, on_main(store)) == (True, 0)
    assert (len(statuses), set(statuses)) == (239, {"named"})
    assert len(store.with_field("component", "entry.origin", "port-239")) == 239


def test_a_landing_cut_short_finishes_and_keeps_his_edit(store: Store) -> None:
    first = PORT["drafts"][0]
    edited = {**first["fields"], "entry": {**first["fields"]["entry"], "boundaries": "his words"}}
    item = str(first["item"])
    store.put(
        OPERATOR,
        Draft("component", item, "his", fields=edited),
        on=drafts_ref(item),
        expected_head=None,
    )

    landed = land_port(store)

    kept = store.get(OPERATOR, cast(tuple[str, int], store.head(item, drafts_ref(item)))[0])
    assert (str(landed), land_port(store)) == (
        f"238 drafts landed and 1 kept in collection {COLLECTION}",
        None,
    )
    assert cast(dict[str, object], kept.fields["entry"])["boundaries"] == "his words"


def test_only_his_click_publishes_the_collection_and_a_second_click_changes_nothing(
    tmp_path: Path, store: Store
) -> None:
    land_port(store)
    control = ControlService(
        resolve(tmp_path / "QMX", create=True).home, secret_getter=lambda _s, _n: None
    )
    control.attach_library(store)
    app = FastAPI()
    app.include_router(publish_collection_router(control))
    route = f"/api/library/collections/{COLLECTION}/publish"
    others = [
        Caller("agent", "x"),
        Caller("workflow", "run-1"),
        Caller("agent", "mcp"),
        Caller("agent", "observer:o"),
        UNNAMED,
    ]

    refused = [TestClient(as_caller(app, c)).post(route) for c in others]
    nothing = on_main(store)
    first = TestClient(as_caller(app, Caller("user"))).post(route).json()
    after = store.refs()
    second = TestClient(as_caller(app, Caller("user"))).post(route).json()

    assert [r.status_code for r in refused] == [403] * 5
    assert [r.json()["detail"]["context"]["caller"] for r in refused] == [
        "agent:x",
        "run:run-1",
        "agent:mcp",
        "agent:observer:o",
        "agent:unnamed",
    ]
    assert (nothing, first["counts"], on_main(store)) == (
        0,
        {"published": 239, "already": 0, "refused": 0},
        239,
    )
    assert (second["counts"], store.refs() == after) == (
        {"published": 0, "already": 239, "refused": 0},
        True,
    )
    mains = [cast(tuple[str, int], store.head(i, MAIN))[0] for i in ITEMS]
    assert mains == [cast(tuple[str, int], store.head(i, drafts_ref(i)))[0] for i in ITEMS]


def test_a_member_his_single_publish_refuses_is_refused_with_the_same_words(
    tmp_path: Path, store: Store
) -> None:
    unit = cast(dict[str, JsonValue], template())
    cast(dict[str, dict[str, object]], unit["numbers"])["ema_period"]["default"] = "500"
    store.put(
        OPERATOR, Draft("unit", "u-1", "u", fields=unit), on=drafts_ref("u-1"), expected_head=None
    )
    first = PORT["drafts"][0]
    store.put(
        OPERATOR,
        Draft("component", first["item"], "e", fields=first["fields"]),
        on=drafts_ref(first["item"]),
        expected_head=None,
    )
    members = Draft("collection", "c-1", "c", fields={"items": ["u-1", first["item"]]})
    store.put(OPERATOR, members, on=MAIN, expected_head=None)
    control = ControlService(
        resolve(tmp_path / "QMX", create=True).home, secret_getter=lambda _s, _n: None
    )
    control.attach_library(store)
    app = FastAPI()
    app.include_router(publish_collection_router(control))

    answer = (
        TestClient(as_caller(app, Caller("user")))
        .post("/api/library/collections/c-1/publish")
        .json()
    )
    with pytest.raises(ControlError) as single:
        control.library_merge(
            cast(tuple[str, int], store.head("u-1", drafts_ref("u-1")))[0],
            from_ref=drafts_ref("u-1"),
        )

    assert (answer["published"], answer["refused"]) == (
        [first["item"]],
        [{"item": "u-1", "code": single.value.code, "message": str(single.value)}],
    )
    assert store.head("u-1", MAIN) is None
