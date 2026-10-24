"""P-DISKFULL (W4; F22, D-11; Library AD-10, AD-27), acceptance: a machine gives way in one order, a
Library save that cannot fit is refused whole, and an upload stops whole and resumes later.

`p_torn.py`'s sibling, and the same shape:

1. **The order.** A volume under the scratch root is declared at a fixed size and filled with the
   four expendable classes. Making room for a floor takes the price cache, then transient blobs,
   then the telemetry queue, then fetched cache copies, and the log quotes that order.
2. **The refusal.** A scratch Library store whose floor is above the machine's real free space
   refuses `put` with `disk_full` and a plain message, and leaves no object, no blob and no move
   behind.
3. **The upload.** A write that stops on an I/O error leaves the bytes it took as a prefix of the
   file, never a torn mixture; the partial is re-hashed, resumed at that offset and the finished
   blob hashes to the whole file. DR7's upload half (AD-27).

On the server, lane 2 runs this against a loop-mounted volume under `/srv/qmx/check/dr2a/` with
`QMX_PROBE_SCRATCH` pointing into it, which is the same code on a real small disk; on the PC the
volume half is a fixed-size folder, because Windows has no loop mount.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_diskfull.py

Scratch goes to `D:/Temp/prb-dp/diskfull/` and is removed before the probe exits.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path

from qmx_engine.ledger import redact
from qmx_host.disk import EXPENDABLE, give_way
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

PROBE = "P-DISKFULL"
OPERATOR = Principal("operator")
MIB = 1024 * 1024
TOTAL_MB = 16
"""The fake volume's size."""
PART_MB = 2
"""What each expendable class holds, so the volume starts with half its room free."""
ORDER = ("price cache", "transient blobs", "telemetry queue", "fetched cache copies")
SCRATCH = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/prb-dp"))


def fill(root: Path, megabytes: int) -> None:
    """One file of `megabytes` in every expendable class's first folder."""
    for row in EXPENDABLE:
        folder = root / row.folders[0]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "part.bin").write_bytes(b"\0" * (megabytes * MIB))


def volume_free(root: Path, total: int) -> int:
    """A fixed-size volume's room: its size minus what sits on it."""
    used = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    return total - used


def order_case(folder: Path, problems: list[str]) -> None:
    """The rule takes the classes in table order and stops as soon as the room is there."""
    root = folder / "volume"
    shutil.rmtree(root, ignore_errors=True)
    total = TOTAL_MB * MIB
    fill(root, PART_MB)
    free = volume_free(root, total)
    need = free + 5 * MIB
    taken = give_way(root, need, free=lambda: volume_free(root, total), rows=EXPENDABLE)
    print(f"volume {total // MIB} MB, free before {free // MIB} MB, needed {need // MIB} MB")
    print(f"gave way: {', '.join(taken) or 'nothing'}")
    if taken != ORDER[:3]:
        problems.append(f"took {taken}, the table's first three are {ORDER[:3]}")
    if volume_free(root, total) < need:
        problems.append("the room asked for was not made")
    left = [
        row.name
        for row in EXPENDABLE
        if (root / row.folders[0]).is_dir() and any((root / row.folders[0]).iterdir())
    ]
    if left != [ORDER[-1]]:
        problems.append(f"classes left with data: {left}, wanted only {ORDER[-1]!r}")
    again = give_way(root, total, free=lambda: volume_free(root, total), rows=EXPENDABLE)
    print(f"the second pass took: {', '.join(again) or 'nothing'}")
    if ORDER[-1] not in again:
        problems.append(f"the second pass took {again}, wanted the last class")


def refusal_case(folder: Path, problems: list[str]) -> None:
    """A save below the floor is refused whole: no object, no blob, a plain message."""
    root = folder / "library"
    shutil.rmtree(root, ignore_errors=True)
    free = shutil.disk_usage(folder).free
    floor = free + MIB
    print(f"real free {free // MIB} MB, floor set to {floor // MIB} MB")
    with Store.open(root, redactor=redact, floor_bytes=floor) as store:
        try:
            store.put(
                OPERATOR,
                Draft("note", "n1", title="below the floor", blobs={"body.md": b"half a note"}),
                on="refs/drafts/n1",
                expected_head=None,
            )
        except LibraryRefused as refused:
            print(f"refused {refused.code}: {refused}")
            if refused.code != "disk_full":
                problems.append(f"refused {refused.code}, wanted disk_full")
            if "floor" not in str(refused):
                problems.append("the message does not name the floor it keeps")
        else:
            problems.append("the save was taken below the floor")
    objects = list((root / "objects").rglob("*.json")) if (root / "objects").is_dir() else []
    blobs = [path for path in (root / "blobs").rglob("*") if path.is_file()]
    move_log = root / "refs" / "log.jsonl"
    moves = len(move_log.read_text("utf-8").splitlines()) if move_log.exists() else 0
    print(f"objects written {len(objects)}, blobs {len(blobs)}, moves {moves}")
    if objects or blobs or moves:
        problems.append("a refused save left files behind")


def upload_case(folder: Path, problems: list[str]) -> None:
    """A write that hits an I/O error leaves a prefix, and the resume finishes the right blob."""
    root = folder / "upload-library"
    shutil.rmtree(root, ignore_errors=True)
    whole = b"qmx upload bytes " * 400_000
    half = len(whole) // 2
    first, rest = whole[:half], whole[half:]

    def stopping() -> Iterator[bytes]:
        yield first
        raise OSError(28, "No space left on device")

    with Store.open(root, redactor=redact) as store:
        try:
            store.append_upload(stopping(), upload_id="full-1")
        except OSError as error:
            print(f"the upload stopped: {error}")
        held, partial = store.upload_held("full-1")
        print(f"held {held} of {len(whole)} bytes, prefix hashes {partial == sha256(first).hexdigest()}")
        resumed, _ = store.append_upload(
            [rest], upload_id="full-1", offset=held, partial_sha256=partial
        )
        blob_id = store.complete_upload("full-1")
    if held != len(first):
        problems.append(f"the stopped upload held {held} bytes, not the {len(first)} it wrote")
    if partial != sha256(first).hexdigest():
        problems.append("the partial does not hash to the prefix it holds")
    if resumed != len(whole) or blob_id != f"sha256:{sha256(whole).hexdigest()}":
        problems.append("the resumed upload did not finish as the same blob")


def main() -> int:
    folder = SCRATCH / "diskfull"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    try:
        order_case(folder, problems)
        refusal_case(folder, problems)
        upload_case(folder, problems)
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    for problem in problems:
        print(f"  problem: {problem}")
    if problems:
        print(f"{PROBE} FAIL")
        return 1
    print(f"{PROBE} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
