"""P-MEM, Contabo half (engine AD-18, ruling 119, SOLUTION-DESIGN 28.8, review 48 M11): embedded
Hindsight with its embedding model against PRB-L's rows on his server, plus the free-RAM pair and
the derived `overhead_mb`.

The rows are PRB-L's `homes/prb-l/p_mem_rows.jsonl` (3,591 paragraphs of his plan record and his
library items) copied unchanged to `homes/prb-s/p_mem_rows.jsonl`. The question set, the FTS5
adapter, the relevance oracle and the RAM line come from `scripts/probes/library/p_mem.py` by
path. What is the server's own is the memory measurement (its pg0 tree, its free RAM), the judge
(the PC's numbers are held, and RAM is the line this host decides) and the overhead arithmetic
from AD-30.

No key is read and no model turn runs. Hindsight starts with `llm_provider=none`, the rows are
retained in `chunks` mode with observations off, so extraction never runs, and recall is pure
retrieval. The embedding model is the local download `BAAI/bge-small-en-v1.5`.

    HOME=/srv/qmx/check/prb-s/homes/prb-s \\
        /srv/qmx/check/prb-s/homes/prb-s/venv/bin/python scripts/probes/server/p_mem.py [--ram]

`--ram` is the same workload recorded as lane 4, whose pass line is the free-RAM pair and the
derived `overhead_mb`. Lane 3's log is the P-MEM row.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Final

from common import PROBE_HOME, Log, free_mb, library, total_mb

MEM = library("p_mem")
Row = MEM.Row
Question = MEM.Question
Verdict = MEM.Verdict
QUESTIONS: Final = MEM.QUESTIONS
TYPES: Final = MEM.TYPES
TOP: Final = MEM.TOP
RSS_LIMIT_MB: Final = MEM.RSS_LIMIT_MB
FALLBACK_RAM: Final = MEM.FALLBACK_RAM
FALLBACK_QUALITY: Final = MEM.FALLBACK_QUALITY

ROWS: Final = PROBE_HOME / "p_mem_rows.jsonl"
LLM: Final = "none"
"""No provider, no key, no model turn: chunks retain with observations off never extracts, and
recall is pure retrieval."""
START_TIMEOUT_S: Final = 900.0
"""The first start downloads the embedder and the reranker and unpacks Postgres."""
PG0_MARK: Final = "/.pg0/instances/"
"""pg0 keeps its instance under the probe home on this host; the instance name is pg0's to
choose, so the tree is matched by the folder shape rather than the name."""
PC_QUALITY: Final[dict[str, float]] = {
    "already-built": 1.0,
    "dead-end": 1.4,
    "lab-to-hub": 2.2,
    "decided": 1.2,
}
"""PRB-L's Hindsight means in the top 5 per question type (`scripts/probes/library/FINDINGS.md`,
P-MEM row): the numbers the server must hold."""
PC_FTS5: Final[dict[str, float]] = {
    "already-built": 0.4,
    "dead-end": 0.8,
    "lab-to-hub": 2.4,
    "decided": 0.6,
}
"""FTS5's, from the same row. The server's FTS5 runs over the same rows with the same adapter, so
it is the check that the copied rows are the PC's."""
SESSION_MB: Final = 1536
"""AD-30's reservation per agent session (Claude's default)."""
RAM_BUDGET_MB: Final = 12_288
"""The plan's figure for this box: 12 GB (AD-30, ruling 76); `free -m` reads 11,960 MB."""
BASE_OVERHEAD_MB: Final = 6_144
"""Contabo's colocated services without Hindsight: the Hub, vault, market data, monitoring, the
server engine and its warm workers (AD-30, Claude's default)."""
OVERHEAD_GRID_MB: Final = 256


def load_rows() -> list[Row]:
    with ROWS.open(encoding="utf-8") as handle:
        return [Row(**json.loads(line)) for line in handle]


def mean_hits(questions: Sequence[Question], hits_of: Callable[[str], Sequence[str]]) -> float:
    """The mean count of relevant hits in the top 5: the library's score for one type."""
    counts = [MEM.relevant(hits_of(q.text), q) for q in questions]
    return sum(counts) / len(counts) if counts else 0.0


