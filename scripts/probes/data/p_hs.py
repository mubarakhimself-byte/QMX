"""P-HS: Hindsight 1.1 on the server's system PostgreSQL 16 with pgvector.

The probe answers what the P-HS row needs, on the server's own CPU and RAM:

* resident memory at idle, once the service is up and before any row is retained;
* resident memory through a retain burst at the package's default worker slots, with no worker
  count set in the environment;
* whether the host, the collector and one measured agent session still fit the live free RAM
  beside it (the probe's own bound, named at `RESERVED_MB`);
* recall on the fixed query set, and parity with another run's answers when one is named.

The service is the artifact DR2E will run: the `hindsight-api` console script from the probe's own
venv, started in its own session, so peak memory is read across the whole service group and its
exit is the probe's to see. PostgreSQL is the Ubuntu package's `initdb` and `pg_ctl` over a data
folder under the probe root, on a loopback port picked at run time, so it runs as `qmx` and not
root. Its backends are a separate group, so their high-water mark is summed separately and the row
reports the admission figure as the two together.

Neither side holds a key: the service starts with `HINDSIGHT_API_LLM_PROVIDER=none`, the bank
retains in `chunks` mode with observations off, and the embedding and rerank models are the
package's local ones. Nothing leaves the box.

Run it on the server as `qmx` from `/srv/qmx/check/prb-ds/checkout`:

    /srv/qmx/check/prb-ds/venv-hs/bin/python scripts/probes/data/p_hs.py \
        --rows /srv/qmx/check/prb-ds/rows.jsonl \
        --questions scripts/probes/library/questions.json

Parity is a second run of the same script that wrote its answers out with `--emit-recall`, named
here with `--pc-recall`. Without that file the memory legs are still measured and the parity leg is
printed as `not run` with the reason, never guessed.

A recall against this box took 25 s on an idle 6-core server and 80 s while another probe held two
cores, so `--recall-limit N` asks only the first N questions of the set. The row records how many
ran, and a run that asked fewer says so.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Final

import server_common as common

PROBE: Final[str] = "P-HS"
HINDSIGHT_PIN: Final[str] = "1.1.0"
PG_BIN: Final[Path] = Path("/usr/lib/postgresql/16/bin")
"""The Ubuntu package's binaries. DR2E reuses the package; this data folder is removed."""
PGDATA: Final[Path] = common.PROBE_ROOT / "pgdata"
DATABASE: Final[str] = "hindsight"
BANK: Final[str] = "prb-ds-hs"
RESERVED_MB: Final[int] = 2_560
"""The probe's own admission bound, not a QMX cap: AD-30's 1,536 MB session (a measured agent
session) plus 1,024 MB for the host and the collector. The row records it as the derived figure."""
TOP: Final[int] = 5
CHUNK_CHARS: Final[int] = 1_200
"""The corpus chunk the ranking is produced on, so two runs rank the same rows."""
BATCH: Final[int] = 200


def build_rows(root: Path) -> list[dict[str, str]]:
    """One row per paragraph of every markdown file under `root`, the corpus both runs share."""
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


def service_env(pg_port: int, api_port: int) -> dict[str, str]:
    """The service's environment: loopback only, no model provider, models cached in the root."""
    catch = common.PROBE_ROOT / "home" / ".cache" / "huggingface"
    catch.mkdir(parents=True, exist_ok=True)
    return common.child_env(
        HINDSIGHT_API_DATABASE_URL=f"postgresql://qmx@127.0.0.1:{pg_port}/{DATABASE}",
        HINDSIGHT_API_DATABASE_BACKEND="postgresql",
        HINDSIGHT_API_LLM_PROVIDER="none",
        HINDSIGHT_API_HOST="127.0.0.1",
        HINDSIGHT_API_PORT=str(api_port),
        HINDSIGHT_API_LOG_LEVEL="WARNING",
        HF_HOME=str(catch),
    )


def psql(port: int, statement: str, database: str = "postgres") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(PG_BIN / "psql"),
            "-h",
            "127.0.0.1",
            "-p",
            str(port),
            "-U",
            "qmx",
            "-d",
            database,
            "-tAc",
            statement,
        ],
        capture_output=True,
        text=True,
        env=common.child_env(),
    )


