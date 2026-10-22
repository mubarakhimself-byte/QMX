"""P-HS: Hindsight 1.1 on the server's system PostgreSQL 16 with pgvector.

The probe answers the three things the P-HS row needs, on the server's own CPU and RAM:

* resident memory at idle, once the service is up and before any row is retained;
* resident memory through a retain burst at the package's default worker slots, with no worker
  count set in the environment;
* whether the host, the collector and one measured agent session still fit the live free RAM
  beside it (the probe's own bound, named at `RESERVED_MB`);
* recall parity on the fixed query set, against the PC's answers for the same corpus.

The work runs in a child process in its own session, so the memory figure covers Hindsight, its
embedders and the PostgreSQL backends the burst opens, and nothing of the shell's. The parent
samples that group every second and reads the child's own summary when it ends.

Neither side holds a key: Hindsight starts with `llm_provider=none`, retention is `chunks` mode
with observations off, and the embedding and rerank models are the local ones.

Run it on the server as `qmx` from `/srv/qmx/check/prb-ds/checkout`:

    /srv/qmx/check/prb-ds/venv-hs/bin/python scripts/probes/data/p_hs.py \
        --rows /srv/qmx/check/prb-ds/rows.jsonl

Parity is a second run of the same script on the PC, which writes its answers out:

    uv run python scripts/probes/data/p_hs.py --rows <the same rows> --emit-recall pc-recall.json

and then the server run names them with `--pc-recall`. Without that file the memory legs are
still measured and the parity leg is printed as `not run` with the reason, never guessed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import server_common as common

PROBE: Final[str] = "P-HS"
HINDSIGHT_PIN: Final[str] = "1.1.0"
PG_BIN: Final[Path] = Path("/usr/lib/postgresql/16/bin")
"""The Ubuntu package's binaries. DR2E reuses the package; this data folder is removed."""
PGDATA: Final[Path] = common.PROBE_ROOT / "pgdata"
"""The cluster's data folder, under the probe root, so the service runs as `qmx` and not root."""
DATABASE: Final[str] = "hindsight"
SUMMARY: Final[Path] = common.PROBE_ROOT / "logs" / "p_hs-work.json"
RESERVED_MB: Final[int] = 2_560
"""The probe's own admission bound, not a QMX cap: AD-30's 1,536 MB session (a measured agent
session) plus 1,024 MB for the host and the collector. The row records it as the derived figure."""
TOP: Final[int] = 5
BANK: Final[str] = "prb-ds-hs"
CHUNK_CHARS: Final[int] = 1_200
"""The corpus chunk the PC's ranking is produced on, so both sides rank the same rows."""


