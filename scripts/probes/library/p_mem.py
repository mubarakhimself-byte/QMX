"""P-MEM, PC half (engine AD-18, ruling 119, SOLUTION-DESIGN 28.8): embedded Hindsight against an
FTS5 index over the same rows, on his material.

The plan names his session transcripts as the source. Copying them out of `~/.claude` was refused
by the session's permission check, so the rows come from his written planning record instead:
every Markdown file under `tracker/qma-v2/` on `plan/agent-system` (his rulings, the studies and
the architecture, read with `git show`), cut at paragraphs, plus a read-only copy of his
`library.db` items. Both engines answer the same questions of the four types; a hit is relevant
when its text holds one of the question's answer phrases. Hindsight runs in-process
(`HindsightServer`, embedded pg0, its local embedder and reranker) with the bulk rows retained in
`chunks` mode, so both engines search the same rows. Observations are off on both banks:
consolidation would send every row to the extractor, and the binding rules run it only from
`consolidate`. A digest-sized text (the first 8,000 characters of his rulings file) is then
retained in the default `concise` mode with a DeepSeek extractor on the OpenRouter row (provider
proof); the key is read in-process from the keyring entry `qmx/openrouter` and never printed.
Memory is the peak over this process and pg0's Postgres for the probe instance (see `Peak`).

Runs in the throwaway venv under the store's `homes/prb-l/hs-venv`, with the model downloads in
`homes/prb-l/hs-home`. pg0 ignores the moved profile and keeps its instance in
`~/.pg0/instances/hindsight` on C:.

    D:/QMX-worktrees/qma-ship/build/homes/prb-l/hs-venv/Scripts/python.exe \
        scripts/probes/library/p_mem.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from common import (
    HIS_LIBRARY,
    HOMES,
    Log,
    Verdict,
    copy_read_only,
    redact,
    sha256_file,
)

HS_HOME: Final = HOMES / "hs-home"
SOURCES: Final = HOMES / "sources"
ROWS: Final = HOMES / "p_mem_rows.jsonl"
MODEL: Final = "deepseek/deepseek-v4.1-flash"
CHUNK_CHARS: Final = 1500
MIN_CHARS: Final = 80
PLAN_REPO: Final = Path("D:/QMX-worktrees/agent-system")
PLAN_REF: Final = "plan/agent-system"
GIT: Final = shutil.which("git") or "git"
DIGEST_SOURCE: Final = "26-operator-rulings-and-alignment"
"""The digest retained with the extractor: the first 8,000 characters of his rulings file, about
the size of a session digest."""
START_TIMEOUT_S: Final = 900.0
"""The first start downloads the embedder and reranker and unpacks Postgres."""
PG_DATA: Final = "/.pg0/instances/hindsight/data"
"""pg0 keeps its instances under the real user profile whatever USERPROFILE says."""
TOP: Final = 5
RSS_LIMIT_MB: Final = 2048
RETAIN_LIMIT_S: Final = 30.0
TYPES: Final = ("already-built", "dead-end", "lab-to-hub", "decided")
FALLBACK_RAM: Final = (
    "Hindsight stays on the PC and the server's runs recall through FTS5 over the same rows "
    "until the server grows."
)
FALLBACK_QUALITY: Final = "recorded and tuned; the choice of Hindsight stands (ruling 119)."
STOP: Final = frozenset(
    [
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "we",
        "our",
        "us",
        "you",
        "your",
        "it",
        "its",
        "this",
        "that",
        "what",
        "which",
        "who",
        "whom",
        "did",
        "do",
        "does",
        "done",
        "have",
        "has",
        "had",
        "with",
        "about",
        "from",
        "by",
        "at",
        "as",
        "how",
        "why",
        "when",
        "where",
        "there",
        "any",
        "some",
        "not",
        "no",
        "yes",
        "can",
        "could",
        "would",
        "should",
        "will",
        "just",
        "one",
        "all",
    ]
)


@dataclass(frozen=True)
class Row:
    row_id: str
    session: str
    text: str


@dataclass(frozen=True)
class Question:
    kind: str
    text: str
    answers: tuple[str, ...]
    """Lower-case phrases; a hit holding any of them is relevant."""


QUESTIONS: Final[tuple[Question, ...]] = (
    Question(
        "already-built",
        "Do we already have a fake model that answers test turns without spending?",
        ("fake_model",),
    ),
    Question(
        "already-built",
        "Is there an existing tool that scans the repo for leaked keys?",
        ("secret_scan",),
    ),
    Question(
        "already-built",
        "Has a validator for workflow definitions already been written?",
        ("validate.py",),
    ),
    Question(
        "already-built",
        "Does the apps supervisor already schedule runs on its own?",
        ("supervisor.py & interval",),
    ),
    Question(
        "already-built",
        "Is the check for work that was already built keyed on something deterministic?",
        ("check_built & intent key",),
    ),
    Question(
        "dead-end", "Why did we stop building the agents on LangGraph?", ("langgraph & superseded",)
    ),
    Question(
        "dead-end",
        "What became of the node kind that ran the Claude Code Workflow tool?",
        ("claude_workflow & retired",),
    ),
    Question(
        "dead-end",
        "Does certifying a graph path tell us whether an answer is right?",
        ("at chance",),
    ),
    Question(
        "dead-end",
        "What happened to the old software factory pipeline?",
        ("factory & retired", "bulk-worker"),
    ),
    Question(
        "dead-end", "Where do we record an idea that a test killed?", ("dead end & hypothesis",)
    ),
    Question(
        "lab-to-hub",
        "A Lab session noted something about a pod; how does a later hub session recall it?",
        ("pod p", "hub session & lab session"),
    ),
    Question(
        "lab-to-hub",
        "How does the Lab count the trials run on one strategy family?",
        ("family & trial count",),
    ),
    Question(
        "lab-to-hub",
        "Which edge records that a run opened the sealed holdout data?",
        ("touched & holdout",),
    ),
    Question(
        "lab-to-hub",
        "What links a pod version to the book compiled from it?",
        ("compiles-to & book",),
    ),
    Question(
        "lab-to-hub", "What checks run before a pod goes to paper trading?", ("send to paper",)
    ),
    Question(
        "decided",
        "Which memory engine did he settle on for workflows and the copilot?",
        ("hindsight & ruling 119",),
    ),
    Question("decided", "Who moves the main branch, and how?", ("squash-merge",)),
    Question("decided", "What did he rule about usage limits inside QMX?", ("usage cap & 106",)),
    Question("decided", "How often does a host send its heartbeat?", ("heartbeat & 30 s",)),
    Question("decided", "Which model rows come first in every role tier?", ("chinese rows",)),
)
"""Claude's default: five questions per type, written over this corpus because no labelled set
exists. An answer alternative joins phrases with ` & ` when all must appear."""


def plan_docs() -> list[tuple[str, str]]:
    """Every Markdown file under `tracker/qma-v2/` on `plan/agent-system`, archive and fetched
    sources left out, read with `git show` so no checkout changes."""
    names = subprocess.run(
        [GIT, "-C", str(PLAN_REPO), "ls-tree", "-r", "--name-only", PLAN_REF, "tracker/qma-v2"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    picked = [
        n for n in names if n.endswith(".md") and "/archive/" not in n and "/sources/" not in n
    ]
    return [
        (
            name,
            subprocess.run(
                [GIT, "-C", str(PLAN_REPO), "show", f"{PLAN_REF}:{name}"],
                capture_output=True,
                check=True,
            ).stdout.decode("utf-8", errors="replace"),
        )
        for name in picked
    ]


def chunks(text: str) -> Iterator[str]:
    """Paragraphs packed up to 1,500 characters; a longer paragraph is cut."""
    piece = ""
    for paragraph in re.split(r"\n\s*\n", text):
        if len(piece) + len(paragraph) > CHUNK_CHARS and len(piece) >= MIN_CHARS:
            yield piece.strip()
            piece = ""
        piece = f"{piece}\n\n{paragraph}" if piece else paragraph
        while len(piece) > CHUNK_CHARS:
            yield piece[:CHUNK_CHARS].strip()
            piece = piece[CHUNK_CHARS:]
    if len(piece.strip()) >= MIN_CHARS:
        yield piece.strip()


def doc_rows(name: str, text: str) -> Iterator[Row]:
    stem = Path(name).stem
    for n, piece in enumerate(chunks(redact(text))):
        yield Row(f"{stem[:24]}-{n:04d}", stem, piece)


def library_rows(path: Path) -> Iterator[Row]:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        for item_id, data in db.execute("SELECT id, data FROM items"):
            fields = json.loads(data)
            text = f"Library item {fields.get('kind')} {fields.get('title')}: {data}"
            yield Row(f"lib-{item_id[:8]}", "library", redact(text)[:CHUNK_CHARS])
    db.close()


def corpus(log: Log) -> tuple[list[Row], dict[Path, str]]:
    hashes = copy_read_only([HIS_LIBRARY], SOURCES)
    docs = plan_docs()
    rows = [r for name, text in docs for r in doc_rows(name, text)]
    rows += library_rows(SOURCES / HIS_LIBRARY.name)
    with ROWS.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row.__dict__) + "\n")
    log.say(f"corpus: {len(docs)} plan documents and his library.db, {len(rows)} rows")
    return rows, hashes


def terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2 and t not in STOP]


class Fts:
    """The backup adapter's shape: FTS5 over the rows, BM25, terms ORed."""

    def __init__(self, rows: Sequence[Row]) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE VIRTUAL TABLE rows USING fts5(row_id UNINDEXED, text)")
        self.db.executemany("INSERT INTO rows VALUES (?, ?)", [(r.row_id, r.text) for r in rows])

    def recall(self, query: str) -> list[str]:
        match = " OR ".join(f'"{t}"' for t in terms(query))
        found = self.db.execute(
            "SELECT text FROM rows WHERE rows MATCH ? ORDER BY bm25(rows) LIMIT ?", (match, TOP)
        )
        return [text for (text,) in found]


