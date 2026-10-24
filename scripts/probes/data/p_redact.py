"""P-REDACT: a token-shaped value written into a log line, a span attribute and a heartbeat field
never reaches the server's collector (DATA-PLAN DR10, W18; finding F43).

    cd qmx-agents
    uv run --no-sync python ../scripts/probes/data/p_redact.py

The collector in this run is a stub on loopback that records the OTLP bodies it receives: the
probe proves the exporter seam on the PC, which is what "fed after redaction" means, and not the
server's install (that is DR10's real step, gate G-LAND). The value is shaped like a provider key
and made at run time; it is never a real one and is never printed whole.

PASS when all three signals arrive, no received byte holds the value, and each record shows the
redaction mask. FAIL when any received body holds it. Scratch goes under `D:/Temp/prb-dp/p-redact`
and is removed at the end.
"""

from __future__ import annotations

import shutil
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar, Final

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qmx_engine import telemetry
from qmx_engine.heartbeat import Heartbeat, HeartbeatLog, kinds_digest
from qmx_engine.ledger.store import Ledger

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE: Final[str] = "P-REDACT"
RUN: Final[str] = "run-p-redact"
MASK: Final[str] = "[redacted]"
SIGNALS: Final = ("/v1/logs", "/v1/traces", "/v1/metrics")


class Collector(BaseHTTPRequestHandler):
    """A collector that keeps every body it receives and answers 200."""

    received: ClassVar[list[tuple[str, bytes]]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        type(self).received.append((self.path, body))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args: object) -> None:
        """A probe's log is its own; the HTTP server's per-request line is noise."""


@contextmanager
def collector() -> Iterator[str]:
    """One stub collector on a free loopback port, stopped when the `with` ends."""
    Collector.received = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Collector)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(10)


def token_shaped() -> str:
    """A provider-key shape, made at run time: the value every record carries."""
    return "sk-or-v1-" + "a" * 32


def write_records(home: Path, secret: str, at: str) -> None:
    """The three write points, each given a record whose text holds the value."""
    key = {"node_id": "step", "iteration": 0, "partition": None, "attempt": 1}
    with Ledger.open(home) as ledger:
        ledger.append(RUN, "run_created", {"mode": "test", "note": f"saw {secret}"}, at=at)
        ledger.append(RUN, "node_started", key, at=at)
        ledger.append(
            RUN,
            "tool_called",
            {**key, "tool": {"id": "t-1", "name": f"read {secret}", "duration_ms": 4}},
            at=at,
        )
        ledger.append(RUN, "node_finished", {**key, "status": "ok"}, at=at)
    HeartbeatLog(home, 7).write(
        [
            Heartbeat(
                subject="host",
                id=f"pc {secret}",
                at=at,
                cpu_seconds=1.0,
                rss_bytes=1024,
                machine_minutes=1.0,
                qmx_version="0.1.0",
                node_kinds=("script",),
                kinds_digest=kinds_digest(("script",)),
                paused=False,
            )
        ]
    )


def main() -> int:
    report = Report(PROBE)
    scratch = common.scratch_folder("p-redact")
    home = scratch / "home"
    home.mkdir(parents=True, exist_ok=True)
    secret = token_shaped()
    try:
        with collector() as endpoint:
            telemetry.reset()
            exporter = telemetry.configure(endpoint, state=home / telemetry.STATE_FILE)
            write_records(home, secret, "2026-10-23T09:00:00+00:00")
            exporter.flush()
        bodies = Collector.received
        paths = sorted({path for path, _ in bodies})
        joined = b"".join(body for _, body in bodies)
        report.numbers.update(
            endpoint_kind="stub on loopback",
            signals=len(bodies),
            paths=", ".join(paths),
            bytes=len(joined),
            masked=joined.count(MASK.encode()),
            dropped=exporter.counters.dropped,
            failed=exporter.counters.failed,
        )
        missing = [signal for signal in SIGNALS if signal not in paths]
        if missing:
            report.fail(f"these signals never arrived: {', '.join(missing)}")
        if secret.encode() in joined:
            report.fail("the token-shaped value reached the collector")
        if joined.count(MASK.encode()) < 3:
            report.fail("a record arrived without the redaction mask")
        if b"qmx.data" not in joined:
            report.fail("the log record's data did not arrive")
        if b"qmx.id" not in joined:
            report.fail("the heartbeat field did not arrive as a gauge label")
        if b"read " not in joined:
            report.fail("the tool span's name did not arrive")
        report.note(
            "the log line, the tool span's name and the heartbeat id each held the value and "
            f"each arrived as {MASK}; the collector never saw it"
        )
    except Exception as error:
        report.fail(f"{type(error).__name__}: {error}")
    finally:
        telemetry.reset()
        shutil.rmtree(scratch, ignore_errors=True)
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
