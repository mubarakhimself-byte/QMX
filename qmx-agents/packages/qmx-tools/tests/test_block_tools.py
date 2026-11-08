"""The dictionary's doors (A11): find, get, check and match over QML's entries and the Library's,
and the put check that refuses a wrong entry while every unmarked component saves as before."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
import qml
from qmx_library.kinds import KindRefused, Problem
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store

from qmx_tools.functions import domain_functions, write_entry_statuses
from qmx_tools.gather import entry_problems
from qmx_tools.service import DomainContext

STDLIB = Path(qml.__file__).resolve().parent / "blocks" / "stdlib"
GOLDEN = (
    Path(qml.__file__).resolve().parents[2] / "tests" / "golden" / "talib-0.7.1.json"
).read_bytes()
OPERATOR = Principal("operator")
Row = Callable[..., dict[str, Any]]


def entry(entry_id: str) -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads((STDLIB / entry_id / "1" / "entry.json").read_text()))


def source(entry_id: str) -> bytes:
    return (STDLIB / entry_id / "1" / "block.py").read_bytes()


def as_item(face: dict[str, Any]) -> JsonObject:
    rest = {k: v for k, v in face.items() if k != "component_type"}
    return cast("JsonObject", {"component_type": face["component_type"], "entry": rest})


def library_check(fields: JsonObject) -> list[Problem]:
    """The host's `qml.entry/1` registration, as `qmx_host.host.entry_check` maps it."""
    return [
        Problem(p.message, (f"/entry{p.where}",), "check_failed", "entry/face")
        for p in entry_problems(fields)
    ]


@pytest.fixture
def context(tmp_path: Path) -> DomainContext:
    return DomainContext(root=tmp_path)


@pytest.fixture
def blocks(context: DomainContext) -> dict[str, Row]:
    return domain_functions(context)["blocks"]


@pytest.fixture
def store(context: DomainContext) -> Store:
    found = context.library.store
    found.register_checker("qml.entry/1", library_check)
    return found


def test_match_maps_the_rsi_sentence_and_asks_to_append_the_unknown_one(
    blocks: dict[str, Row],
) -> None:
    text = "RSI crosses back above 30. Price sweeps the Asian high and closes back in."

    assert blocks["blocks_match"](text=text) == {
        "sentences": [
            {"sentence": "RSI crosses back above 30", "entry": "rsi-cross-back@1"},
            {"sentence": "Price sweeps the Asian high and closes back in", "entry": "unmatched"},
        ],
        "append_requests": [
            {
                "sentence": "Price sweeps the Asian high and closes back in",
                "words": ["price", "sweep", "asian", "high", "close", "back"],
            }
        ],
    }


def test_find_names_the_trend_filters_in_one_line_each(blocks: dict[str, Row]) -> None:
    found = blocks["blocks_find"](words="trend filter", role="filter", limit=4)

    assert [row["line"] for row in found["rows"]] == [
        "adx@1 | indicator | series | level 1 | implemented | Wilder's Average Directional "
        "Index: the smoothed mean of 100 x |+DI - -DI| / (+DI + -DI) over period bars, from 0 to "
        "100.",
        "alligator-line@1 | indicator | series | level 1 | implemented | One Alligator balance "
        "line: the smoothed mean of the median price over period bars, drawn shift bars ahead. "
        "Jaw 13 and 8, teeth 8 and 5, lips 5 and 3.",
        "ichimoku-senkou-a@1 | indicator | series | level 1 | implemented | The mean of "
        "Tenkan-sen and Kijun-sen, drawn shift bars ahead.",
        "initial-balance-range-extension@1 | indicator | series | level 1 | implemented | How far "
        "the session has traded beyond its initial balance on one side since the balance "
        "completed: the highest high above the balance's high for side 1, the lowest low below "
        "the balance's low for side -1, and 0 while it has not extended.",
    ]


def test_get_reads_an_entry_with_its_code_and_names_the_nearest_for_a_typo(
    blocks: dict[str, Row],
) -> None:
    ema = blocks["blocks_get"](entry_id="ema")

    assert (ema["status"], ema["held_in"], ema["entry"]["aliases"]) == (
        "implemented",
        "qml",
        ["EMA", "exponential moving average"],
    )
    assert ema["code"] == source("ema").decode("utf-8")
    with pytest.raises(ValueError, match=r"^no entry 'emaa'; the nearest are ema, "):
        blocks["blocks_get"](entry_id="emaa")


def test_check_refuses_a_native_claim_with_no_source_and_a_name_another_entry_holds(
    blocks: dict[str, Row],
) -> None:
    draft = entry("time-exit-bars") | {
        "entry_id": "hold-bars",
        "aliases": ["EMA"],
        "transfer": {"fx": "native"},
    }
    del draft["sources"]

    result = blocks["blocks_check"](entry=draft, source=source("time-exit-bars").decode())

    assert (result["verdict"], result["status"]) == ("fail", None)
    assert [(e["where"], e["message"]) for e in result["errors"]] == [
        ("/transfer/fx", "fx is claimed native with no source"),
        ("/sources", "an entry with no published reference cites no source"),
        ("hold-bars@1/aliases/0", "'EMA' already names ema"),
    ]
    assert result["fingerprint"] == entry("time-exit-bars")["fingerprint"]