def holds(hit: str, question: Question) -> bool:
    text = hit.lower()
    return any(all(p in text for p in a.split(" & ")) for a in question.answers)


def relevant(hits: Sequence[str], question: Question) -> int:
    return sum(holds(hit, question) for hit in hits[:TOP])


def judge(
    scores: Mapping[str, Mapping[str, float]], memory_mb: float, retain_s: float | None
) -> Verdict:
    """`scores[engine][type]` is the mean count of relevant hits in the top 5. PASS when Hindsight
    matches or beats FTS5 on every type, peak memory is at most 2,048 MB, and the digest retain
    finished within 30 s."""
    numbers: dict[str, float | int | str] = {
        f"{engine}_{kind}": round(scores[engine][kind], 2)
        for kind in TYPES
        for engine in ("hindsight", "fts5")
    }
    numbers["memory_mb"] = round(memory_mb)
    numbers["retain_s"] = "none" if retain_s is None else round(retain_s, 1)
    if memory_mb > RSS_LIMIT_MB:
        return Verdict("P-MEM", "FAIL", numbers, "FAIL on RAM", FALLBACK_RAM)
    behind = [k for k in TYPES if scores["hindsight"][k] < scores["fts5"][k]]
    if behind:
        reason = f"FAIL on quality: Hindsight is behind FTS5 on {', '.join(behind)}"
        return Verdict("P-MEM", "FAIL", numbers, reason, FALLBACK_QUALITY)
    if retain_s is None or retain_s > RETAIN_LIMIT_S:
        reason = "FAIL on retain time: the digest retain did not finish within 30 s"
        return Verdict("P-MEM", "FAIL", numbers, reason, FALLBACK_QUALITY)
    return Verdict("P-MEM", "PASS", numbers, "Hindsight matches or beats FTS5 on every type")