def build_rows(root: Path) -> list[dict[str, str]]:
    """One row per paragraph of every markdown file under `root`, the corpus both sides share."""
    rows: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in {".git", "archive"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, paragraph in enumerate(text.split("\n\n")):
            body = " ".join(paragraph.split())
            if len(body) < 40:
                continue
            rows.append({"id": f"{path.stem}-{number}", "text": body[:CHUNK_CHARS]})
    return rows


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def questions(path: Path) -> list[str]:
    """The fixed query set, as text, in file order."""
    document = json.loads(path.read_text(encoding="utf-8"))
    return [entry["question"] for entry in document["questions"]]


def postgres_dsn(port: int, socket_dir: Path) -> str:
    """A unix-socket DSN: the cluster listens on no TCP port, so nothing on the box can reach it."""
    return f"postgresql://qmx@/{DATABASE}?host={socket_dir}&port={port}"


def start_cluster(log: common.Log, port: int, socket_dir: Path) -> None:
    """Initialize the cluster once and start it. Idempotent: a second run reuses the data folder."""
    initdb = PG_BIN / "initdb"
    if not (PGDATA / "PG_VERSION").exists():
        PGDATA.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [str(initdb), "-D", str(PGDATA), "-A", "trust", "-U", "qmx", "--encoding=UTF8"],
            capture_output=True,
            text=True,
            env=common.child_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(f"initdb failed: {result.stderr[-500:]}")
        log.say(f"initdb: {PGDATA}")
    socket_dir.mkdir(parents=True, exist_ok=True)
    options = f"-p {port} -k {socket_dir} -c listen_addresses=''"
    result = subprocess.run(
        [
            str(PG_BIN / "pg_ctl"),
            "-D",
            str(PGDATA),
            "-l",
            str(common.PROBE_ROOT / "logs" / "p_hs-pg.log"),
            "-o",
            options,
            "-w",
            "start",
        ],
        capture_output=True,
        text=True,
        env=common.child_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_ctl start failed: {result.stderr[-500:]}")


def psql(port: int, socket_dir: Path, statement: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(PG_BIN / "psql"),
            "-h",
            str(socket_dir),
            "-p",
            str(port),
            "-U",
            "qmx",
            "-d",
            "postgres",
            "-tAc",
            statement,
        ],
        capture_output=True,
        text=True,
        env=common.child_env(),
    )


def prepare_database(log: common.Log, port: int, socket_dir: Path) -> None:
    existing = psql(port, socket_dir, "SELECT 1 FROM pg_database WHERE datname = 'hindsight'")
    if existing.stdout.strip() != "1":
        created = subprocess.run(
            [
                str(PG_BIN / "createdb"),
                "-h",
                str(socket_dir),
                "-p",
                str(port),
                "-U",
                "qmx",
                DATABASE,
            ],
            capture_output=True,
            text=True,
            env=common.child_env(),
        )
        if created.returncode != 0:
            raise RuntimeError(f"createdb failed: {created.stderr[-500:]}")
        log.say(f"createdb: {DATABASE}")
    vector = psql(port, socket_dir, "CREATE EXTENSION IF NOT EXISTS vector")
    if vector.returncode != 0:
        raise RuntimeError(f"pgvector missing: {vector.stderr[-500:]}")
    log.say("pgvector: present")


def work(args: argparse.Namespace, log: common.Log) -> int:
    """The measured half: Hindsight over the system cluster, one burst, one recall, one summary."""
    summary: dict[str, object] = {"started": False, "errors": []}
    port = common.free_port()
    socket_dir = common.PROBE_ROOT / "run"
    try:
        start_cluster(log, port, socket_dir)
        prepare_database(log, port, socket_dir)
        import hindsight  # noqa: PLC0415 - the probe's venv imports it, not the checkout
        from hindsight import HindsightClient, HindsightServer  # noqa: PLC0415

        summary["hindsight_version"] = getattr(hindsight, "__version__", HINDSIGHT_PIN)
        summary["worker_slots"] = {
            key: value
            for key, value in os.environ.items()
            if key.startswith("HINDSIGHT_API_") and key.endswith(("WORKERS", "SLOTS"))
        } or "default (QMX sets none)"
        server = HindsightServer(db_url=postgres_dsn(port, socket_dir), llm_provider="none")
        began = time.perf_counter()
        server.start(timeout=args.start_timeout)
        summary["start_seconds"] = round(time.perf_counter() - began, 1)
        summary["started"] = True
        log.say(
            f"hindsight {summary['hindsight_version']} up in "
            f"{summary['start_seconds']} s on {server.url}"
        )
        try:
            client = HindsightClient(base_url=server.url, timeout=600)
            client.create_bank(
                bank_id=BANK, retain_extraction_mode="chunks", enable_observations=False
            )
            summary["idle_peak_mb"] = common.group_peak_mb(os.getpgrp())
            summary["idle_free_mb"] = common.free_mb()
            log.say(
                f"idle: {summary['idle_peak_mb']} MB resident, {summary['idle_free_mb']} MB free"
            )
            rows = args.rows_loaded[: args.burst]
            began = time.perf_counter()
            for start in range(0, len(rows), 200):
                client.retain_batch(
                    bank_id=BANK,
                    items=[
                        {"content": row["text"], "document_id": row["id"], "tags": ["prb-ds"]}
                        for row in rows[start : start + 200]
                    ],
                )
            summary["retain_seconds"] = round(time.perf_counter() - began, 1)
            summary["retained"] = len(rows)
            summary["burst_peak_mb"] = common.group_peak_mb(os.getpgrp())
            summary["free_after_mb"] = common.free_mb()
            log.say(
                f"burst: {len(rows)} rows in {summary['retain_seconds']} s, "
                f"{summary['burst_peak_mb']} MB resident, {summary['free_after_mb']} MB free"
            )
            answers: dict[str, list[str]] = {}
            for question in args.questions_loaded:
                found = client.recall(bank_id=BANK, query=question, budget="mid", max_tokens=4096)
                answers[question] = [
                    getattr(hit, "document_id", "") or "" for hit in found.results[:TOP]
                ]
            summary["recall"] = answers
            summary["recall_seconds"] = round(time.perf_counter() - began, 1)
        finally:
            server.stop()
    except Exception as error:
        summary["errors"].append(f"{type(error).__name__}: {error}")
        log.say(f"error: {summary['errors'][-1]}")
    finally:
        stop_cluster(log, port, socket_dir)
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        log.say(f"summary: {SUMMARY}")
    return 0 if summary.get("started") and not summary["errors"] else 1


def stop_cluster(log: common.Log, port: int, socket_dir: Path) -> None:
    """Stop the cluster unless the run was asked to leave it up, and say which happened."""
    if os.environ.get("PRB_DS_KEEP_POSTGRES") == "1":
        log.say("cluster left running on request")
        return
    if not (PGDATA / "PG_VERSION").exists():
        return
    result = subprocess.run(
        [str(PG_BIN / "pg_ctl"), "-D", str(PGDATA), "-m", "fast", "-w", "stop"],
        capture_output=True,
        text=True,
        env=common.child_env(),
    )
    log.say(f"cluster stopped: exit {result.returncode}")


def judge(
    summary: dict[str, object], pc_recall: Path | None, run: common.ChildRun
) -> common.Report:
    """The P-HS verdict from the child's summary: started, killed, memory, fit, parity."""
    report = common.Report(PROBE)
    report.numbers.update(
        {
            "hindsight_version": summary.get("hindsight_version", HINDSIGHT_PIN),
            "worker_slots": summary.get("worker_slots", "default (QMX sets none)"),
            "start_seconds": summary.get("start_seconds"),
            "idle_peak_mb": summary.get("idle_peak_mb"),
            "burst_peak_mb": summary.get("burst_peak_mb"),
            "run_peak_mb": run.peak_mb,
            "retained": summary.get("retained"),
            "retain_seconds": summary.get("retain_seconds"),
            "free_after_mb": summary.get("free_after_mb"),
            "reserved_mb": RESERVED_MB,
            "error": "; ".join(summary.get("errors") or []) or None,
        }
    )
    if summary.get("errors"):
        report.fail(f"the service did not start: {summary['errors'][0]}")
        return report
    if not summary.get("started"):
        report.fail("the service does not start")
        return report
    if run.returncode < 0:
        report.fail(f"the process was killed (signal {-run.returncode})")
        return report
    free_after = int(summary.get("free_after_mb") or 0)
    if free_after < RESERVED_MB:
        report.fail(
            f"the host, the collector and one agent session do not fit: {free_after} MB free, "
            f"{RESERVED_MB} MB reserved"
        )
    report.note(
        f"peak resident {run.peak_mb} MB over {run.samples} samples, against PRB-S's 2,687 MB"
    )
    if pc_recall is None:
        report.not_run("recall parity not measured: no --pc-recall file on this host")
        return report
    answer = json.loads(pc_recall.read_text(encoding="utf-8"))
    mine = summary.get("recall") or {}
    differs = [question for question, hits in answer.items() if mine.get(question) != hits]
    report.numbers["parity_questions"] = len(answer)
    report.numbers["parity_differ"] = len(differs)
    if differs:
        report.fail(f"recall differs on {len(differs)} of {len(answer)} questions: {differs[:3]}")
    else:
        report.note(f"recall parity: {len(answer)} questions, top {TOP} identical to the PC's")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=common.PROBE_ROOT / "rows.jsonl")
    parser.add_argument("--corpus-root", type=Path, default=None)
    parser.add_argument(
        "--questions", type=Path, default=Path("scripts/probes/library/questions.json")
    )
    parser.add_argument("--burst", type=int, default=500)
    parser.add_argument("--start-timeout", type=float, default=300.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--pc-recall", type=Path, default=None)
    parser.add_argument("--emit-recall", type=Path, default=None)
    parser.add_argument("--work", action="store_true")
    args = parser.parse_args(argv)

    log = common.Log("prb-ds-hs")
    try:
        if args.corpus_root is not None:
            rows = build_rows(args.corpus_root)
            args.rows.parent.mkdir(parents=True, exist_ok=True)
            args.rows.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            log.say(f"corpus: {len(rows)} rows from {args.corpus_root} into {args.rows}")
        if not args.rows.exists():
            log.say(
                f"no corpus at {args.rows}: build one with --corpus-root, "
                "or copy the PC's rows over"
            )
            log.say(f"{PROBE} {common.NOT_RUN}")
            return 1
        args.rows_loaded = load_rows(args.rows)
        args.questions_loaded = questions(args.questions)
        log.say(f"rows: {len(args.rows_loaded)}, questions: {len(args.questions_loaded)}")
        if args.work:
            return work(args, log)

        child = common.run_child(
            "prb-ds-hs",
            [
                sys.executable,
                str(Path(__file__)),
                "--work",
                "--rows",
                str(args.rows),
                "--questions",
                str(args.questions),
                "--burst",
                str(args.burst),
                "--start-timeout",
                str(args.start_timeout),
            ],
            timeout_s=args.timeout,
            interval_s=1.0,
        )
        summary = (
            json.loads(common.SUMMARY.read_text(encoding="utf-8"))
            if common.SUMMARY.exists()
            else {}
        )
        report = judge(summary, args.pc_recall, child)
        if args.emit_recall is not None and summary.get("recall"):
            args.emit_recall.write_text(json.dumps(summary["recall"], indent=2), encoding="utf-8")
            log.say(f"recall written to {args.emit_recall}")
        log.say(f"child: exit {child.returncode} in {child.seconds} s, log {child.log}")
        return report.render()
    finally:
        log.close()


if __name__ == "__main__":
    raise SystemExit(main())