def judge(hindsight: Mapping[str, float], memory_mb: float, pc: Mapping[str, float]) -> Verdict:
    """PASS when Hindsight's peak resident memory is at most 2,048 MB and it holds the PC's
    per-type numbers. Quality is the PC's question (ruling 119 keeps the choice); the server's is
    memory, and a drop against the PC would mean the move lost something."""
    numbers: dict[str, float | int | str] = {
        f"hindsight_{kind}": round(hindsight[kind], 2) for kind in TYPES
    }
    numbers |= {f"pc_{kind}": pc[kind] for kind in TYPES}
    numbers["memory_mb"] = round(memory_mb)
    failed: list[tuple[str, str]] = []
    if memory_mb > RSS_LIMIT_MB:
        failed.append(("FAIL on RAM", FALLBACK_RAM))
    behind = [kind for kind in TYPES if hindsight[kind] < pc[kind] - 1e-9]
    if behind:
        failed.append(
            (
                f"FAIL on quality: Hindsight is behind the PC on {', '.join(behind)}",
                FALLBACK_QUALITY,
            )
        )
    if not failed:
        return Verdict(
            "P-MEM", "PASS", numbers, "it holds the PC's numbers within the 2,048 MB line"
        )
    reasons, fallbacks = zip(*failed, strict=True)
    return Verdict("P-MEM", "FAIL", numbers, "; ".join(reasons), " ".join(fallbacks))