class Peak:
    """Samples the memory of this process plus pg0's Postgres for the probe's instance (its
    postmaster, found by data folder, and every backend under it). Two sums are kept: the RSS
    sum, which counts Postgres's shared buffers once per backend, and the private-bytes sum,
    which counts each page once. The verdict reads the private sum; both are logged."""

    def __init__(self) -> None:
        import psutil  # noqa: PLC0415

        self.psutil = psutil
        self.peak_rss_mb = 0.0
        self.peak_private_mb = 0.0
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.watch, daemon=True)

    def tree(self) -> list[Any]:
        own = self.psutil.Process()
        found = [own]
        for proc in self.psutil.process_iter(["cmdline"]):
            line = " ".join(proc.info.get("cmdline") or []).replace("\\", "/").lower()
            if PG_DATA in line:
                found.append(proc)
                found.extend(proc.children(recursive=True))
        return found

    def current(self) -> tuple[float, float]:
        rss = private = 0
        for proc in self.tree():
            try:
                info = proc.memory_info()
            except self.psutil.Error:
                continue
            rss += info.rss
            private += getattr(info, "private", info.rss)
        return rss / 2**20, private / 2**20

    def watch(self) -> None:
        while not self.stop.is_set():
            rss, private = self.current()
            self.peak_rss_mb = max(self.peak_rss_mb, rss)
            self.peak_private_mb = max(self.peak_private_mb, private)
            self.stop.wait(1.0)

    def leftovers(self) -> list[str]:
        return [f"{p.pid} {p.name()}" for p in self.tree()[1:]]


def isolate() -> None:
    """Every home folder Hindsight, pg0 and the model downloads use, on D: under the probe home."""
    HS_HOME.mkdir(parents=True, exist_ok=True)
    for name in ("USERPROFILE", "HOME", "LOCALAPPDATA", "APPDATA"):
        os.environ[name] = str(HS_HOME)
    os.environ["HF_HOME"] = str(HS_HOME / "hf")
    os.environ["HINDSIGHT_API_EMBEDDINGS_PROVIDER"] = "local"
    os.environ["HINDSIGHT_API_RERANKER_PROVIDER"] = "local"


