"""LIB3's live lanes: P-SRCH's questions on the migrated Library, under noise, and the curator.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/library/lib3_search.py [lane ...]`
Lanes are `srch noise curator pod none asof rebuild secrets processes`; none named runs
`srch noise curator`. Each writes `<LIB3_EVIDENCE>/<LIB3_LOG_PREFIX>lib3-<lane>.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/lib3`, prefix `owner-`, `check-` for the coordinator)
on a fresh copy of the migrated store under `D:/QMX-worktrees/qma-ship/build/homes/lib3-<lane>`,
and the script exits 1 if any lane failed. No model, no key, no ship home, no lane lock.

The migrated store is LIBM's import of his home (`LIB3_SOURCE`, default LIBM's `import` lane
store): his Library B items plus LIBM's registry and app fixtures. `questions.json` was written
over his `library.db` of 2026-10-18; a remote-flow item imported since then is one the set cannot
judge, so scoring skips it and logs how many it skipped.

- `srch` (lane 2): precision at least 0.85 at coverage at least 0.70 over the 40 questions, and
  the preview cut keeps every top 5. Also the perf block: search p95 over three passes, beside
  the FTS5 `search` verb of LIB1 on the same questions.
- `noise` (lane 3): 5,000 newer test-run copies of the store's items, 50 runs of 100; every top 5
  holds.
- `curator` (lane 4): test records 31 days old on the fake clock; uncited ones are archived, cited,
  young and live ones stay, and no object or blob file goes.
- `pod` (the "You see" box), `none` (lane 6), `asof` (lane 7), `rebuild` (lane 8), `secrets`
  (lane 9), `processes` (lane 10).
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

import psutil
from qmx_engine.ledger import redact
from qmx_library.curator import curate
from qmx_library.port import Answer, Draft, JsonObject, LibraryRefused, ObjectId
from qmx_library.principal import Principal
from qmx_library.search import PREVIEW_CHARS, answer
from qmx_library.store import Store

BUILD: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = Path(os.environ.get("LIB3_EVIDENCE", str(BUILD / "evidence" / "lib3")))
PREFIX: Final = os.environ.get("LIB3_LOG_PREFIX", "owner-")
SOURCE: Final = Path(
    os.environ.get(
        "LIB3_SOURCE", str(BUILD / "homes" / "libm-import" / "migration" / "dry" / "library")
    )
)
ROOT: Final = Path(__file__).resolve().parents[3]
QUESTIONS: Final = ROOT / "scripts" / "live" / "library" / "questions.json"
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
OPERATOR: Final = Principal("operator")
TOP: Final = 5
PASS_PRECISION: Final = 0.85
PASS_COVERAGE: Final = 0.70
NOISE_RUNS: Final = 50
NOISE_PER_RUN: Final = 100
PASSES: Final = 3


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{PREFIX}lib3-{slug}.log"
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


class Clock:
    def __init__(self) -> None:
        self.now = datetime.now(UTC)

    def __call__(self) -> datetime:
        return self.now


@contextmanager
def copied(slug: str, clock: Clock | None = None) -> Generator[Store]:
    """A fresh copy of the migrated store; the source is only read."""
    root = BUILD / "homes" / f"lib3-{slug}" / "library"
    shutil.rmtree(root.parent, ignore_errors=True)
    shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns("writer.lock"))
    with Store.open(root, redactor=redact, wall=clock) as store:
        yield store


@dataclass(frozen=True, slots=True)
class Question:
    text: str
    expected: frozenset[str]


def questions() -> list[Question]:
    rows = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    return [Question(q["question"], frozenset(q["expected"])) for q in rows]


def legacy_id(store: Store, object_id: ObjectId) -> str | None:
    found = store.get(OPERATOR, object_id).fields.get("legacy_id")
    return None if found is None else str(found)


@dataclass(frozen=True, slots=True)
class Score:
    precision: float
    coverage: float
    answered: int
    answerable: int
    unjudged: int


def judged(found: Answer) -> bool:
    return found.refused is None and not found.abstain


def score(store: Store, asked: Sequence[Question], answers: Sequence[Answer]) -> Score:
    """Precision: answered questions whose first judgeable result is expected; an answer to a
    question that expects an abstention is wrong. Coverage: answerable questions answered."""
    known = frozenset[str]().union(*(q.expected for q in asked))
    answered = right = covered = unjudged = 0
    for question, found in zip(asked, answers, strict=True):
        if not judged(found):
            continue
        answered += 1
        covered += bool(question.expected)
        for result in found.results:
            legacy = legacy_id(store, result.object_id)
            if legacy is not None and legacy not in known:
                unjudged += 1
                continue
            right += legacy in question.expected
            break
    answerable = sum(bool(q.expected) for q in asked)
    return Score(
        right / answered if answered else 0.0,
        covered / answerable if answerable else 0.0,
        answered,
        answerable,
        unjudged,
    )


def top(found: Answer) -> list[str]:
    return [r.object_id for r in found.results[:TOP]]


def p95(samples: Sequence[float]) -> float:
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def distinct(store: Store) -> int:
    rows = store.catalog.db.execute(
        "SELECT DISTINCT o.kind, o.title, s.text FROM objects o "
        "JOIN items i ON i.item = o.item AND i.state = 'active' "
        "LEFT JOIN search s ON s.object_id = o.object_id"
    )
    return len(rows.fetchall())


def ask_all(store: Store, asked: Sequence[Question], log: Log | None = None) -> list[Answer]:
    answers = [answer(store, OPERATOR, q.text) for q in asked]
    if log is not None:
        for question, found in zip(asked, answers, strict=True):
            shown = found.refused or ("abstain" if found.abstain else f"{len(found.results)} hits")
            first = found.results[0].title if found.results and judged(found) else "-"
            log(
                f"  {question.text!r}: confidence {found.confidence:.2f} -> {shown}; "
                f"first {first!r}; expects {'ids' if question.expected else 'abstain'}"
            )
    return answers


def scored(log: Log, store: Store, asked: Sequence[Question]) -> tuple[Score, list[Answer]]:
    answers = ask_all(store, asked, log)
    found = score(store, asked, answers)
    log(
        f"precision {found.precision:.3f}, coverage {found.coverage:.3f} "
        f"({found.answered} answered, {found.answerable} answerable, "
        f"{found.unjudged} results the set cannot judge skipped)"
    )
    return found, answers


def timed(store: Store, asked: Sequence[Question]) -> tuple[list[float], list[float]]:
    """Milliseconds of `answer` and of the FTS5 `search` verb, per question, `PASSES` times."""
    times: list[float] = []
    baseline: list[float] = []
    for _ in range(PASSES):
        for question in asked:
            started = time.perf_counter()
            answer(store, OPERATOR, question.text)
            times.append((time.perf_counter() - started) * 1000)
            started = time.perf_counter()
            with suppress(LibraryRefused):
                store.search(OPERATOR, question.text)
            baseline.append((time.perf_counter() - started) * 1000)
    return times, baseline


def lane_srch() -> bool:
    log = Log("srch")
    asked = questions()
    with copied("srch") as store:
        count = distinct(store)
        log(f"store {SOURCE}: {count} distinct active objects, {len(asked)} questions")
        log.check("the store can score a wrong grounding", count >= 2, count)
        found, answers = scored(log, store, asked)
        log.check(
            f"precision at least {PASS_PRECISION} at coverage at least {PASS_COVERAGE}",
            found.precision >= PASS_PRECISION and found.coverage >= PASS_COVERAGE,
            (round(found.precision, 3), round(found.coverage, 3)),
        )
        whole = [answer(store, OPERATOR, q.text, preview_chars=None) for q in asked]
        moved = [q.text for q, a, w in zip(asked, answers, whole, strict=True) if top(a) != top(w)]
        log.check(
            f"the preview cut at {PREVIEW_CHARS} characters keeps every top {TOP}", not moved, moved
        )
        times, baseline = timed(store, asked)
        log(
            f"perf: search p95 {p95(times):.2f} ms over {len(times)} calls; LIB1 FTS5 search "
            f"p95 {p95(baseline):.2f} ms; cpu {psutil.cpu_percent(interval=0.5)} %"
        )
    return log.verdict()


def noise(store: Store) -> int:
    """`NOISE_RUNS` test runs, each fanning out `NOISE_PER_RUN` copies of the store's titles."""
    titles = [
        str(t)
        for (t,) in store.catalog.db.execute(
            "SELECT DISTINCT o.title FROM objects o JOIN items i ON i.item = o.item "
            "WHERE i.state = 'active' AND o.title <> '' ORDER BY o.title"
        )
    ]
    made = 0
    for n in range(NOISE_RUNS):
        run_id = f"lib3-noise-{n:02d}"
        run = Principal("run", run_id)
        ref = f"refs/runs/{run_id}"
        fields: JsonObject = {"run_id": run_id, "mode": "test", "status": "passed"}
        store.put(run, Draft("workflow-run", run_id, fields=fields), on=ref, expected_head=None)
        for k in range(NOISE_PER_RUN):
            title = titles[(n * NOISE_PER_RUN + k) % len(titles)]
            body = f"{title} fan-out attempt {k} of {run_id}".encode()
            draft = Draft("artifact", title=title, blobs={"content": body})
            store.put(run, draft, on=ref, expected_head=None)
            made += 1
    return made


