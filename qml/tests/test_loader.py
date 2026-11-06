"""The one block loader: fingerprint before compile, every problem at once (AD-109, A4)."""

from __future__ import annotations

from pathlib import Path

from qmf.core.fingerprint import fingerprint_bytes

from qml.blocks.api import Block, EntryFace, parse_entry
from qml.catalogue import LoadProblemKind, Loaded, LockEntry, block_fingerprint, load

_STDLIB = Path(__file__).resolve().parents[1] / "src" / "qml" / "blocks" / "stdlib"
_PINS = (
    "ema@1",
    "roc-of-series@1",
    "rsi-cross-back@1",
    "market-next-open@1",
    "swing-stop-buffer@1",
    "target-r-multiple@1",
    "time-exit-bars@1",
    "fixed-fraction-at-stop@1",
    "percentile-of-own-history@1",
    "trend-floor-from-record@1",
)


def _folder(pin: str) -> Path:
    entry_id, version = pin.split("@")
    return _STDLIB / entry_id / version


def _face(pin: str) -> EntryFace:
    face = parse_entry((_folder(pin) / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


def _lock() -> list[LockEntry]:
    return [LockEntry(f.entry_id, f.version, f.fingerprint) for f in map(_face, _PINS)]


def _sources() -> dict[str, bytes]:
    return {pin: (_folder(pin) / "block.py").read_bytes() for pin in _PINS}


def test_the_ten_stdlib_blocks_load_with_the_fingerprints_their_entries_record() -> None:
    loaded = load(_lock(), _sources())

    assert isinstance(loaded, Loaded), loaded
    assert sorted(loaded.blocks) == sorted(_PINS)
    assert all(isinstance(block, Block) for block in loaded.blocks.values())
    assert loaded.lock_fingerprint.value.startswith("fp1:sha256:")


def test_placeholder_blocks_say_so_and_name_the_risk_session() -> None:
    marked = {
        pin: (_face(pin).origin, _face(pin).owner) for pin in _PINS if _face(pin).origin != "qml"
    }

    assert marked == {
        "swing-stop-buffer@1": ("placeholder", "risk-session"),  # mock-data-scan: allow
        "target-r-multiple@1": ("placeholder", "risk-session"),  # mock-data-scan: allow
        "time-exit-bars@1": ("placeholder", "risk-session"),  # mock-data-scan: allow
        "fixed-fraction-at-stop@1": ("placeholder", "risk-session"),  # mock-data-scan: allow
    }


def test_crlf_and_lf_copies_share_one_fingerprint() -> None:
    lf = b"BLOCK = None\nx = 1\n"
    crlf = b"BLOCK = None\r\nx = 1\r\n"

    assert block_fingerprint(crlf) == block_fingerprint(lf)
    assert block_fingerprint(lf) != block_fingerprint(b"BLOCK = None\nx = 2\n")


def test_a_missing_block_a_mismatch_and_no_block_come_back_together_while_crlf_loads() -> None:
    sources = _sources()
    lock = _lock()
    del sources["ema@1"]
    sources["rsi-cross-back@1"] = sources["rsi-cross-back@1"] + b"\n# edited\n"
    sources["market-next-open@1"] = (
        sources["market-next-open@1"].replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    )
    no_block = b"VALUE = 1\n"
    broken = b"def broken(:\n"
    lock += [
        LockEntry("no-block", 1, block_fingerprint(no_block).value),
        LockEntry("broken", 1, block_fingerprint(broken).value),
    ]
    sources["no-block@1"] = no_block
    sources["broken@1"] = broken

    problems = load(lock, sources)

    assert isinstance(problems, tuple)
    assert [(p.kind, p.pin) for p in problems] == [
        (LoadProblemKind.BLOCK_MISSING, "ema@1"),
        (LoadProblemKind.BLOCK_FINGERPRINT_MISMATCH, "rsi-cross-back@1"),
        (LoadProblemKind.BLOCK_PROTOCOL, "no-block@1"),
        (LoadProblemKind.BLOCK_COMPILE_ERROR, "broken@1"),
    ]
    assert all(p.message and p.hint for p in problems)


def test_a_mismatched_source_is_never_run() -> None:
    hostile = b"raise SystemExit('ran')\nBLOCK = None\n"
    lock = [LockEntry("hostile", 1, block_fingerprint(b"BLOCK = None\n").value)]

    problems = load(lock, {"hostile@1": hostile})

    assert isinstance(problems, tuple)
    assert [p.kind for p in problems] == [LoadProblemKind.BLOCK_FINGERPRINT_MISMATCH]


def test_pinned_weights_are_checked_by_their_own_fingerprint() -> None:
    source = (_folder("ema@1") / "block.py").read_bytes()
    pinned = fingerprint_bytes(b"weights-v1").value
    lock = [
        LockEntry("ema", 1, block_fingerprint(source).value, weights=pinned),
        LockEntry("ema", 2, block_fingerprint(source).value, weights=pinned),
    ]
    sources = {"ema@1": source, "ema@2": source}

    problems = load(lock, sources, {"ema@2": b"weights-v2"})
    loaded = load(lock[:1], sources, {"ema@1": b"weights-v1"})

    assert isinstance(problems, tuple)
    assert [(p.kind, p.pin) for p in problems] == [
        (LoadProblemKind.WEIGHTS_MISSING, "ema@1"),
        (LoadProblemKind.WEIGHTS_FINGERPRINT_MISMATCH, "ema@2"),
    ]
    assert isinstance(loaded, Loaded)
    assert loaded.weights == {"ema@1": b"weights-v1"}
