"""A store survives a torn append and refuses to write when a line in the middle is bad (AD-16):
a cut or NUL-filled last line goes to `quarantine/` with an alarm and the store opens, and a
rename Windows refuses because the target is held open is retried until it lands."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
ENGINE = Principal("engine", "pc")
LOGS = ("refs/log.jsonl", "edges/pc.jsonl", "annotations/log.jsonl")


def note(text: str, item: str) -> Draft:
    return Draft("note", item, title=text, blobs={"body.md": text.encode()})


def seeded(root: Path) -> str:
    """Three notes, an edge between two of them and an annotation on each, in a closed store.
    Returns the first note's object id, which is the first record in every log."""
    with Store.open(root, redactor=redact) as store:
        kept = store.put(OPERATOR, note("kept", "kept"), on="refs/drafts/kept", expected_head=None)
        cut = store.put(OPERATOR, note("cut", "cut"), on="refs/drafts/cut", expected_head=None)
        store.put(OPERATOR, note("third", "third"), on="refs/drafts/third", expected_head=None)
        store.relate(OPERATOR, cut.object_id, "supersedes", kept.object_id)
        return kept.object_id


def last_line(path: Path) -> bytes:
    return path.read_bytes().splitlines(keepends=True)[-1]


def test_a_torn_tail_opens_the_store_with_one_quarantined_line(tmp_path: Path) -> None:
    root = tmp_path / "library"
    kept = seeded(root)
    cut_halves: dict[str, bytes] = {}
    for name in LOGS:
        path = root / name
        torn = last_line(path)
        cut_halves[name] = torn[: len(torn) // 2]
        path.write_bytes(path.read_bytes()[: -len(torn)] + cut_halves[name])

    with Store.open(root, redactor=redact) as store:
        assert (store.state.health, store.state.alarms, store.state.incident) == (
            "torn",
            tuple(f"library:torn:{name}" for name in LOGS),
            None,
        )
        assert store.resolve(OPERATOR, "kept", "refs/drafts/kept") == kept
        store.put(OPERATOR, note("after", "after"), on="refs/drafts/after", expected_head=None)

    for name in LOGS:
        assert (root / "quarantine" / name).read_bytes() == cut_halves[name] + b"\n"


def test_a_nul_filled_tail_opens_the_store_and_keeps_the_bytes(tmp_path: Path) -> None:
    root = tmp_path / "library"
    kept = seeded(root)
    for name in LOGS:
        path = root / name
        torn = last_line(path)
        path.write_bytes(path.read_bytes()[: -len(torn)] + b"\x00" * len(torn))

    with Store.open(root, redactor=redact) as store:
        assert store.state.health == "torn"
        assert store.state.alarms == tuple(f"library:torn:{name}" for name in LOGS)
        assert store.resolve(OPERATOR, "kept", "refs/drafts/kept") == kept

    quarantined = (root / "quarantine" / "refs/log.jsonl").read_bytes()
    assert quarantined.count(b"\x00") > 100


def test_a_bad_middle_line_opens_the_store_read_only_and_refuses_a_put(tmp_path: Path) -> None:
    root = tmp_path / "library"
    kept = seeded(root)
    path = root / "refs/log.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    lines[1] = b'{"seq": 2, "item": "cut", torn\n'
    path.write_bytes(b"".join(lines))

    with Store.open(root, redactor=redact) as store:
        assert (store.state.health, store.state.incident) == (
            "read_only",
            "refs/log.jsonl line 2 does not parse",
        )
        assert store.get(OPERATOR, kept).title == "kept"
        with pytest.raises(LibraryRefused, match=r"^storage_failure:") as refused:
            store.put(OPERATOR, note("nope", "nope"), on="main", expected_head=None)

    assert "refs/log.jsonl line 2" in str(refused.value)


def test_a_rename_under_a_held_handle_lands_when_the_handle_closes(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "library"
    with Store.open(root, redactor=redact) as store:
        assert store.claim(ENGINE, "backtest:eurusd", "run-1", 60).granted
        store.release(ENGINE, "backtest:eurusd", "run-1")
        held = (root / "refs" / "claims.json").open("rb")
        closer = threading.Timer(0.15, held.close)
        closer.start()
        try:
            taken = store.claim(ENGINE, "backtest:eurusd", "run-2", 60)
        finally:
            closer.join()
            held.close()

        assert taken.granted
        assert store.live_claims() == {"backtest:eurusd": "run-2"}

    if sys.platform == "win32":
        assert "retrying rename onto claims.json" in caplog.text
