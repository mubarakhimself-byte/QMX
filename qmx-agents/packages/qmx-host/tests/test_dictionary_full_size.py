"""Foundation check 7, the dictionary at full size: a fresh store takes first start's landings and a
publish of every collection through his route, and every page then tells the truth by itself. A
clashing save is refused, and an ordinary sentence stays unmatched. Every folder is in pytest's tmp
folder; no host process starts.

474 pages are 131 stdlib versions, in 116 folders, plus the 104 of the first wave and the 239 of
the port. The audit's older 455 counted 112 stdlib `@1` entries. R05 added `value-above@1` and
`trend-floor-from-record@2`, R06 added ten session versions and `fixed-fraction-at-stop@2`, and
RC-12 added `swing-stop-buffer@2`, `target-r-multiple@2` and `time-exit-bars@2`, which are the
126th to the 128th stdlib versions and the 469th to the 471st pages. RC-21 added `level-factor@1`,
the 129th stdlib version and the 472nd page. RC-22 added `cushion-rule@1` and `press-gate@1`,
the 130th and 131st versions and the 473rd and 474th pages. First start lands only the
343: the stdlib is read from its files."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qml.catalogue.loader import block_fingerprint
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
    HostStore,
    land_dictionary_statuses,
    land_dictionary_wave,
    land_first_unit,
    land_ported_dictionary,
    open_store,
    register_checkers,
)
from qmx_host.publish_collection import publish_collection_router

OPERATOR = Principal("operator")
CODE_STOPPED = "this entry's code stopped its own check, by an exit or a raise no check can read"
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
    land_dictionary_statuses(cast(HostStore, store)).join()

    assert [v.annotations.get("status") is None for v in before] == [False] * 343
    assert sum(c["published"] for c in counts) == 343
    assert [c["refused"] for c in counts] == [0] * 5
    assert len(pages) == 474
    assert [p["entry_id"] for p in pages if p["status"] is None] == []
    assert len(list(cast(Path, STDLIB).glob("*/*/entry.json"))) == 131
    assert store.annotation_log.read_bytes() == log


def test_a_start_gives_a_status_to_a_page_an_older_host_saved(control: ControlService) -> None:
    store: Store = control.library.store
    older = Store.put(
        store, OPERATOR, a_draft("older-word"), on=drafts_ref("older-word"), expected_head=None
    )

    unmarked = store.get(OPERATOR, older.object_id).annotations.get("status")
    land_dictionary_statuses(cast(HostStore, store)).join()

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
    fields = {"component_type": "indicator", "entry": cast(Any, entry)}
    return Draft("component", entry_id, entry_id, fields=fields)


A_BLOCK = '''"""An agent's block."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qml.blocks.api import Side, quantise


class _It:
    __slots__ = ("_seen",)

    def __init__(self) -> None:
        self._seen: list[Decimal] = []

    @property
    def warm_up_bars(self) -> int:
        return 3

    @property
    def state_bound(self) -> int:
        return 5

    def retained(self) -> int:
        return len(self._seen)

    def update(self, evidence: Mapping[str, object]) -> Decimal | None:
        STATEMENT

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        return None


class _Block:
    def make(
        self, params: Mapping[str, Decimal], inputs: Mapping[str, str], side: Side = Side.LONG
    ) -> _It:
        return _It()