def openrouter_key() -> str:
    import keyring  # noqa: PLC0415

    key = keyring.get_password("qmx/openrouter", "openrouter")
    if not key:
        raise SystemExit("BLOCKED: no keyring entry qmx/openrouter")
    return key


def digest_of(rows: Sequence[Row], session: str) -> str:
    text = "\n\n".join(r.text for r in rows if r.session == session)
    return text[:8000]


def run_hindsight(
    log: Log, rows: Sequence[Row], peak: Peak
) -> tuple[dict[str, list[str]], float | None]:
    from hindsight import HindsightClient, HindsightServer  # noqa: PLC0415
    from pg0 import Pg0  # noqa: PLC0415

    key = openrouter_key()
    server = HindsightServer(
        db_url="pg0", llm_provider="openrouter", llm_api_key=key, llm_model=MODEL
    )
    del key
    answers: dict[str, list[str]] = {}
    retain_s: float | None = None
    server.start(timeout=START_TIMEOUT_S)
    try:
        client = HindsightClient(base_url=server.url, timeout=600)
        bank = f"prb-l-chunks-{int(time.time())}"
        client.create_bank(bank_id=bank, retain_extraction_mode="chunks", enable_observations=False)
        began = time.perf_counter()
        for start in range(0, len(rows), 200):
            batch = rows[start : start + 200]
            client.retain_batch(
                bank_id=bank,
                items=[
                    {"content": r.text, "document_id": r.row_id, "tags": [r.session]} for r in batch
                ],
            )
        log.say(f"hindsight chunks retain of {len(rows)} rows: {time.perf_counter() - began:.0f} s")
        log.say(f"rss after bulk retain {peak.current()[1]:.0f} MB private")
        for q in QUESTIONS:
            found = client.recall(bank_id=bank, query=q.text, budget="mid", max_tokens=4096)
            answers[q.text] = [r.text for r in found.results[:TOP]]
        digest_bank = f"prb-l-digest-{int(time.time())}"
        client.create_bank(bank_id=digest_bank, enable_observations=False)
        session = DIGEST_SOURCE
        began = time.perf_counter()
        try:
            client.retain(
                bank_id=digest_bank, content=digest_of(rows, session), document_id=session
            )
            retain_s = time.perf_counter() - began
            facts = client.recall(bank_id=digest_bank, query="what was decided", budget="low")
            log.say(
                f"digest retain ({MODEL}, {session}): {retain_s:.1f} s, "
                f"{len(facts.results)} facts recalled"
            )
        except Exception as error:
            log.say(f"digest retain failed after {time.perf_counter() - began:.1f} s: {error!r}")
    finally:
        server.stop()
        Pg0(name="hindsight").stop()
    return answers, retain_s


def main() -> None:
    log = Log("prb-l-mem")
    isolate()
    rows, hashes = corpus(log)
    if "--corpus-only" in sys.argv:
        return
    peak = Peak()
    peak.thread.start()
    fts = Fts(rows)
    hindsight, retain_s = run_hindsight(log, rows, peak)
    peak.stop.set()
    peak.thread.join()
    scores: dict[str, dict[str, float]] = {"hindsight": {}, "fts5": {}}
    for kind in TYPES:
        asked = [q for q in QUESTIONS if q.kind == kind]
        for engine, hits_of in (("hindsight", hindsight.get), ("fts5", None)):
            counts = [
                relevant(hits_of(q.text) or [] if hits_of else fts.recall(q.text), q) for q in asked
            ]
            scores[engine][kind] = sum(counts) / len(counts) if counts else 0.0
        for q in asked:
            log.say(
                f"  [{kind}] {q.text!r}: hindsight {relevant(hindsight.get(q.text) or [], q)}/5, "
                f"fts5 {relevant(fts.recall(q.text), q)}/5"
            )
    changed = [str(p) for p, h in hashes.items() if sha256_file(p) != h and p == HIS_LIBRARY]
    result = judge(scores, peak.peak_private_mb, retain_s)
    result.notes.append(
        f"peak private bytes {peak.peak_private_mb:.0f} MB; peak RSS sum {peak.peak_rss_mb:.0f} MB "
        "(counts shared buffers once per Postgres backend)"
    )
    result.notes.append(f"his library.db unchanged: {not changed}")
    left = peak.leftovers()
    result.notes.append(f"processes left from the probe home: {left or 'none'}")
    log.verdict(result)


if __name__ == "__main__":
    main()
