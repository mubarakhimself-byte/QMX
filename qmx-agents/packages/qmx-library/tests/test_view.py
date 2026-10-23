"""Every kind has a card and a page, from one read, with the header computed at read (W20, AD-33).

The kinds are read from their own schema files, the way the roster does, so a kind added later is
covered here without editing this module. A fact the read cannot compute answers unavailable with
its reason; an archived item still answers and says why.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_engine.ledger import redact

from qmx_library.kinds import roster, schema_files
from qmx_library.port import Draft, ObjectId
from qmx_library.principal import Principal
from qmx_library.store import Store
from qmx_library.view import CardView, PageView, family, view

OPERATOR = Principal("operator")
START = datetime(2026, 10, 23, 9, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=Clock()) as opened:
        yield opened


def filled_from(schema: dict[str, Any]) -> dict[str, JsonValue]:
    """A value for every required field of one JSON Schema object, recursively."""
    properties = cast(dict[str, dict[str, Any]], schema.get("properties") or {})
    filled: dict[str, JsonValue] = {}
    for name in cast(list[str], schema.get("required") or []):
        spec = properties.get(name, {})
        if "enum" in spec:
            filled[name] = cast(JsonValue, spec["enum"][0])
        elif "required" in spec:
            filled[name] = filled_from(spec)
        elif spec.get("type") == "integer":
            filled[name] = 1
        elif spec.get("type") == "array":
            filled[name] = []
        elif spec.get("type") == "object":
            filled[name] = {}
        else:
            filled[name] = f"{name}-1"
    return filled


def schema_of(kind_name: str, key: str) -> dict[str, Any]:
    path = next(p for p in schema_files() if p.name == f"{kind_name}.schema.json")
    return cast(dict[str, Any], json.loads(path.read_text("utf-8"))[key])


def example(kind_name: str) -> dict[str, JsonValue]:
    """The smallest fields an object of this kind may carry, from its own schema."""
    return filled_from(schema_of(kind_name, "fields"))


def required_blobs(kind_name: str) -> dict[str, bytes]:
    """One small body per blob slot the kind declares as required."""
    blobs = cast(dict[str, dict[str, Any]], schema_of(kind_name, "blobs"))
    return {name: b"{}" for name, spec in blobs.items() if spec.get("required")}


def put(
    store: Store, kind_name: str, item: str, fields: dict[str, JsonValue] | None = None
) -> ObjectId:
    """One object of `kind_name`: a record lands on main, a definition on its own draft."""
    ref = "main" if roster()[kind_name].klass == "record" else f"refs/drafts/{item}"
    draft = Draft(
        kind_name,
        item,
        f"{item} title",
        fields=example(kind_name) | (fields or {}),
        blobs=required_blobs(kind_name),
    )
    head = store.head(item, ref)
    return store.put(
        OPERATOR, draft, on=ref, expected_head=None if head is None else head[0]
    ).object_id


def obj(value: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(value, dict)
    return value


def seq(value: JsonValue) -> list[JsonValue]:
    assert isinstance(value, list)
    return value


def test_every_kind_answers_a_card_of_at_most_five_facts_and_a_page(store: Store) -> None:
    live = [name for name, spec in roster().items() if not spec.retired]
    assert len(live) > 30

    for name in live:
        object_id = put(store, name, f"item-{name}")
        card = view(store, OPERATOR, object_id, "card")
        page = view(store, OPERATOR, object_id, "page")

        assert isinstance(card, CardView) and isinstance(page, PageView)
        facts = seq(obj(card.as_json())["facts"])
        header = obj(obj(card.as_json())["header"])
        assert 1 <= len(facts) <= 5, name
        assert all(isinstance(obj(fact)["available"], bool) for fact in facts), name
        assert {"title", "kind", "icon", "version", "state", "mark", "landed", "bytes"} <= set(
            header
        ), name
        assert header["kind"] == name
        assert seq(obj(page.as_json())["tabs"]), name


def test_an_archived_item_still_answers_and_says_why(store: Store) -> None:
    object_id = put(store, "note", "note-archived", {"text": "an old note"})
    store.archive(OPERATOR, "note-archived", "replaced by the October rewrite")

    header = obj(obj(view(store, OPERATOR, object_id, "card").as_json())["header"])

    assert header["state"] == "archived"
    assert header["archived_because"] == "replaced by the October rewrite"


def test_a_fact_that_fails_reads_unavailable_with_its_reason(store: Store) -> None:
    item = "result-corrupt"
    head = store.head(item, "main")
    draft = Draft(
        "backtest-result",
        item,
        "A result whose trades blob is corrupt",
        fields={"world": "backtest", "outcome": "supports"},
        blobs={"report": b"not json at all"},
    )
    object_id = store.put(
        OPERATOR, draft, on="main", expected_head=None if head is None else head[0]
    ).object_id

    body = obj(view(store, OPERATOR, object_id, "page").as_json())
    tabs = {str(obj(tab)["tab"]): obj(tab) for tab in seq(body["tabs"])}

    assert tabs["Equity"]["available"] is False
    assert "report blob is corrupt" in str(tabs["Equity"]["reason"])


def test_the_family_read_returns_parent_children_siblings_and_what_changed(store: Store) -> None:
    parent = put(store, "note", "idea")
    child = put(store, "note", "idea-gbpusd", {"what_changed": "EURUSD becomes GBPUSD"})
    sibling = put(store, "note", "idea-15m", {"what_changed": "the timeframe: 1h becomes 15m"})
    store.relate(OPERATOR, child, "variant-of", parent)
    store.relate(OPERATOR, sibling, "variant-of", parent)

    found = family(store, OPERATOR, child)

    assert found.parent == parent
    assert found.children == ()
    assert found.siblings == (sibling,)
    assert [(edge.edge, edge.to_id, edge.what_changed) for edge in found.edges] == [
        ("variant-of", parent, "EURUSD becomes GBPUSD")
    ]