BLOCK = _Block()
'''


def a_block(entry_id: str, statement: str, **blobs: bytes) -> Draft:
    code = A_BLOCK.replace("STATEMENT", statement).encode()
    entry = a_draft(
        entry_id,
        inputs=[{"port": "series", "stream_kind": "series", "measure": "price", "data_level": 1}],
        output={"type": "series", "measure": "price"},
        parameters={},
        warm_up={"rule": "1", "bars": 3},
        transfer={"fx": "not_assessed"},
        mirroring="not_applicable",
        fingerprint=block_fingerprint(code).value,
    ).fields["entry"]
    return Draft(
        "component",
        entry_id,
        entry_id,
        fields={"component_type": "indicator", "entry": entry},
        blobs={"code": code, **blobs},
    )


NO_WORDS = """class _Bad:
            def __str__(self) -> str:
                raise RuntimeError("no words")

        raise SystemExit(_Bad())"""
NO_NAME = """class _Meta(type):
            @property
            def __name__(cls) -> str:
                raise RuntimeError("no name")

        class _Boom(BaseException, metaclass=_Meta):
            pass

        raise _Boom()"""


def test_one_bad_entry_costs_its_own_status_and_the_start_carries_on(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = [
        a_block("a-index-error", "return quantise(self._seen[7])"),
        a_block("b-base", "raise BaseException('x')"),
        a_block("b-exits", "raise SystemExit(1)"),
        a_block("b-generator-exit", "raise GeneratorExit"),
        a_block("b-keyboard", "raise KeyboardInterrupt"),
        a_block("b-no-name", NO_NAME),
        a_block("b-no-words", NO_WORDS),
        a_block("c-unreadable-golden", "return None", golden=b"not json"),
        a_draft("d-older-word"),
    ]
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as store:
        register_checkers(store)
        heads = {
            d.item: Store.put(store, OPERATOR, d, on=drafts_ref(str(d.item)), expected_head=None)
            for d in saved
        }

        # A raise left to reach pytest crashes its report on the same bad name, and the run exits 0.
        try:
            land_dictionary_statuses(store).join()
            answer = store.put(
                OPERATOR,
                a_block("e-saved-now", "raise KeyboardInterrupt"),
                on=drafts_ref("e-saved-now"),
                expected_head=None,
            ).item
        except BaseException:
            answer = "a raise got out"

        status = {
            item: store.get(OPERATOR, commit.object_id).annotations.get("status")
            for item, commit in heads.items()
        }
    said = capsys.readouterr().err

    assert answer == "e-saved-now"
    assert {
        item: mark and cast(dict[str, str], mark)["value"] for item, mark in status.items()
    } == {
        "a-index-error": "specified",
        "b-base": "refused",
        "b-exits": "refused",
        "b-generator-exit": "refused",
        "b-keyboard": "refused",
        "b-no-name": "refused",
        "b-no-words": "refused",
        "c-unreadable-golden": None,
        "d-older-word": "named",
    }
    assert "c-unreadable-golden was not written: JSONDecodeError: " in said
    for item in ("b-base", "b-exits", "b-generator-exit", "b-keyboard", "b-no-name", "b-no-words"):
        assert f"library: the status of {item} is refused: {CODE_STOPPED}" in said
    assert f"library: the status of e-saved-now is refused: {CODE_STOPPED}" in said


A_START = """
import sys
import time
from pathlib import Path

sys.path.insert(0, sys.argv[2])
from test_dictionary_full_size import (
    OPERATOR, Store, a_block, a_draft, drafts_ref, land_dictionary_statuses, open_store,
    register_checkers,
)

def status_of(store, item):
    mark = store.get(OPERATOR, store.head(item, drafts_ref(item))[0]).annotations.get("status")
    return mark and mark["value"]

root = Path(sys.argv[1])
with open_store(root, root / "library", serving=False, floor=0) as store:
    register_checkers(store)
    for draft in (
        a_draft("a-older-word"),
        a_block("b-endless", "while True:\\n            pass"),
        a_draft("c-older-word"),
    ):
        Store.put(store, OPERATOR, draft, on=drafts_ref(str(draft.item)), expected_head=None)
    land_dictionary_statuses(store)
    print("the start went on", flush=True)
    while status_of(store, "a-older-word") is None:
        time.sleep(0.05)
    time.sleep(2)
    store.put(OPERATOR, a_draft("d-saved-now"), on=drafts_ref("d-saved-now"), expected_head=None)
    for item in ("a-older-word", "b-endless", "c-older-word", "d-saved-now"):
        print(item, status_of(store, item), flush=True)
print("the store closed", flush=True)
"""


def test_an_endless_block_costs_a_stuck_thread_and_not_the_start(tmp_path: Path) -> None:
    """Its own process, because a thread stuck in `while True` takes the GIL for as long as the
    process lives, and here that process must also end by itself."""
    done = subprocess.run(
        [sys.executable, "-c", A_START, str(tmp_path), str(Path(__file__).parent)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert (done.returncode, done.stdout.splitlines(), done.stderr) == (
        0,
        [
            "the start went on",
            "a-older-word named",
            "b-endless None",
            "c-older-word None",
            "d-saved-now named",
            "the store closed",
        ],
        "",
    )


A_LEAVING = """
import sys
import time
from pathlib import Path

from qmx_host.host import land_dictionary_statuses, open_store, register_checkers

root = Path(sys.argv[1])
with open_store(root, root / "library", serving=False, floor=0) as store:
    register_checkers(store)
    running = land_dictionary_statuses(store)
    time.sleep(float(sys.argv[2]))
running.join(60)
print("the pass goes on" if running.is_alive() else "the pass stopped")
"""


def test_leaving_the_store_under_the_status_pass_says_nothing(tmp_path: Path) -> None:
    """`serve` leaves its store on a refused start and on a normal stop, with the pass maybe still
    on it. Its own process, because that close used to end the process with an access violation."""

    def leaving(root: Path, after_seconds: float) -> tuple[int, str, str]:
        done = subprocess.run(
            [sys.executable, "-c", A_LEAVING, str(root), str(after_seconds)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return done.returncode, done.stdout, done.stderr

    clean = (0, "the pass stopped\n", "")
    full, one_slow = tmp_path / "full", tmp_path / "one-slow"
    with open_store(full, full / "library", serving=False, floor=0) as store:
        register_checkers(store)
        land_ported_dictionary(store)
        land_dictionary_wave(store)
    with open_store(one_slow, one_slow / "library", serving=False, floor=0) as store:
        register_checkers(store)
        slow = a_block("slow", "for _ in range(6_000_000):\n            pass\n        return None")
        Store.put(store, OPERATOR, slow, on=drafts_ref("slow"), expected_head=None)

    between_entries = [leaving(full, seconds) for seconds in (0.0, 0.05, 0.2)]
    inside_a_block = leaving(one_slow, 1.0)

    assert [*between_entries, inside_a_block] == [clean] * 4


def test_a_save_beside_a_thread_reading_the_store_answers(tmp_path: Path) -> None:
    """The start's pass reads and writes beside his saves. A save that committed must not read as
    failed because another thread was on the same catalog statement."""
    failed: list[str] = []
    stop = threading.Event()
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as store:
        register_checkers(store)
        held = store.put(OPERATOR, a_draft("held"), on=drafts_ref("held"), expected_head=None)

        def reads() -> None:
            try:
                while not stop.is_set():
                    store.get(OPERATOR, held.object_id)
            except Exception as error:
                failed.append(f"read {type(error).__name__}")

        reader = threading.Thread(target=reads, daemon=True)
        reader.start()
        try:
            for n in range(60):
                item = f"saved-{n}"
                store.put(OPERATOR, a_draft(item), on=drafts_ref(item), expected_head=None)
        except Exception as error:
            failed.append(f"save {type(error).__name__}")
        stop.set()
        reader.join()

    assert failed == []


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