def capacity(overhead_mb: int, budget_mb: int = RAM_BUDGET_MB, session_mb: int = SESSION_MB) -> int:
    """AD-30's derived session count: `floor((ram_budget_mb - overhead_mb) / session_mb)`."""
    return max(0, (budget_mb - overhead_mb) // session_mb)


def derive_overhead(
    footprint_mb: float, base_mb: int = BASE_OVERHEAD_MB, grid_mb: int = OVERHEAD_GRID_MB
) -> int:
    """The colocated budget plus Hindsight's measured footprint, rounded up to the grid. The
    result is reported with the sessions it reserves; it does not force a session count."""
    return math.ceil((base_mb + footprint_mb) / grid_mb) * grid_mb


def ram_verdict(without_mb: int, with_mb: int, peak_mb: float, overhead_mb: int) -> Verdict:
    """Lane 4's record: both free-RAM numbers and the derived overhead, with the sessions each
    overhead reserves. The 4 without Hindsight is AD-30's figure for this box."""
    footprint = round(max(peak_mb, without_mb - with_mb))
    numbers: dict[str, float | int | str] = {
        "free_without_hindsight_mb": without_mb,
        "free_with_hindsight_mb": with_mb,
        "hindsight_footprint_mb": footprint,
        "overhead_mb": overhead_mb,
        "sessions_with_hindsight": capacity(overhead_mb),
        "sessions_without_hindsight": capacity(BASE_OVERHEAD_MB),
    }
    if min(without_mb, with_mb, peak_mb, overhead_mb) > 0:
        return Verdict(
            "P-RAM",
            "PASS",
            numbers,
            f"{without_mb} MB free without Hindsight, {with_mb} MB with it; overhead {overhead_mb} "
            f"MB leaves {numbers['sessions_with_hindsight']} sessions with Hindsight and "
            f"{numbers['sessions_without_hindsight']} without",
        )
    return Verdict("P-RAM", "FAIL", numbers, "the free-RAM pair or the derived overhead is missing")


class Peak(MEM.Peak):
    """The library's sampler over this run's pg0 tree: this process, the postmaster whose data
    folder sits under `.pg0/instances`, and every backend under it."""

    def tree(self) -> list[Any]:
        own = self.psutil.Process()
        found = [own]
        for proc in self.psutil.process_iter(["cmdline"]):
            line = " ".join(proc.info.get("cmdline") or []).replace("\\", "/").lower()
            if PG0_MARK in line:
                found.append(proc)
                found.extend(proc.children(recursive=True))
        return found


def run_hindsight(log: Log, rows: Sequence[Row], peak: Peak) -> tuple[dict[str, list[str]], int]:
    from hindsight import HindsightClient, HindsightServer  # noqa: PLC0415
    from pg0 import Pg0  # noqa: PLC0415

    server = HindsightServer(db_url="pg0", llm_provider=LLM)
    answers: dict[str, list[str]] = {}
    server.start(timeout=START_TIMEOUT_S)
    try:
        client = HindsightClient(base_url=server.url, timeout=600)
        bank = f"prb-s-chunks-{int(time.time())}"
        client.create_bank(bank_id=bank, retain_extraction_mode="chunks", enable_observations=False)
        began = time.perf_counter()
        for start in range(0, len(rows), 200):
            client.retain_batch(
                bank_id=bank,
                items=[
                    {"content": r.text, "document_id": r.row_id, "tags": [r.session]}
                    for r in rows[start : start + 200]
                ],
            )
        log.say(f"hindsight chunks retain of {len(rows)} rows: {time.perf_counter() - began:.0f} s")
        for q in QUESTIONS:
            found = client.recall(bank_id=bank, query=q.text, budget="mid", max_tokens=4096)
            answers[q.text] = [r.text for r in found.results[:TOP]]
        free_with = free_mb()
        log.say(
            f"free RAM with Hindsight {free_with} MB; "
            f"resident {peak.current()[1]:.0f} MB after recall"
        )
        return answers, free_with
    finally:
        server.stop()
        try:
            Pg0(name="hindsight").stop()
        except Exception as error:
            log.say(f"pg0 stop: {error!r}")


def round_scores(scores: Mapping[str, float]) -> dict[str, float]:
    return {kind: round(value, 2) for kind, value in scores.items()}


def main() -> None:
    ram_only = "--ram" in sys.argv
    log = Log("prb-s-ram" if ram_only else "prb-s-mem")
    os.environ["HOME"] = str(PROBE_HOME)
    os.environ.setdefault("HF_HOME", str(PROBE_HOME / "hf"))
    os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_PROVIDER", "local")
    os.environ.setdefault("HINDSIGHT_API_RERANKER_PROVIDER", "local")
    os.environ.setdefault("HINDSIGHT_API_ENABLE_OBSERVATIONS", "false")
    log.say(
        "P-RAM, lane 4: free RAM with and without Hindsight, and the derived overhead_mb"
        if ram_only
        else "P-MEM, lane 3: Hindsight with its embedding model against PRB-L's rows"
    )
    rows = load_rows()
    log.say(f"rows: {len(rows)} from {ROWS}")
    free_without = free_mb()
    log.say(
        f"machine before Hindsight: {free_without} MB free of {total_mb()} MB, "
        f"load {os.getloadavg()}"
    )
    peak = Peak()
    peak.thread.start()
    hindsight, free_with = run_hindsight(log, rows, peak)
    peak.stop.set()
    peak.thread.join()
    free_after = free_mb()
    fts = MEM.Fts(rows)
    fts_scores = {
        kind: mean_hits([q for q in QUESTIONS if q.kind == kind], fts.recall) for kind in TYPES
    }
    hindsight_scores = {
        kind: mean_hits([q for q in QUESTIONS if q.kind == kind], lambda text: hindsight[text])
        for kind in TYPES
    }
    for q in QUESTIONS:
        log.say(
            f"  [{q.kind}] {q.text!r}: hindsight {MEM.relevant(hindsight.get(q.text) or [], q)}/5, "
            f"fts5 {MEM.relevant(fts.recall(q.text), q)}/5"
        )
    log.say(
        f"  FTS5 on the same rows: {round_scores(fts_scores)}; the PC's {PC_FTS5} "
        f"(equal means the copied rows are the PC's)"
    )
    footprint = max(peak.peak_resident_mb, free_without - free_with)
    overhead = derive_overhead(footprint)
    log.say(
        f"free RAM {free_without} MB without Hindsight, {free_with} MB with it "
        f"(delta {free_without - free_with} MB), {free_after} MB after it stopped"
    )
    log.say(
        f"peak resident {peak.peak_resident_mb:.0f} MB, peak RSS sum {peak.peak_rss_mb:.0f} MB, "
        f"footprint {footprint:.0f} MB"
    )
    log.say(
        f"overhead_mb {overhead}: {capacity(overhead)} sessions with Hindsight, "
        f"{capacity(BASE_OVERHEAD_MB)} without (session_mb {SESSION_MB}, "
        f"ram_budget_mb {RAM_BUDGET_MB})"
    )
    log.verdict(ram_verdict(free_without, free_with, peak.peak_resident_mb, overhead))
    result = judge(hindsight_scores, peak.peak_resident_mb, PC_QUALITY)
    result.notes.append(
        f"peak resident {peak.peak_resident_mb:.0f} MB over this process and pg0's Postgres; "
        f"peak RSS sum {peak.peak_rss_mb:.0f} MB (shared buffers once per backend)"
    )
    result.notes.append(
        f"free RAM {free_without} MB without Hindsight, {free_with} MB with it; "
        f"derived overhead_mb {overhead}"
    )
    result.notes.append(f"processes left from the probe home: {peak.leftovers() or 'none'}")
    log.verdict(result)


if __name__ == "__main__":
    main()