def lane_noise() -> bool:
    log = Log("noise")
    asked = questions()
    with copied("noise") as store:
        before = ask_all(store, asked)
        started = time.perf_counter()
        made = noise(store)
        log(f"added {made} test-run records in {time.perf_counter() - started:.1f} s")
        found, after = scored(log, store, asked)
        moved = [
            q.text
            for q, b, a in zip(asked, before, after, strict=True)
            if judged(b) and top(b) != top(a)
        ]
        log.check(f"every answered top {TOP} holds under the noise", not moved, moved)
        firsts = {r.results[0].producer for r in after if judged(r) and r.results}
        log.check("no test-run record ranks first", "test-run" not in firsts, sorted(firsts))
        log.check(
            f"precision at least {PASS_PRECISION} at coverage at least {PASS_COVERAGE}",
            found.precision >= PASS_PRECISION and found.coverage >= PASS_COVERAGE,
            (round(found.precision, 3), round(found.coverage, 3)),
        )
        times, baseline = timed(store, asked)
        log(
            f"perf under noise: search p95 {p95(times):.2f} ms over {len(times)} calls; "
            f"LIB1 FTS5 search p95 {p95(baseline):.2f} ms"
        )
    return log.verdict()


def records(store: Store, run_id: str, mode: str, *titles: str) -> list[str]:
    run = Principal("run", run_id)
    ref = f"refs/runs/{run_id}"
    fields: JsonObject = {"run_id": run_id, "mode": mode, "status": "passed"}
    store.put(run, Draft("workflow-run", run_id, fields=fields), on=ref, expected_head=None)
    return [
        store.put(
            run,
            Draft("artifact", title=t, blobs={"content": t.encode()}),
            on=ref,
            expected_head=None,
        ).item
        for t in titles
    ]


