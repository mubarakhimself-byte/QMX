"""P-BAN (W14; engine AD-68, rulings 122 and 128), acceptance: two Binance connections on one
server share one egress slowdown wait.

Two Binance connections (spot and futures) talk to a local stub on `127.0.0.1` that answers
`429` with `Retry-After`, then `418` to any request inside the wait. Both connections must wait
until the shared `slowed_until` for that egress address, and the stub must record no request
inside the wait. The wait is three seconds: a probe bound, not a provider limit.

    uv run --no-sync python -m scripts.probes.data.p_ban

FAIL when any request lands inside the wait, or a connection's reading is not `slowed`.

Scratch is `D:/Temp/prb-dp/ban` and is removed before the probe exits. The stub binds an
ephemeral port on `127.0.0.1` and serves only that one address, so nothing leaves the machine.
"""

from __future__ import annotations

import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qmx_broker.models import Broker, Connection
from qmx_broker.registry import (
    ProbeResult,
    Reading,
    SlowDown,
    Slowdowns,
    describe,
    walk,
)

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE = "P-BAN"
EGRESS = "203.0.113.9"
WAIT_SECONDS = 3.0
RETRY_AFTER = 2
SPOT = "binance-spot"
FUTURES = "binance-futures"


class Stub:
    """A local Binance stand-in: one 429 with Retry-After, then 418 inside the wait."""

    def __init__(self) -> None:
        self.wait_until = 0.0
        self.served = 0
        self.inside_wait: list[float] = []
        self._lock = threading.Lock()
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 (the stdlib's name)
                with stub._lock:
                    now = time.time()
                    if now < stub.wait_until:
                        stub.inside_wait.append(now)
                        code, headers = 418, {}
                    elif stub.served == 0:
                        stub.served = 1
                        stub.wait_until = now + WAIT_SECONDS
                        code, headers = 429, {"Retry-After": str(RETRY_AFTER)}
                    else:
                        stub.served += 1
                        code, headers = 200, {}
                self.send_response(code)
                for name, value in headers.items():
                    self.send_header(name, value)
                body = b"{}"
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> Stub:
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.server.shutdown()
        self.server.server_close()


def probe_with(stub: Stub):
    """The health probe both connections share: one bucket request to the stub."""

    def probe(provider: Broker, connection: Connection, /) -> ProbeResult:
        del provider, connection
        started = time.monotonic()
        import http.client  # noqa: PLC0415 (only the probe's one request)

        host, port = stub.url.removeprefix("http://").rstrip("/").split(":")
        connection = http.client.HTTPConnection(host, int(port), timeout=10)
        connection.request("GET", "/", headers={"User-Agent": "qmx-p-ban"})
        reply = connection.getresponse()
        code = reply.status
        retry_after = float(reply.getheader("Retry-After") or 60)
        reply.read()
        connection.close()
        if code == 429:
            raise SlowDown("http_429", retry_after=retry_after)
        if code == 418:
            raise SlowDown("http_418", retry_after=retry_after)
        if code != 200:
            raise SlowDown("http_unexpected", retry_after=retry_after)
        return ProbeResult(latency_ms=int((time.monotonic() - started) * 1000))

    return probe


def main() -> int:
    report = Report(probe=PROBE)
    declaration = describe("binance-vision")
    report.numbers["limit_scope"] = declaration.limit_scope
    report.numbers["wait_seconds"] = WAIT_SECONDS
    broker = Broker(
        id="binance",
        name="Binance",
        adapter="binance-vision",
        kind="data",
        connections=[
            Connection(id=SPOT, credential_ref="qmx/data/binance-vision", home="contabo"),
            Connection(id=FUTURES, credential_ref="qmx/data/binance-vision", home="contabo"),
        ],
    )
    with Stub() as stub:
        space = Slowdowns()
        now = time.time()
        probe = probe_with(stub)
        try:
            first: Reading = walk(
                broker, broker.connections[0], probe=probe, now=now, slowdowns=space,
                egress_ip=EGRESS,
            )
            inside = len(stub.inside_wait)
            second: Reading = walk(
                broker, broker.connections[1], probe=probe, now=time.time(), slowdowns=space,
                egress_ip=EGRESS,
            )
            waited = second.slowed_until is not None and second.slowed_until > time.time()
            report.numbers["first_word"] = first.word
            report.numbers["first_slowed_until"] = round(first.slowed_until or 0.0, 3)
            report.numbers["second_word"] = second.word
            report.numbers["other_egress_waits"] = space.remaining(
                declaration, broker.connections[1], now=time.time(), egress_ip="198.51.100.4"
            )
            report.numbers["requests_inside_wait"] = inside
            if first.word != "slowed":
                report.fail(f"the first connection read {first.word!r}, not 'slowed'")
            if not waited:
                report.fail("the first connection's wait was not shared with the second")
            if second.word != "slowed":
                report.fail(f"the second connection read {second.word!r}, not 'slowed'")
            time.sleep(WAIT_SECONDS + 0.2)
            third: Reading = walk(
                broker, broker.connections[1], probe=probe, now=time.time(), slowdowns=space,
                egress_ip=EGRESS,
            )
            report.numbers["third_word"] = third.word
            if third.word != "ok":
                report.fail(f"the connection did not recover after the wait: {third.word!r}")
            if stub.inside_wait:
                report.fail(
                    f"the stub answered {len(stub.inside_wait)} requests inside the wait"
                )
            report.note(
                "both connections waited on one egress address; no request landed inside the wait"
            )
        finally:
            common.drop_scratch()
    return report.render()


if __name__ == "__main__":
    sys.exit(main())