def test_check_refuses_a_draft_that_reuses_a_held_pin_with_different_content(
    blocks: dict[str, Row],
) -> None:
    code = source("ema").decode()
    changed = entry("ema") | {"definition": "A different average under the same pin."}

    result = blocks["blocks_check"](entry=changed, source=code)

    assert (result["verdict"], result["status"]) == ("fail", None)
    assert [(e["where"], e["message"]) for e in result["errors"]] == [
        ("ema@1", "ema@1 is held by two different entries"),
    ]


def test_check_finds_no_corpus_problem_for_the_held_entry_itself_or_its_next_version(
    blocks: dict[str, Row],
) -> None:
    code = source("ema").decode()
    same = blocks["blocks_check"](entry=entry("ema"), source=code)
    newer = blocks["blocks_check"](entry=entry("ema") | {"version": 2}, source=code)

    assert [(r["errors"], r["status"]) for r in (same, newer)] == [
        ([], "specified"),
        ([], "specified"),
    ]


def test_the_put_check_refuses_a_wrong_entry_and_every_unmarked_component_saves_as_before(
    store: Store,
) -> None:
    wrong = entry("ema") | {"transfer": {"fx": "native"}}
    del wrong["sources"]
    unmarked: list[JsonObject] = [
        {"legacy_provides": "k", "app_id": "a", "output": "o"},
        {"record_kind": "confluence", "body": {"legs": []}},
        {"component_type": "indicator", "entry": {"note": "no marker"}},
    ]

    saved = [
        store.put(
            OPERATOR,
            Draft("component", f"u{i}", fields=f),
            on=drafts_ref(f"u{i}"),
            expected_head=None,
        )
        for i, f in enumerate(unmarked)
    ]
    with pytest.raises(KindRefused) as refused:
        store.put(
            OPERATOR,
            Draft("component", "wrong", fields=as_item(wrong)),
            on=drafts_ref("wrong"),
            expected_head=None,
        )

    assert [s.object_id.startswith("fp1:sha256:") for s in saved] == [True, True, True]
    assert [(p.where, p.message) for p in refused.value.problems] == [
        (("/entry/transfer/fx",), "fx is claimed native with no source"),
    ]


def test_the_ten_qml_blocks_save_as_entries_and_their_status_is_written(
    store: Store, blocks: dict[str, Row]
) -> None:
    ids = (
        "ema",
        "fixed-fraction-at-stop",
        "market-next-open",
        "percentile-of-own-history",
        "roc-of-series",
        "rsi-cross-back",
        "swing-stop-buffer",
        "target-r-multiple",
        "time-exit-bars",
        "trend-floor-from-record",
    )
    for entry_id in ids:
        blobs = {"code": source(entry_id)} | (
            {"golden": GOLDEN} if "golden" in entry(entry_id) else {}
        )
        draft = Draft("component", entry_id, fields=as_item(entry(entry_id)), blobs=blobs)
        store.put(OPERATOR, draft, on=drafts_ref(entry_id), expected_head=None)
    held = entry("time-exit-bars") | {"entry_id": "hold-bars", "aliases": ["bars held exit"]}
    copy = Draft(
        "component", "hold", fields=as_item(held), blobs={"code": source("time-exit-bars")}
    )
    store.put(OPERATOR, copy, on=drafts_ref("hold"), expected_head=None)
    store.merge(OPERATOR, "hold", from_ref=drafts_ref("hold"), into=MAIN)

    written = write_entry_statuses(store)
    again = write_entry_statuses(store)

    assert [(item, ref, c.status) for item, ref, c in written] == [
        ("ema", "refs/drafts/ema", "implemented"),
        ("fixed-fraction-at-stop", "refs/drafts/fixed-fraction-at-stop", "implemented"),
        ("hold", "main", "implemented"),
        ("market-next-open", "refs/drafts/market-next-open", "implemented"),
        ("percentile-of-own-history", "refs/drafts/percentile-of-own-history", "implemented"),
        ("roc-of-series", "refs/drafts/roc-of-series", "implemented"),
        ("rsi-cross-back", "refs/drafts/rsi-cross-back", "implemented"),
        ("swing-stop-buffer", "refs/drafts/swing-stop-buffer", "implemented"),
        ("target-r-multiple", "refs/drafts/target-r-multiple", "implemented"),
        ("time-exit-bars", "refs/drafts/time-exit-bars", "implemented"),
        ("trend-floor-from-record", "refs/drafts/trend-floor-from-record", "implemented"),
    ]
    assert [c.evidence for _, _, c in again] == [c.evidence for _, _, c in written]
    found = blocks["blocks_get"](entry_id="hold-bars")
    assert (found["status"], found["held_in"]) == ("implemented", "hold")
