"""P-SERVERLOST (W7, acceptance): the flip waits for his click, and a lost server is restored from
the bucket, or, without one, names exactly what has one copy only (Library AD-14, AD-16; 55 probe
row 12; F14, F21, F24, N13).

Two scratch roots stand in for the two machines, and the probe runs twice: once with a scratch
bucket folder, once without. Each run begins with the flip of MIGRATION step 8 on those roots. The
card says "Move the Library to the server" with one button, a save during the hold is refused
`primary_moving`, the epoch does not move until the button is pressed, and pressing it raises the
epoch by one. The server then writes the Library and the PC takes the selective sync.

With a bucket, the server pushes after its commit batch, the server root is wiped, and the procedure
restores a new server from that folder; every object the bucket held reads back by hash. Without
one, the server root is wiped, the procedure names the durable blobs born on the server that the PC
never opened (a text slot reaches the PC, so it is not among them), and a new server is rebuilt from
the PC's replica. Both runs then re-pair and agree on every ref the PC owns.

The scratch bucket is a folder: the push and the rebuild run through an rclone command over a local
remote (`scratch:<folder>`), so this probe measures the procedure and the bytes, not the bucket
service. An old server that comes back is P-SPLIT's case, which DR2D's lane 6 reruns after a flip.

**Pass:** nothing flips before the press, the epoch rises by one on the press and again on the
promotion, a reachable old host is asked to stop first, with the bucket every object reads back and
the two ref logs agree, without it the lost list is exactly the blobs never opened and everything
else reads back. **Fail:** a step needs an action the procedure does not name, a bucket object does
not come back, or the lost list is wrong.

    uv run --no-sync python ../scripts/probes/data/p_serverlost.py
    uv run --no-sync python ../scripts/probes/data/p_serverlost.py --branch bucket
    uv run --no-sync python ../scripts/probes/data/p_serverlost.py --branch no-bucket
    uv run --no-sync python ../scripts/probes/data/p_serverlost.py --branch flip
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import shutil
from collections.abc import Callable, Sequence
from pathlib import Path

from common import SCRATCH, Report
from qmx_control import node
from qmx_control.primary import Flip, server_lost
from qmx_engine.ledger import redact
from qmx_hub.bucket import Bucket
from qmx_hub.replicate import StorePeer, sync, sync_since
from qmx_library.client import OwnerTable
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
HUB = "http://100.64.0.2:18100"
MOVE = "Move the Library to the server"
ITEMS = 3


class Upstream:
    """The server as a replica's blob source, which is what "opened on the PC" means (AD-10)."""

    def __init__(self, peer: StorePeer) -> None:
        self.peer = peer

    def fetch(self, blob_id: str) -> bytes | None:
        return self.peer.blob(blob_id)


def local_runner(folder: Path) -> Callable[[Sequence[str]], str]:
    """`rclone copy|copyto` over the folder as a local remote named `scratch`."""

    def run(call: Sequence[str]) -> str:
        verb = call[1]
        source = folder / call[2].split(":", 1)[1].removeprefix("library/")
        target = folder / call[3].split(":", 1)[1].removeprefix("library/")
        excludes = [call[index + 1] for index, item in enumerate(call) if item == "--exclude"]
        if verb == "copyto":
            _copy(source, target)
            return ""
        for path in sorted(source.rglob("*")) if source.exists() else []:
            relative = path.relative_to(source).as_posix()
            if path.is_file() and not any(
                fnmatch.fnmatch(relative, pattern) for pattern in excludes
            ):
                _copy(path, target / relative)
        return ""

    return run


def _copy(source: Path, target: Path) -> None:
    if not source.is_file():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def flip_phase(root: Path, report: Report, name: str) -> list[str]:
    """MIGRATION step 8 on the two roots: the card, the hold, the equal push, his press."""
    problems: list[str] = []
    with (
        Store.open(root / "pc", redactor=redact, name="pc") as pc,
        Store.open(root / "server", redactor=redact, name="server") as server,
    ):
        flip = Flip(pc, StorePeer(server), root / "pc-home", HUB)
        card = flip.announce()
        if (card.title, card.button, card.stage) != (MOVE, MOVE, "waiting"):
            problems.append(f"the inbox card reads {card.title!r} with button {card.button!r}")
        pc.put(
            OPERATOR,
            Draft("note", "before-the-move", title="a save made before the flip"),
            on="main",
            expected_head=None,
        )
        flip.quiesce()
        try:
            flip.save(OPERATOR, Draft("note", "during", title="a save during the flip"), on="main")
        except LibraryRefused as refused:
            if refused.code != "primary_moving":
                problems.append(f"a save during the flip refused with {refused.code}")
        else:
            problems.append("a save during the flip was taken")
        flip.push_until_equal()
        held = pc.epoch
        if held is not None:
            problems.append(f"the epoch moved to {held.epoch} before the button was pressed")
        pressed = flip.press(OPERATOR)
        raised = pc.epoch
        if raised is None or (raised.primary, raised.epoch) != ("server", 1):
            problems.append(f"the press raised {raised}")
        if pressed.epoch != 1:
            problems.append(f"the closed card names epoch {pressed.epoch}")
        report.note(f"{name}: flip paused saves {flip.paused_s} s, epoch now {raised}")
        server.learn_epoch(raised)
    return problems