def start_cluster(log: common.Log) -> int:
    """Initialize the cluster once and start it on a loopback port nobody holds."""
    if not (PGDATA / "PG_VERSION").exists():
        PGDATA.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                str(PG_BIN / "initdb"),
                "-D",
                str(PGDATA),
                "-A",
                "trust",
                "-U",
                "qmx",
                "--encoding=UTF8",
            ],
            capture_output=True,
            text=True,
            env=common.child_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(f"initdb failed: {result.stderr[-500:]}")
        log.say(f"initdb: {PGDATA}")
    port = common.free_port()
    sockets = common.PROBE_ROOT / "run"
    sockets.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(PG_BIN / "pg_ctl"),
            "-D",
            str(PGDATA),
            "-l",
            str(common.PROBE_ROOT / "logs" / "prb-ds-hs-pg.log"),
            "-o",
            f"-p {port} -c listen_addresses=127.0.0.1 -k {sockets}",
            "-w",
            "start",
        ],
        capture_output=True,
        text=True,
        env=common.child_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_ctl start failed: {result.stderr[-500:]}")
    return port


def prepare_database(port: int, log: common.Log) -> str:
    """The database and its vector extension, and the extension's own version for the row."""
    existing = psql(port, "SELECT 1 FROM pg_database WHERE datname = 'hindsight'")
    if existing.stdout.strip() != "1":
        created = subprocess.run(
            [str(PG_BIN / "createdb"), "-h", "127.0.0.1", "-p", str(port), "-U", "qmx", DATABASE],
            capture_output=True,
            text=True,
            env=common.child_env(),
        )
        if created.returncode != 0:
            raise RuntimeError(f"createdb failed: {created.stderr[-500:]}")
    vector = psql(port, "CREATE EXTENSION IF NOT EXISTS vector", DATABASE)
    if vector.returncode != 0:
        raise RuntimeError(f"pgvector missing: {vector.stderr[-500:]}")
    version = psql(port, "SELECT extversion FROM pg_extension WHERE extname = 'vector'", DATABASE)
    log.say(f"pgvector: {version.stdout.strip()}")
    return version.stdout.strip()


def stop_cluster(log: common.Log) -> None:
    """No probe cluster outlives its run."""
    if not (PGDATA / "PG_VERSION").exists():
        return
    result = subprocess.run(
        [str(PG_BIN / "pg_ctl"), "-D", str(PGDATA), "-m", "fast", "-w", "stop"],
        capture_output=True,
        text=True,
        env=common.child_env(),
    )
    log.say(f"cluster stopped: exit {result.returncode}")


def start_service(log: common.Log, pg_port: int) -> tuple[subprocess.Popen[bytes], int]:
    """The service in its own session, so its memory and its exit are both the probe's to read."""
    api_port = common.free_port()
    log_path = common.PROBE_ROOT / "logs" / "prb-ds-hs-service.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        [str(common.PROBE_ROOT / "venv-hs" / "bin" / "hindsight-api")],
        stdout=log_path.open("ab"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=service_env(pg_port, api_port),
    )
    log.say(f"service: pid {process.pid} on {api_port}")
    return process, api_port


def http_json(
    method: str, url: str, body: object | None = None, timeout_s: float = 600.0
) -> dict[str, object]:
    """One JSON call. A non-2xx answer is an error with the code and the service's own words."""
    payload = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(  # noqa: S310
        url,
        data=payload,
        headers={"Content-Type": "application/json"} if payload else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"{method} {url} answered {error.code}: {error.read()[:300]!r}"
        ) from error


def wait_healthy(base: str, timeout_s: float) -> bool:
    """Whether the service answered a healthy `/health` before the timeout."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            answer = http_json("GET", f"{base}/health", timeout_s=5)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError):
            time.sleep(1.0)
            continue
        if answer.get("status") == "healthy":
            return True
        time.sleep(1.0)
    return False


def postgres_peak_mb() -> int:
    """The cluster's own high-water mark: its backends are a different session group."""
    total = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if str(PGDATA).encode() not in cmdline:
            continue
        memory = common.read_status(int(entry.name))
        if memory is not None:
            total += memory.peak_mb
    return total


