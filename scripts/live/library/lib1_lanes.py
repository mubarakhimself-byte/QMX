"""LIB1's own live lanes on the real Library store.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/library/lib1_lanes.py [lane ...]`
Lanes are `refs redact rebuild governed secrets processes perf`; none named runs `refs redact`.
Each writes `<LIB1_EVIDENCE>/<LIB1_LOG_PREFIX>lib1-<lane>.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/lib1`, prefix `owner-` for the builder, `check-` for the
coordinator), on a throwaway store under `D:/QMX-worktrees/qma-ship/build/homes/lib1-<lane>`, and
the script exits 1 if any lane failed. No model, no key, no ship home, no lane lock.

- `refs` (lane 3): two agents check out one draft into their own refs and commit there; each
  write to the other's ref, and a put onto the draft, is refused; both merge into the draft, the
  second three ways, and the draft ends holding both edits.
- `redact` (lane 4): a run puts an artifact holding a planted key through the engine adapter; the
  stored blob and manifest on disk hold no key.
- `rebuild` (lane 5): every index file is deleted and rebuilt from evidence; search answers the
  same.
- `governed` (lane 6): a passed live run's `book` waits on `refs/drafts/<item>`; `main` is empty.
- `secrets` (lane 9): `tools/secret_scan.py` is clean.
- `processes` (lane 10): no `qmx_host`, `claude` or `qma-cli-launcher` process on a LIB1 lane
  home (the operator's own Claude app and other builders' hosts are not this PR's) and no lane
  lock.
- `perf`: `put` and `get` p95 in ms on a store seeded with 1,000 objects of each of ten kinds,
  against `library_fake.py` on the same calls. It records numbers and fails nothing.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Final

import psutil
from qmx_engine.ledger import redact
from qmx_engine.ports.library_fake import LibraryFake
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.landing import land
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = Path(os.environ.get("LIB1_EVIDENCE", str(BUILD / "evidence" / "lib1")))
PREFIX: Final = os.environ.get("LIB1_LOG_PREFIX", "owner-")
ROOT: Final = Path(__file__).resolve().parents[3]
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
OPERATOR: Final = Principal("operator")
ALICE: Final = Principal("agent", "alice")
BOB: Final = Principal("agent", "bob")
PLANTED: Final = "sk-or-" + "v1-" + "7b" * 32
SEED_KINDS: Final = (
    "note",
    "artifact",
    "source",
    "test-report",
    "paper-run",
    "stress-scenario",
    "setup",
    "dataset",
    "collection",
    "hypothesis",
)
SEED_EACH: Final = 1000
SAMPLES: Final = 300


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}lib1-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> bool:
        self("PASS" if self.passed else "FAIL")
        return self.passed


def home(slug: str) -> Path:
    root = BUILD / "homes" / f"lib1-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def refused(call: Callable[[], object]) -> str:
    try:
        call()
    except LibraryRefused as error:
        return error.code
    return "accepted"


def workflow(name: str, notes: str) -> Draft:
    definition = json.dumps({"id": "brief", "name": name}).encode()
    blobs = {"definition": definition, "files/notes.md": notes.encode()}
    return Draft("workflow", "brief", title=name, blobs=blobs)


def lane_refs() -> bool:
    log = Log("refs")
    with Store.open(home("refs") / "library", redactor=redact) as store:
        base = store.put(
            OPERATOR, workflow("Morning brief", "v1"), on="refs/drafts/brief", expected_head=None
        )
        log(f"operator draft {base.object_id} on {base.ref}")
        alice_copy = store.checkout(ALICE, "brief", "refs/drafts/brief")
        bob_copy = store.checkout(BOB, "brief", "refs/drafts/brief")
        (alice_copy / "blobs" / "files" / "notes.md").write_text("v2: Alice's notes", "utf-8")
        definition = json.dumps({"id": "brief", "name": "Morning brief, by Bob"}).encode()
        (bob_copy / "blobs" / "definition").write_bytes(definition)
        alice = store.commit(ALICE, alice_copy, "notes")
        bob = store.commit(BOB, bob_copy, "rename")
        log(f"alice committed {alice.object_id} on {alice.ref}")
        log(f"bob committed {bob.object_id} on {bob.ref}")
        log.check(
            "each agent's commit landed on its own ref",
            (alice.ref, bob.ref) == ("refs/agents/alice/brief", "refs/agents/bob/brief"),
            (alice.ref, bob.ref),
        )
        cross = refused(
            lambda: store.put(
                BOB,
                workflow("Bob writes Alice's ref", "x"),
                on="refs/agents/alice/brief",
                expected_head=alice.object_id,
            )
        )
        onto = refused(
            lambda: store.put(
                BOB,
                workflow("Bob writes the draft", "x"),
                on="refs/drafts/brief",
                expected_head=base.object_id,
            )
        )
        log.check("Bob's write to Alice's ref is refused", cross == "ref_not_owned", cross)
        log.check("Bob's put onto the draft is refused", onto == "ref_not_owned", onto)
        first = store.merge(ALICE, "brief", from_ref=alice.ref, into="refs/drafts/brief")
        second = store.merge(BOB, "brief", from_ref=bob.ref, into="refs/drafts/brief")
        log(f"alice merge: {first.outcome}; bob merge: {second.outcome} {second.object_id}")
        merged = store.get(OPERATOR, second.object_id, blobs="fetch")
        name = json.loads(merged.data["definition"])["name"]
        log.check(
            "the draft holds both edits after a fast-forward and a three-way merge",
            (first.outcome, second.outcome, name, merged.data["files/notes.md"])
            == ("fast-forward", "merged", "Morning brief, by Bob", b"v2: Alice's notes"),
            (first.outcome, second.outcome, name),
        )
        log.check(
            "the merged object records merged-from both sides",
            {("merged-from", alice.object_id), ("merged-from", bob.object_id)}
            <= set(merged.relations),
            merged.relations,
        )
    return log.verdict()


def lane_redact() -> bool:
    log = Log("redact")
    root = home("redact") / "library"
    with Store.open(root, redactor=redact) as store:
        adapter = EngineLibraryAdapter(store)
        stored = adapter.put_artifact(
            f"step log\nOPENROUTER_API_KEY={PLANTED}\nupstream said key_{PLANTED}\n".encode(),
            "run-file",
            {"path": "logs/step.txt", "note": f"carried {PLANTED}"},
            run_id="r-redact",
            principal="run:r-redact",
        )
        log(f"artifact {stored.object_id} blob {stored.blob}")
        data = adapter.get_artifact(str(stored.blob))
    files = [p for d in ("objects", "blobs", "refs", "annotations") for p in (root / d).rglob("*")]
    holding = [str(p) for p in files if p.is_file() and PLANTED.encode() in p.read_bytes()]
    log(f"stored bytes: {data!r}")
    log.check("the stored blob holds no key", PLANTED.encode() not in data, len(data))
    log.check("the stored blob says where it redacted", b"[redacted" in data, data.count(b"["))
    log.check("no evidence file on disk holds the key", holding == [], holding)
    return log.verdict()


def seed(store: Store, each: int) -> None:
    for kind in SEED_KINDS:
        for n in range(each):
            draft = Draft(kind, title=f"{kind} number {n} about momentum {n % 37}")
            store.put(OPERATOR, draft, on="main", expected_head=None)


def lane_rebuild() -> bool:
    log = Log("rebuild")
    root = home("rebuild") / "library"
    queries = ("momentum 3", "note number 12", "dataset", "hypothesis momentum 30", "setup 7")
    with Store.open(root, redactor=redact) as store:
        seed(store, 50)
        before = {q: [h.object_id for h in store.search(OPERATOR, q, limit=50)] for q in queries}
    removed = [p.name for p in root.glob("catalog.db*")]
    for path in root.glob("catalog.db*"):
        path.unlink()
    log(f"deleted {removed}")
    began = time.perf_counter()
    with Store.open(root, redactor=redact) as store:
        log(f"reopened and rebuilt in {time.perf_counter() - began:.2f} s")
        after = {q: [h.object_id for h in store.search(OPERATOR, q, limit=50)] for q in queries}
    for query in queries:
        log(f"{query!r}: {len(before[query])} hits before, {len(after[query])} after")
    log.check(
        "search answers the same after the rebuild", after == before, sum(map(len, after.values()))
    )
    log.check(
        "the searches found something", all(before.values()), {q: len(v) for q, v in before.items()}
    )
    return log.verdict()


def lane_governed() -> bool:
    log = Log("governed")
    run = Principal("run", "r-gov")
    with Store.open(home("governed") / "library", redactor=redact) as store:
        made = store.put(
            run,
            Draft("book", "book-1", title="Compiled book"),
            on="refs/runs/r-gov",
            expected_head=None,
        )
        note = store.put(
            run,
            Draft("note", "note-1", title="Compile notes"),
            on="refs/runs/r-gov",
            expected_head=None,
        )
        landed = land(store, "r-gov", mode="live", status="passed")
        for each in landed:
            log(f"landed {each.item} into {each.into}: {each.result.outcome}")
        log.check(
            "the governed book waits on its drafts ref",
            store.head("book-1", "refs/drafts/book-1") == (made.object_id, 1),
            store.head("book-1", "refs/drafts/book-1"),
        )
        log.check(
            "main holds no book", store.head("book-1", "main") is None, store.head("book-1", "main")
        )
        on_main = store.head("note-1", "main")
        log.check("the run's record landed on main", on_main == (note.object_id, 1), on_main)
        forced = refused(
            lambda: store.merge(store.engine, "book-1", from_ref="refs/runs/r-gov", into="main")
        )
        log.check(
            "the engine cannot land a governed object on main", forced == "ref_not_owned", forced
        )
    return log.verdict()


def lane_secrets() -> bool:
    log = Log("secrets")
    done = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "secret_scan.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    for line in (done.stdout + done.stderr).splitlines():
        log(line)
    log.check("the secret scan is clean", done.returncode == 0, done.returncode)
    return log.verdict()


def lane_processes() -> bool:
    log = Log("processes")
    found: list[str] = []
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            line = " ".join(process.info["cmdline"] or [])
            name = str(process.info["name"] or "").lower()
        except psutil.Error:
            continue
        mine = "lib1-" in line
        host = name.startswith("python") and "qmx_host" in line
        if mine and (host or name.startswith(("claude", "qma-cli-launcher"))):
            found.append(f"{process.info['pid']} {name} {line[:160]}")
    for row in found:
        log(f"  {row}")
    log.check("no qmx_host, claude or qma-cli-launcher process is left", found == [], len(found))
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK)
    return log.verdict()


def p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def timed(call: Callable[[], object]) -> float:
    began = time.perf_counter()
    call()
    return (time.perf_counter() - began) * 1000


def lane_perf() -> bool:
    log = Log("perf")
    root = home("perf")
    began = time.perf_counter()
    with Store.open(root / "library", redactor=redact) as store:
        seed(store, SEED_EACH)
        log(f"seeded {len(SEED_KINDS) * SEED_EACH} objects in {time.perf_counter() - began:.1f} s")
        real = EngineLibraryAdapter(store)
        puts = [
            timed(
                lambda n=n: real.put_artifact(
                    f"body {n}".encode(),
                    "run-file",
                    {"n": n},
                    run_id="r-perf",
                    principal="run:r-perf",
                )
            )
            for n in range(SAMPLES)
        ]
        ids = [head for _, head in store.heads_on("main")][:SAMPLES]
        gets = [timed(lambda o=o: store.get(OPERATOR, o, blobs="fetch")) for o in ids]
    with LibraryFake.open(root / "fake") as fake:
        began = time.perf_counter()
        seeded = [
            fake.put_artifact(
                f"seed {n}".encode(), "run-file", {"n": n}, run_id="r-seed", principal="run:r-seed"
            ).object_id
            for n in range(len(SEED_KINDS) * SEED_EACH)
        ]
        log(f"seeded the fake with {len(seeded)} objects in {time.perf_counter() - began:.1f} s")
        fake_puts = [
            timed(
                lambda n=n: fake.put_artifact(
                    f"body {n}".encode(),
                    "run-file",
                    {"n": n},
                    run_id="r-perf",
                    principal="run:r-perf",
                )
            )
            for n in range(SAMPLES)
        ]
        fake_gets = [timed(lambda o=o: fake.get(o)) for o in seeded[:SAMPLES]]
    log(f"Library store: put p95 {p95(puts):.2f} ms, get p95 {p95(gets):.2f} ms, {SAMPLES} each")
    log(f"library_fake:  put p95 {p95(fake_puts):.2f} ms, get p95 {p95(fake_gets):.2f} ms")
    log("no fail rule (LIB1 perf box); P-LAT measures the server case in LIB4")
    return log.verdict()


LANES: Final = {
    "refs": lane_refs,
    "redact": lane_redact,
    "rebuild": lane_rebuild,
    "governed": lane_governed,
    "secrets": lane_secrets,
    "processes": lane_processes,
    "perf": lane_perf,
}


def main() -> int:
    named = sys.argv[1:] or ["refs", "redact"]
    results = {name: LANES[name]() for name in named}
    print(json.dumps(results))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
