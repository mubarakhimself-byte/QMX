"""P-TORN (W2; Library AD-16), acceptance: a store survives a torn append and refuses to write
when a line in the middle is bad.

Four cases on a scratch store under `TMP`:

1. The last line of the ref, edge and annotation logs cut mid-line: the store opens, the line sits
   under `quarantine/`, `library:torn:<log>` is raised, and every other record reads back.
2. The same three tails NUL-filled instead of cut.
3. A bad middle line: the store opens read-only with an incident naming the log and the line, and
   a save is refused with that reason.
4. A second process holds `refs/claims.json` open while the store renames onto it: the rename
   retries, lands when the handle closes, and the retry lines are printed.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_torn.py
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from qmx_engine.ledger import redact

from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
ENGINE = Principal("engine", "pc")
LOGS = ("refs/log.jsonl", "edges/pc.jsonl", "annotations/log.jsonl")
HOLDER = """
import sys
import time
from pathlib import Path

handle = open(sys.argv[1], "rb")
Path(sys.argv[2]).write_text("held")
time.sleep(float(sys.argv[3]))
handle.close()
"""


def note(text: str, item: str) -> Draft:
    return Draft("note", item, title=text, blobs={"body.md": text.encode()})


def seed(root: Path) -> str:
    """Three notes, an edge and three annotations in a closed store; returns the first object's
    id, which is the first record in every log."""
    with Store.open(root, redactor=redact) as store:
        kept = store.put(OPERATOR, note("kept", "kept"), on="refs/drafts/kept", expected_head=None)
        cut = store.put(OPERATOR, note("cut", "cut"), on="refs/drafts/cut", expected_head=None)
        store.put(OPERATOR, note("third", "third"), on="refs/drafts/third", expected_head=None)
        store.relate(OPERATOR, cut.object_id, "supersedes", kept.object_id)
        return kept.object_id


def last_line(path: Path) -> bytes:
    return path.read_bytes().splitlines(keepends=True)[-1]


def lines(path: Path) -> int:
    return len(path.read_bytes().splitlines())


def torn_tails(root: Path) -> list[str]:
    kept = seed(root)
    problems: list[str] = []
    fragments: dict[str, bytes] = {}
    before = {name: lines(root / name) for name in LOGS}
    for name in LOGS:
        path = root / name
        torn = last_line(path)
        fragments[name] = torn[: len(torn) // 2]
        path.write_bytes(path.read_bytes()[: -len(torn)] + fragments[name])
    with Store.open(root, redactor=redact) as store:
        if store.state.health != "torn":
            problems.append(f"state {store.state.health}, expected torn")
        for name in LOGS:
            if f"library:torn:{name}" not in store.state.alarms:
                problems.append(f"no library:torn:{name} alarm")
            if lines(root / name) != before[name] - 1:
                problems.append(f"{name} still reads the torn line")
            kept_line = (root / "quarantine" / name).read_bytes()
            if kept_line != fragments[name] + b"\n":
                problems.append(f"quarantine/{name} holds {kept_line!r}")
        if store.resolve(OPERATOR, "kept", "refs/drafts/kept") != kept:
            problems.append("the first record does not read back")
        if store.get(OPERATOR, kept).title != "kept":
            problems.append("the first object does not read back")
        store.put(OPERATOR, note("after", "after"), on="refs/drafts/after", expected_head=None)
    return problems


def nul_tails(root: Path) -> list[str]:
    kept = seed(root)
    problems: list[str] = []
    fragments: dict[str, bytes] = {}
    for name in LOGS:
        path = root / name
        torn = last_line(path)
        fragments[name] = b"\x00" * len(torn)
        path.write_bytes(path.read_bytes()[: -len(torn)] + fragments[name])
    with Store.open(root, redactor=redact) as store:
        if store.state.health != "torn":
            problems.append(f"state {store.state.health}, expected torn")
        for name in LOGS:
            kept_line = (root / "quarantine" / name).read_bytes()
            if kept_line != fragments[name] + b"\n":
                problems.append(f"quarantine/{name} holds {len(kept_line)} bytes, expected NULs")
        if store.resolve(OPERATOR, "kept", "refs/drafts/kept") != kept:
            problems.append("the NUL case lost the first record")
    return problems


def middle_line(root: Path) -> list[str]:
    kept = seed(root)
    problems: list[str] = []
    path = root / "refs/log.jsonl"
    raw = path.read_bytes().splitlines(keepends=True)
    raw[1] = b'{"seq": 2, "item": "cut", torn\n'
    path.write_bytes(b"".join(raw))
    with Store.open(root, redactor=redact) as store:
        if (store.state.health, store.state.incident) != (
            "read_only",
            "refs/log.jsonl line 2 does not parse",
        ):
            problems.append(f"state {store.state.health} incident {store.state.incident}")
        try:
            store.put(OPERATOR, note("nope", "nope"), on="main", expected_head=None)
        except LibraryRefused as refused:
            if refused.code != "storage_failure" or "refs/log.jsonl line 2" not in str(refused):
                problems.append(f"put refused with {refused}")
        else:
            problems.append("put was not refused on a read-only store")
        if store.get(OPERATOR, kept).title != "kept":
            problems.append("the read-only store lost an object")
    return problems


def held_handle(root: Path) -> list[str]:
    problems: list[str] = []
    with Store.open(root, redactor=redact) as store:
        store.claim(ENGINE, "backtest:eurusd", "run-1", 60)
        store.release(ENGINE, "backtest:eurusd", "run-1")
        target = root / "refs" / "claims.json"
        marker = root / "held.marker"
        holder = subprocess.Popen(
            [sys.executable, "-c", HOLDER, str(target), str(marker), "0.6"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 10
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            started = time.monotonic()
            with captured() as said:
                taken = store.claim(ENGINE, "backtest:eurusd", "run-2", 60)
            waited = time.monotonic() - started
        finally:
            holder.wait(timeout=10)
        for line in said:
            print(f"  retry line: {line}")
        if not taken.granted:
            problems.append("the claim was lost while the handle was held")
        if waited < 0.1:
            problems.append(f"the rename landed in {waited:.3f} s, before the handle closed")
        if store.live_claims().get("backtest:eurusd") != "run-2":
            problems.append("the claim does not read back")
        if sys.platform == "win32" and not any("retrying rename" in line for line in said):
            problems.append("no retry line")
    return problems


@contextmanager
def captured() -> Iterator[list[str]]:
    said: list[str] = []

    class Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            said.append(record.getMessage())

    collector = Collect()
    logger = logging.getLogger("qmx_library.store")
    logger.addHandler(collector)
    logger.setLevel(logging.WARNING)
    try:
        yield said
    finally:
        logger.removeHandler(collector)


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="p-torn-"))
    problems: list[tuple[str, list[str]]] = []
    try:
        for name, case in (
            ("cut tail", torn_tails),
            ("NUL tail", nul_tails),
            ("bad middle line", middle_line),
            ("held handle", held_handle),
        ):
            found = case(scratch / name.replace(" ", "-"))
            print(f"{name}: {'ok' if not found else 'FAILED'}")
            problems.append((name, found))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    failed = [f"{name}: {problem}" for name, found in problems for problem in found]
    for problem in failed:
        print(f"  {problem}")
    if failed:
        print("P-TORN FAIL")
        return 1
    print("P-TORN PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