def after_the_flip(root: Path, report: Report, name: str) -> list[str]:
    """A save the server takes after the flip mirrors back to the PC (step 8.6)."""
    problems: list[str] = []
    with Store.open(root / "server", redactor=redact, name="server") as server:
        done = server.put(
            OPERATOR,
            Draft("note", "after-the-flip", title="a save made after the flip"),
            on="main",
            expected_head=None,
        )
        with Store.open(root / "pc", redactor=redact, name="pc", role="replica") as pc:
            sync_since(StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=0)
            if pc.head("after-the-flip", "main") != (done.object_id, 1):
                problems.append("a save after the flip did not mirror back to the PC")
            report.note(f"{name}: the save after the flip landed on the server and mirrored back")
    return problems


def run_branch(name: str, *, bucket: bool, report: Report) -> None:
    """One of the two runs: the flip, the loss, and what comes back."""
    root = SCRATCH / "p-serverlost" / name
    shutil.rmtree(root, ignore_errors=True)
    for folder in ("pc", "server", "bucket", "pc-home", "server-home"):
        (root / folder).mkdir(parents=True)
    runner = local_runner(root / "bucket")
    problems: list[str] = flip_phase(root, report, name)

    # The server is primary from here. It writes, and the PC mirrors and opens one item.
    with Store.open(root / "server", redactor=redact, name="server") as server:
        written = [
            server.put(
                OPERATOR,
                Draft(
                    "source",
                    f"doc-{index}",
                    title=f"document {index} made on the server",
                    blobs={
                        "content": f"bytes of document {index}".encode(),
                        "transcript": f"the words of document {index}".encode(),
                    },
                ),
                on="main",
                expected_head=None,
            )
            for index in range(ITEMS)
        ]
        contents = {
            index: server.get(OPERATOR, done.object_id).blobs for index, done in enumerate(written)
        }
        with Store.open(
            root / "pc",
            redactor=redact,
            name="pc",
            role="replica",
            upstream=Upstream(StorePeer(server)),
        ) as pc:
            sync_since(StorePeer(pc), StorePeer(server), OwnerTable("server"), cursor=0)
            opened = pc.read_blob(contents[0]["content"].blob_id)
            if hashlib.sha256(opened).hexdigest() != contents[0]["content"].blob_id.split(":")[1]:
                problems.append("the blob the PC opened does not hash to its id")
            expected_lost = {contents[index]["content"].blob_id for index in range(1, ITEMS)}
            transcripts = {found["transcript"].blob_id for found in contents.values()}
            objects = set(server.object_ids())
            pushed = Bucket(server, remote="scratch" if bucket else None, runner=runner).push()
            if bucket and not pushed.ok:
                problems.append(f"the bucket push failed: {pushed.said}")
            if not bucket and pushed.said != "no bucket, one copy on the server":
                problems.append(f"the push without a bucket said {pushed.said!r}")
            held = [
                path.relative_to(root / "bucket").as_posix()
                for path in (root / "bucket").rglob("*")
                if path.is_file()
            ]
            report.note(f"{name}: the bucket came to hold {len(held)} files after one push")
            if bucket and not held:
                problems.append("the bucket push left nothing in the scratch folder")
    shutil.rmtree(root / "server")

    # MIGRATION "When the server is lost", steps 1 to 6, on the PC that is now primary.
    with Store.open(root / "pc", redactor=redact, name="pc") as pc:
        if not bucket:

            def rebuild() -> dict[str, object]:
                with Store.open(
                    root / "server", redactor=redact, name="server", role="replica"
                ) as fresh:
                    done = sync(StorePeer(pc), StorePeer(fresh), OwnerTable("pc"))
                return {
                    "restored": True,
                    "objects": len(done.pulled),
                    "refs": len(done.pushed_refs),
                }
        else:

            def rebuild() -> dict[str, object]:
                return node.rebuild(
                    root / "server-home", remote="scratch", root=root / "server", runner=runner
                )

        def repair() -> str:
            code = node.pairing_code()
            left = node.pair(root / "pc-home", code)
            right = node.pair(root / "server-home", code)
            if (
                hashlib.sha256(left.read_bytes()).digest()
                != hashlib.sha256(right.read_bytes()).digest()
            ):
                return "the two ends hold different codes"
            return "paired"

        recovery = server_lost(
            pc,
            who=OPERATOR,
            reachable=bucket,
            bucket=bucket,
            rebuild=rebuild,
            repair=repair,
        )
        promoted = pc.epoch
        if promoted is None or (promoted.primary, promoted.epoch) != ("pc", 2):
            problems.append(f"the promotion left {promoted}")
        if not bucket and promoted is not None and recovery.steps[0].said.startswith("Stop"):
            problems.append("a dead server was asked to stop its host")
        if bucket and not recovery.steps[0].said.startswith("Stop the old host"):
            problems.append("a reachable old host was not asked to stop")
        if not recovery.stale:
            problems.append("the procedure listed no ref the server owned")
        if recovery.steps[4].said != "paired":
            problems.append(f"the re-pair said {recovery.steps[4].said!r}")
        if not (root / "server-home" / "vault" / "pairing-key").is_file():
            problems.append("the new server holds no pairing code")

        # What came back, and what did not.
        with Store.open(root / "server", redactor=redact, name="server") as restored:
            back = [object_id for object_id in objects if restored.has_object(object_id)]
            if len(back) != len(objects):
                problems.append(
                    f"{len(objects) - len(back)} objects the bucket held did not come back"
                )
            if bucket:
                hashes = 0
                for object_id in back:
                    manifest = restored.manifest(object_id) or {}
                    for blob in (manifest.get("blobs") or {}).values():
                        blob_id = str(blob["sha256"])
                        if not restored.has_blob(blob_id):
                            problems.append(f"{blob_id} the bucket held did not come back")
                            continue
                        if (
                            hashlib.sha256(restored.read_blob(blob_id)).hexdigest()
                            == blob_id.split(":")[1]
                        ):
                            hashes += 1
                        else:
                            problems.append(f"{blob_id} came back with other bytes")
                report.note(f"{name}: {hashes} blobs read back by hash, {len(objects)} objects")
            else:
                lost = recovery.lost
                if lost is None:
                    problems.append("the procedure named nothing lost")
                else:
                    if set(lost.blobs) != expected_lost:
                        problems.append(
                            f"the lost list is {len(lost.blobs)} blobs, not {len(expected_lost)}"
                        )
                    if set(lost.slots) != {"content"}:
                        problems.append(f"the lost slots are {lost.slots}")
                    for transcript in sorted(transcripts):
                        if transcript in lost.blobs:
                            problems.append(f"a text slot {transcript} was named lost")
                        if not restored.has_blob(transcript):
                            problems.append(f"the text slot {transcript} did not come back")
                    for blob_id in sorted(expected_lost):
                        if restored.has_blob(blob_id):
                            problems.append(f"{blob_id} was named lost and came back")
                    report.note(
                        f"{name}: lost {len(lost.blobs)} blobs ({', '.join(lost.slots)}), "
                        f"{len(transcripts)} text slots kept"
                    )
            # The two ref logs agree on every ref the PC owns.
        with Store.open(root / "server", redactor=redact, name="server", role="replica") as replica:
            sync(StorePeer(pc), StorePeer(replica), OwnerTable("pc"))
            table = OwnerTable("pc")
            mine = {(row.item, row.ref): row.head for row in StorePeer(pc).refs()}
            theirs = {(row.item, row.ref): row.head for row in StorePeer(replica).refs()}
            agreed = 0
            for (item, ref), head in mine.items():
                if table.owner(ref) not in ("pc", "either"):
                    continue
                if theirs.get((item, ref)) != head:
                    problems.append(f"{item} {ref} agrees on neither side")
                else:
                    agreed += 1
            if mine and agreed < 2:
                problems.append(f"only {agreed} refs were compared")
            report.note(f"{name}: {agreed} refs agree, {len(recovery.stale)} may be behind")
        report.note(
            f"{name}: steps done {recovery.done}, epoch {recovery.epoch}, "
            f"promoted {promoted.primary}"
        )

    for problem in problems:
        report.fail(f"{name}: {problem}")
    if not problems:
        report.note(f"{name}: PASS")
    if not bucket:
        report.numbers["lost"] = recovery.lost.said if recovery.lost is not None else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument(
        "--branch",
        choices=("all", "flip", "bucket", "no-bucket"),
        default="all",
        help="`flip` is lane 4, `bucket` lane 2 and `no-bucket` lane 3",
    )
    arguments = parser.parse_args(argv)
    report = Report(probe="P-SERVERLOST")
    try:
        if arguments.branch == "flip":
            root = SCRATCH / "p-serverlost" / "flip"
            shutil.rmtree(root, ignore_errors=True)
            for folder in ("pc", "server", "pc-home"):
                (root / folder).mkdir(parents=True)
            problems = flip_phase(root, report, "flip")
            problems += after_the_flip(root, report, "flip")
            for problem in problems:
                report.fail(f"flip: {problem}")
            if not problems:
                report.note("flip: PASS")
        else:
            for name, bucket in (("bucket", True), ("no-bucket", False)):
                if arguments.branch in ("all", name):
                    run_branch(name, bucket=bucket, report=report)
    finally:
        if not arguments.keep:
            shutil.rmtree(SCRATCH / "p-serverlost", ignore_errors=True)
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
