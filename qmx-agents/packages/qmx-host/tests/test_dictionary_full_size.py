"""Foundation check 7, the dictionary at full size: a fresh store takes first start's landings and a
publish of every collection through his route, and every page then tells the truth by itself. A
clashing save is refused, and an ordinary sentence stays unmatched. Every folder is in pytest's tmp
folder; no host process starts.

467 pages are 124 stdlib versions, in 113 folders, plus the 104 of the first wave and the 239 of
the port. The audit's older 455 counted 112 stdlib `@1` entries. R05 added `value-above@1` and
`trend-floor-from-record@2`, and R06 adds ten session versions. First start lands only the 343: the
stdlib is read from its files."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmx_control.service import ControlService
from qmx_engine.control_door import PRINCIPAL
from qmx_engine.service.context import Caller
from qmx_home import resolve
from qmx_library.kinds import KindRefused
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.gather import STDLIB
from qmx_tools.service import DomainContext
from starlette.types import ASGIApp, Receive, Scope, Send

from qmx_host.first_start import PORT_SEED, WAVE_SEED, seed_rows
from qmx_host.host import (
    land_dictionary_statuses,
    land_dictionary_wave,
    land_first_unit,
    land_ported_dictionary,
    open_store,
    register_checkers,
)
from qmx_host.publish_collection import publish_collection_router

OPERATOR = Principal("operator")
PORT = cast(dict[str, Any], json.loads((PORT_SEED / "port.json").read_text("utf-8")))
FAMILIES = sorted(f for f in WAVE_SEED.iterdir() if f.is_dir())
COLLECTIONS = [str(PORT["collection"]["item"]), *(str(seed_rows(f)[0]["item"]) for f in FAMILIES)]
ITEMS = [
    *(str(d["item"]) for d in PORT["drafts"]),
    *(str(d["item"]) for f in FAMILIES for d in seed_rows(f)[1]),
]


def his_door(app: ASGIApp) -> ASGIApp:
    async def served(scope: Scope, receive: Receive, send: Send) -> None:
        token = PRINCIPAL.set(Caller("user"))
        try:
            await app(scope, receive, send)
        finally:
            PRINCIPAL.reset(token)

    return served


@pytest.fixture
def control(tmp_path: Path) -> Iterator[ControlService]:
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as store:
        register_checkers(store)
        land_first_unit(store)
        land_ported_dictionary(store)
        land_dictionary_wave(store)
        service = ControlService(
            resolve(tmp_path / "QMX", create=True).home, secret_getter=lambda _s, _n: None
        )
        service.attach_library(store)
        yield service


def blocks(control: ControlService, root: Path) -> dict[str, Any]:
    context = DomainContext(root=root)
    context.control, context.library = control, control.library
    return domain_functions(context)["blocks"]


def test_a_fresh_store_lands_and_publishes_with_no_status_none(
    tmp_path: Path, control: ControlService
) -> None:
    store: Store = control.library.store
    app = FastAPI()
    app.include_router(publish_collection_router(control))
    client = TestClient(his_door(app))

    before = [
        store.get(OPERATOR, cast(tuple[str, int], store.head(i, drafts_ref(i)))[0]) for i in ITEMS
    ]
    counts = [
        client.post(f"/api/library/collections/{collection}/publish").json()["counts"]
        for collection in COLLECTIONS
    ]
    pages = blocks(control, tmp_path)["blocks_find"](words="", limit=1000)["rows"]
    log = store.annotation_log.read_bytes()
    land_dictionary_statuses(store)

    assert [v.annotations.get("status") is None for v in before] == [False] * 343
    assert sum(c["published"] for c in counts) == 343
    assert [c["refused"] for c in counts] == [0] * 5
    assert len(pages) == 467
    assert [p["entry_id"] for p in pages if p["status"] is None] == []
    assert len(list(STDLIB.glob("*/*/entry.json"))) == 124
    assert store.annotation_log.read_bytes() == log


def test_a_start_gives_a_status_to_a_page_an_older_host_saved(control: ControlService) -> None:
    store: Store = control.library.store
    older = Store.put(
        store, OPERATOR, a_draft("older-word"), on=drafts_ref("older-word"), expected_head=None
    )

    unmarked = store.get(OPERATOR, older.object_id).annotations.get("status")
    land_dictionary_statuses(store)

    assert unmarked is None
    assert (
        cast(dict[str, str], store.get(OPERATOR, older.object_id).annotations["status"])["value"]
        == "named"
    )


def a_draft(entry_id: str, **more: object) -> Draft:
    entry = {
        "schema": "qmx.entry/1",
        "entry_id": entry_id,
        "version": 1,
        "origin": "agent",
        "definition": "An agent's word for it.",
        "sources": [{"source_ref": "a note", "quote": "its words", "dated": "2026-11-06"}],
    } | more
    return Draft(
        "component", entry_id, entry_id, fields={"component_type": "indicator", "entry": entry}
    )


def test_a_clashing_save_is_refused_and_a_new_version_is_not(
    tmp_path: Path, control: ControlService
) -> None:
    store: Store = control.library.store
    held = json.loads((STDLIB / "trend-floor-from-record" / "2" / "entry.json").read_text("utf-8"))
    rest = {k: v for k, v in held.items() if k != "component_type"}
    second = Draft(
        "component", "floor-2", "floor", fields={"component_type": "motion", "entry": rest}
    )
    first_of_a_family = a_draft("my-new-word")

    with pytest.raises(KindRefused) as taken_alias:
        store.put(
            OPERATOR,
            a_draft("my-average", aliases=["EMA"]),
            on=drafts_ref("my-average"),
            expected_head=None,
        )
    with pytest.raises(KindRefused) as taken_id:
        store.put(OPERATOR, a_draft("ema", version=1), on=drafts_ref("ema"), expected_head=None)
    saved = store.put(OPERATOR, second, on=drafts_ref("floor-2"), expected_head=None)
    fresh = store.put(OPERATOR, first_of_a_family, on=drafts_ref("my-new-word"), expected_head=None)
    later = store.put(
        OPERATOR,
        a_draft("my-new-word", version=2),
        on=drafts_ref("my-new-word"),
        expected_head=fresh.object_id,
    )

    assert [(p.message, p.where) for p in taken_alias.value.problems] == [
        ("'EMA' already names ema", ("/entry/aliases/0",))
    ]
    assert [(p.message, p.where) for p in taken_id.value.problems] == [
        ("ema@1 is held by two different entries", ("/entry",))
    ]
    assert (saved.item, fresh.item, later.item) == ("floor-2", "my-new-word", "my-new-word")
    assert store.head("my-average", drafts_ref("my-average")) is None
    assert store.head("ema", MAIN) is None
    assert (
        cast(dict[str, str], store.get(OPERATOR, later.object_id).annotations["status"])["value"]
        == "named"
    )


def test_an_ordinary_sentence_stays_unmatched(tmp_path: Path, control: ControlService) -> None:
    store: Store = control.library.store
    app = FastAPI()
    app.include_router(publish_collection_router(control))
    client = TestClient(his_door(app))
    for collection in COLLECTIONS:
        client.post(f"/api/library/collections/{collection}/publish")

    answer = blocks(control, tmp_path)["blocks_match"](
        text="The trend is your friend. He said volume was high today. "
        "Price sweeps the Asian high and closes back in. RSI crosses back above 30."
    )

    assert store.head(ITEMS[0], MAIN) is not None
    assert answer["sentences"] == [
        {"sentence": "The trend is your friend", "entry": "unmatched"},
        {"sentence": "He said volume was high today", "entry": "unmatched"},
        {"sentence": "Price sweeps the Asian high and closes back in", "entry": "unmatched"},
        {"sentence": "RSI crosses back above 30", "entry": "rsi-cross-back@1"},
    ]