def create_bank(base: str, log: common.Log) -> None:
    """A bank that retains in `chunks` mode with observations off, rebuilt from scratch."""
    url = f"{base}/v1/default/banks/{BANK}"
    try:
        http_json("DELETE", url)
        log.say(f"bank {BANK}: deleted a previous run's")
    except RuntimeError as error:
        log.say(f"bank {BANK}: nothing to delete ({error})")
    http_json(
        "PUT",
        url,
        {"retain_extraction_mode": "chunks", "enable_observations": False},
    )
    log.say(f"bank {BANK}: chunks mode, observations off")


def retain(base: str, rows: list[dict[str, str]], log: common.Log) -> float:
    """The burst: every row, in batches, waiting for each to be processed."""
    began = time.perf_counter()
    for start in range(0, len(rows), BATCH):
        chunk = rows[start : start + BATCH]
        http_json(
            "POST",
            f"{base}/v1/default/banks/{BANK}/memories",
            {
                "items": [
                    {"content": row["text"], "document_id": row["id"], "tags": ["prb-ds"]}
                    for row in chunk
                ]
            },
        )
        log.say(f"retained {min(start + BATCH, len(rows))} of {len(rows)}")
    return round(time.perf_counter() - began, 1)


def recall(base: str, asked: list[str]) -> tuple[dict[str, list[str]], float]:
    """Each question's top document ids, in rank order, and the seconds the set took."""
    began = time.perf_counter()
    answers: dict[str, list[str]] = {}
    for question in asked:
        answer = http_json(
            "POST",
            f"{base}/v1/default/banks/{BANK}/memories/recall",
            {"query": question, "budget": "mid", "max_tokens": 4096},
        )
        results = answer.get("results") or []
        answers[question] = [str(hit.get("document_id") or "") for hit in results[:TOP]]
    return answers, round(time.perf_counter() - began, 1)


def judge(summary: dict[str, object], pc_recall: Path | None) -> common.Report:
    """The P-HS verdict from the run: started, killed, memory, fit, parity."""
    report = common.Report(PROBE)
    for key, value in summary.items():
        if key in {"recall", "errors"}:
            continue
        report.numbers[key] = value
    errors = summary.get("errors") or []
    if errors:
        report.fail(f"the service did not start: {errors[0]}")
        return report
    if not summary.get("started"):
        report.fail("the service does not start")
        return report
    free_after = int(summary.get("free_after_mb") or 0)
    if free_after < RESERVED_MB:
        report.fail(
            f"the host, the collector and one agent session do not fit: {free_after} MB free, "
            f"{RESERVED_MB} MB reserved"
        )
    report.note(
        f"{summary.get('service_peak_mb')} MB service peak and "
        f"{summary.get('postgres_peak_mb')} MB PostgreSQL at {summary.get('retained')} rows, "
        f"{free_after} MB free after, against PRB-S's 2,687 MB"
    )
    mine = summary.get("recall") or {}
    if pc_recall is None:
        report.numbers["parity"] = "not run: no --pc-recall file, so no second run to compare"
        report.note(
            "parity: not measured. The only way to compare is a second run of this script with "
            "--emit-recall, and no such run exists on the PC"
        )
        return report
    other = json.loads(pc_recall.read_text(encoding="utf-8"))
    differs = [question for question, hits in other.items() if mine.get(question) != hits]
    report.numbers["parity_questions"] = len(other)
    report.numbers["parity_differ"] = len(differs)
    report.numbers["parity"] = "identical" if not differs else f"differs on {len(differs)}"
    if differs:
        report.fail(f"recall differs on {len(differs)} of {len(other)} questions: {differs[:3]}")
    else:
        report.note(f"recall parity: {len(other)} questions, top {TOP} identical")
    return report