def files(store: Store) -> list[str]:
    return sorted(
        str(p.relative_to(store.root))
        for folder in ("objects", "blobs")
        for p in (store.root / folder).rglob("*")
        if p.is_file()
    )


def lane_curator() -> bool:
    log = Log("curator")
    clock = Clock()
    with copied("curator", clock) as store:
        his = {str(i) for (i,) in store.catalog.db.execute("SELECT item FROM items")}
        old = records(store, "lib3-test-old", "test", "probe output a", "probe output b")
        cited = records(store, "lib3-test-cited", "test", "cited probe output")
        head = store.resolve(OPERATOR, cited[0], "refs/runs/lib3-test-cited")
        store.put(
            OPERATOR,
            Draft("note", title="Probe review", relations=[("cites", head)]),
            on="main",
            expected_head=None,
        )
        live = records(store, "lib3-live-old", "live", "live output")
        clock.now += timedelta(days=20)
        young = records(store, "lib3-test-young", "test", "young probe output")
        clock.now += timedelta(days=11)
        kept = files(store)
        archived = curate(store, now=clock.now)
        log(f"archived {archived}")
        want = sorted([*old, "lib3-test-old", "lib3-test-cited"])
        log.check("the old uncited test records are archived", archived == want, len(archived))
        stays = [*cited, *live, *young, "lib3-live-old", "lib3-test-young", *his]
        active = [i for i in stays if store.catalog.state(i) == "active"]
        log.check(
            "cited, live, young and his own items stay active",
            len(active) == len(stays),
            f"{len(active)} of {len(stays)}",
        )
        log.check("no object or blob file is deleted", files(store) == kept, len(kept))
        log.check(
            "the archived records are still readable",
            all(
                store.get(OPERATOR, store.resolve(OPERATOR, i, "refs/runs/lib3-test-old"))
                for i in old
            ),
            len(old),
        )
        again = curate(store, now=clock.now)
        log.check("a second run archives nothing", again == [], again)
        hidden = answer(store, OPERATOR, "probe output a")
        log.check(
            "search no longer shows them",
            hidden.refused == "only_archived_or_superseded",
            hidden.refused,
        )
    return log.verdict()


