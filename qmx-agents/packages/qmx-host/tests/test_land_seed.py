"""The dictionary's first content wave in the Library (A13): a start lands each seed folder's
entries as drafts in one collection per family, once per store, and a folder that grows lands
only its new entries. Every folder is in pytest's tmp folder; no host process starts."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store
from qmx_tools.functions import write_entry_statuses

from qmx_host.first_start import WAVE_SEED, land_wave, seed_rows
from qmx_host.host import land_dictionary_wave, open_store, register_checkers

OPERATOR = Principal("operator")
CUSTOM = WAVE_SEED / "indicators" / "custom-indicator.json"


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as opened:
        register_checkers(opened)
        yield opened


def _collection(store: Store, family: Path) -> list[str]:
    item = str(seed_rows(family)[0]["item"])
    view = store.get(OPERATOR, cast(tuple[str, int], store.head(item, MAIN))[0])
    return cast(list[str], view.fields["items"])


def test_a_start_lands_each_wave_family_as_drafts_once(store: Store) -> None:
    land_dictionary_wave(store)
    before = store.refs()
    land_dictionary_wave(store)

    items = _collection(store, WAVE_SEED / "indicators")
    statuses = {item: c.annotation()["value"] for item, _, c in write_entry_statuses(store)}
    assert store.refs() == before
    assert [store.head(i, MAIN) for i in items] == [None] * len(items)
    assert statuses[str(seed_rows(WAVE_SEED / "indicators")[1][0]["item"])] == "named"
    assert len(items) == len(list((WAVE_SEED / "indicators").glob("*.json")))


def test_a_grown_folder_lands_its_new_entry_and_keeps_his_edit(
    tmp_path: Path, store: Store
) -> None:
    family = tmp_path / "wave-1" / "indicators"
    family.mkdir(parents=True)
    shutil.copy(CUSTOM, family / "custom-indicator.json")
    first = [str(landed) for landed in land_wave(store, tmp_path / "wave-1")]
    row = seed_rows(family)[1][0]
    edited = {**row["fields"], "entry": {**row["fields"]["entry"], "boundaries": "his words"}}
    store.put(
        OPERATOR,
        Draft("component", row["item"], "his", fields=edited),
        on=drafts_ref(row["item"]),
        expected_head=cast(tuple[str, int], store.head(row["item"], drafts_ref(row["item"])))[0],
    )
    grown = json.loads(CUSTOM.read_text("utf-8")) | {"entry_id": "custom-indicator-copy"}
    grown["aliases"] = []
    (family / "custom-indicator-copy.json").write_text(json.dumps(grown), "utf-8")

    second = [str(landed) for landed in land_wave(store, tmp_path / "wave-1")]

    collection = str(seed_rows(family)[0]["item"])
    kept = store.get(
        OPERATOR, cast(tuple[str, int], store.head(row["item"], drafts_ref(row["item"])))[0]
    )
    assert (first, second, land_wave(store, tmp_path / "wave-1")) == (
        [f"indicators: 1 drafts landed and 0 kept in collection {collection}"],
        [f"indicators: 1 drafts landed and 1 kept in collection {collection}"],
        [],
    )
    assert cast(dict[str, object], kept.fields["entry"])["boundaries"] == "his words"
    assert len(_collection(store, family)) == 2