def run(args: argparse.Namespace, log: common.Log) -> tuple[common.Report, dict[str, object]]:
    summary: dict[str, object] = {"started": False, "errors": []}
    process: subprocess.Popen[bytes] | None = None
    sampler: common.PeakSampler | None = None
    try:
        pg_port = start_cluster(log)
        summary["pg_vector"] = prepare_database(pg_port, log)
        began = time.perf_counter()
        process, api_port = start_service(log, pg_port)
        sampler = common.PeakSampler(process.pid, 1.0)
        sampler.start()
        base = f"http://127.0.0.1:{api_port}"
        if not wait_healthy(base, args.start_timeout):
            raise RuntimeError(f"the service does not answer /health within {args.start_timeout} s")
        summary["start_seconds"] = round(time.perf_counter() - began, 1)
        summary["started"] = True
        summary["hindsight_version"] = http_json("GET", f"{base}/v1/version").get(
            "version", HINDSIGHT_PIN
        )
        summary["worker_slots"] = {
            key: value
            for key, value in os.environ.items()
            if key.startswith("HINDSIGHT_API_") and key.endswith(("WORKERS", "SLOTS"))
        } or "default (QMX sets none)"
        log.say(f"hindsight {summary['hindsight_version']} up in {summary['start_seconds']} s")
        create_bank(base, log)
        summary["idle_peak_mb"] = common.group_peak_mb(process.pid)
        summary["idle_free_mb"] = common.free_mb()
        log.say(f"idle: {summary['idle_peak_mb']} MB, {summary['idle_free_mb']} MB free")
        rows = args.rows_loaded[: args.burst]
        summary["retain_seconds"] = retain(base, rows, log)
        summary["retained"] = len(rows)
        summary["service_peak_mb"] = common.group_peak_mb(process.pid)
        summary["postgres_peak_mb"] = postgres_peak_mb()
        summary["free_after_mb"] = common.free_mb()
        log.say(
            f"burst: {len(rows)} rows in {summary['retain_seconds']} s, "
            f"{summary['service_peak_mb']} MB service, "
            f"{summary['postgres_peak_mb']} MB PostgreSQL, "
            f"{summary['free_after_mb']} MB free"
        )
        began = time.perf_counter()
        asked = args.questions_loaded[: args.recall_limit or len(args.questions_loaded)]
        answers, elapsed = recall(base, asked)
        summary["recall"] = answers
        summary["recall_questions"] = len(asked)
        summary["recall_seconds"] = elapsed
        log.say(f"recall: {len(asked)} questions in {elapsed} s")
        summary["run_peak_mb"] = sampler.peak_mb
    except Exception as error:
        summary["errors"].append(f"{type(error).__name__}: {error}")
        log.say(f"error: {summary['errors'][-1]}")
    finally:
        if sampler is not None:
            sampler.stop()
        if process is not None and process.poll() is None:
            common.signal_pgroup(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                common.signal_pgroup(process.pid, signal.SIGKILL)
            log.say(f"service stopped, exit {process.returncode}")
        stop_cluster(log)
    return judge(summary, args.pc_recall), summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=common.PROBE_ROOT / "rows.jsonl")
    parser.add_argument("--corpus-root", type=Path, default=None)
    parser.add_argument(
        "--questions", type=Path, default=Path("scripts/probes/library/questions.json")
    )
    parser.add_argument("--burst", type=int, default=500)
    parser.add_argument(
        "--recall-limit",
        type=int,
        default=0,
        help="Ask only the first N questions of the set; 0 asks all of them.",
    )
    parser.add_argument("--start-timeout", type=float, default=600.0)
    parser.add_argument("--pc-recall", type=Path, default=None)
    parser.add_argument("--emit-recall", type=Path, default=None)
    args = parser.parse_args(argv)

    log = common.Log("prb-ds-hs")
    try:
        if args.corpus_root is not None:
            rows = build_rows(args.corpus_root)
            args.rows.parent.mkdir(parents=True, exist_ok=True)
            args.rows.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            log.say(f"corpus: {len(rows)} rows from {args.corpus_root} into {args.rows}")
        if not args.rows.exists():
            log.say(f"no corpus at {args.rows}: build one with --corpus-root")
            log.say(f"{PROBE} {common.NOT_RUN}")
            return 1
        args.rows_loaded = load_rows(args.rows)
        args.questions_loaded = questions(args.questions)
        log.say(f"rows: {len(args.rows_loaded)}, questions: {len(args.questions_loaded)}")
        return report_and_emit(args, log)
    finally:
        log.close()


def report_and_emit(args: argparse.Namespace, log: common.Log) -> int:
    report, summary = run(args, log)
    if args.emit_recall is not None:
        args.emit_recall.write_text(
            json.dumps(summary.get("recall") or {}, indent=2), encoding="utf-8"
        )
        log.say(f"recall written to {args.emit_recall}")
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