def lane_pod() -> bool:
    log = Log("pod")
    with copied("pod") as store:
        pod = store.put(
            OPERATOR,
            Draft("pod", "pod-london", title="London breakout pod"),
            on="refs/drafts/pod-london",
            expected_head=None,
        ).object_id
        for title, relation in [
            ("London breakout study", "uses"),
            ("Breakout idea", "derived-from"),
        ]:
            draft = Draft("note", title=title, relations=[(relation, pod)])
            store.put(OPERATOR, draft, on="main", expected_head=None)
        found = answer(store, OPERATOR, "what did we decide about the London breakout pod")
        for r in found.results:
            log(f"  {r.title!r} ({r.kind}) via {r.via or 'its name'} from {r.source or '-'}")
        log.check(
            "the pod comes first", found.results[0].item == "pod-london", found.results[0].title
        )
        log.check(
            "every other result names the edge that admitted it",
            all(r.via and r.source == "pod-london" for r in found.results[1:]),
            [r.via for r in found.results[1:]],
        )
    return log.verdict()


def lane_none() -> bool:
    log = Log("none")
    with copied("none") as store:
        found = answer(store, OPERATOR, "kangaroo futures arbitrage")
        log.check("it reports nothing matched", found.refused == "no_entry_point", found.refused)
    return log.verdict()


def lane_asof() -> bool:
    log = Log("asof")
    clock = Clock()
    with copied("asof", clock) as store:
        then = clock.now
        clock.now += timedelta(days=2)
        store.put(OPERATOR, Draft("note", title="Tokyo fade plan"), on="main", expected_head=None)
        now = answer(store, OPERATOR, "the tokyo fade plan")
        past = answer(store, OPERATOR, "the tokyo fade plan", as_of=then)
        old = answer(store, OPERATOR, "the remote-flow result", as_of=then)
        log.check(
            "today the new plan answers",
            [r.title for r in now.results] == ["Tokyo fade plan"],
            now.refused,
        )
        log.check(
            "as of before it, nothing was alive", past.refused == "no_evidence_as_of", past.refused
        )
        log.check(
            "items alive then still answer",
            old.refused is None and bool(old.results),
            len(old.results),
        )
    return log.verdict()


def lane_rebuild() -> bool:
    log = Log("rebuild")
    asked = questions()
    with copied("rebuild") as store:
        first = score(store, asked, ask_all(store, asked))
        store.rebuild_indexes()
        again = score(store, asked, ask_all(store, asked))
        log(f"before {first}; after {again}")
        log.check("the scores match after the rebuild", first == again, again)
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
        host = name.startswith("python") and "qmx_host" in line
        if "lib3-" in line and (host or name.startswith(("claude", "qma-cli-launcher"))):
            found.append(f"{process.info['pid']} {name} {line[:160]}")
    for row in found:
        log(f"  {row}")
    log.check("no qmx_host, claude or qma-cli-launcher process is left", found == [], len(found))
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK)
    return log.verdict()


LANES: Final[dict[str, Callable[[], bool]]] = {
    "srch": lane_srch,
    "noise": lane_noise,
    "curator": lane_curator,
    "pod": lane_pod,
    "none": lane_none,
    "asof": lane_asof,
    "rebuild": lane_rebuild,
    "secrets": lane_secrets,
    "processes": lane_processes,
}


def main() -> int:
    named = sys.argv[1:] or ["srch", "noise", "curator"]
    results = {name: LANES[name]() for name in named}
    print(json.dumps(results))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
