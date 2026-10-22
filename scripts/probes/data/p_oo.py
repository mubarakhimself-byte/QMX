"""P-OO: OpenObserve 1.0.4's memory and disk per day under a synthetic day of QMX telemetry.

The probe replays the records QMX's write points would send in one day (one heartbeat row per
agent per 30 s, the day's span rows and the day's log lines), points them at OpenObserve on the
server's own disk, and reads three numbers while the service holds them: peak resident memory of
the whole service process group, the disk its data folder occupies, and how long the day took to
replay. The disk figure is the day's storage because exactly one day is replayed; a run with
`--scale` below 1 records the figure it would reach at a full day.

OpenObserve publishes no asset on its GitHub tag: `v1.0.4`'s release asset list is empty and the
published download is on `downloads.openobserve.ai`. That URL is pinned here, and the FINDINGS
row names it as the departure from "from its GitHub release".

Run it on the server as `qmx` from `/srv/qmx/check/prb-ds/checkout`:

    /srv/qmx/check/prb-ds/venv-oo/bin/python scripts/probes/data/p_oo.py

Credentials are made for the run, live only in the child's environment, and are never printed.
"""

from __future__ import annotations

import argparse
import base64
import json
import secrets
import signal
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Final

import server_common as common

PROBE: Final[str] = "P-OO"
OO_VERSION: Final[str] = "1.0.4"
OO_URL: Final[str] = (
    "https://downloads.openobserve.ai/releases/openobserve/v1.0.4/"
    "openobserve-v1.0.4-linux-amd64.tar.gz"
)
DOWNLOADS: Final[Path] = common.PROBE_ROOT / "downloads"
ORG: Final[str] = "default"
BATCH: Final[int] = 1_000
"""Records per request: a day's real shape in batches small enough to watch memory move."""


def fetch(log: common.Log) -> Path:
    """The OpenObserve binary, downloaded once and unpacked beside the probe."""
    home = DOWNLOADS / f"openobserve-v{OO_VERSION}"
    binary = home / "openobserve"
    if binary.exists():
        log.say(f"reuse {binary}")
        return binary
    archive = DOWNLOADS / f"openobserve-v{OO_VERSION}-linux-amd64.tar.gz"
    common.download_file(OO_URL, archive)
    home.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as bundle:
        bundle.extractall(home)  # noqa: S202 - the pinned release's own archive
    log.say(f"unpacked {binary}")
    return binary


def day_records(
    agents: int, interval_s: int, day_seconds: int, spans: int, logs: int
) -> list[dict[str, object]]:
    """One day of the three write points, in the order a host would send them."""
    records: list[dict[str, object]] = []
    for index in range((day_seconds // interval_s) * agents):
        records.append(
            {
                "stream": "heartbeat",
                "run_id": f"run-{index % 97:03d}",
                "agent": f"agent-{index % agents:02d}",
                "at": 1_785_000_000 + index * interval_s,
                "cpu_seconds": round(index * 0.1, 1),
                "rss_mb": 340 + index % 64,
                "machine_minutes": 0.5,
                "capacity_in_use": 0.031,
                "host": "server",
                "free_disk_mb": 163_840,
            }
        )
    for index in range(spans):
        records.append(
            {
                "stream": "span",
                "trace_id": f"trace-{index % 977:04d}",
                "span": "workflow.step",
                "at": 1_785_000_000 + index * 3,
                "duration_ms": 12 + index % 500,
                "status": "ok" if index % 11 else "error",
            }
        )
    for index in range(logs):
        records.append(
            {
                "stream": "log",
                "at": 1_785_000_000 + index * 2,
                "level": "info" if index % 37 else "warning",
                "service": "qmx_host",
                "message": f"step {index} finished in {index % 900} ms with {index % 7} rows",
            }
        )
    return records


def start(
    binary: Path, port: int, data_dir: Path, email: str, password: str
) -> subprocess.Popen[bytes]:
    """The service in its own session, so its memory and its exit are both the probe's to read."""
    env = common.child_env(
        ZO_ROOT_USER_EMAIL=email,
        ZO_ROOT_USER_PASSWORD=password,
        ZO_DATA_DIR=str(data_dir),
        ZO_HTTP_PORT=str(port),
        ZO_TELEMETRY="false",
    )
    log_path = common.PROBE_ROOT / "logs" / "prb-ds-oo-service.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        [str(binary)],
        stdout=log_path.open("ab"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )


def login(base: str, email: str, password: str, log: common.Log) -> str:
    """OpenObserve's token for the ingest calls, or the password itself when login is basic-only."""
    body = json.dumps({"name": email, "password": password}).encode()
    request = urllib.request.Request(  # noqa: S310
        f"{base}/auth/login", data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        log.say(f"login answered {error.code}: basic auth on ingest")
        return password
    token = payload.get("token") or (payload.get("data") or {}).get("token") or ""
    log.say(f"login: {'token' if token else 'no token, basic auth on ingest'}")
    return token or password


def ingest(
    base: str, email: str, secret: str, records: list[dict[str, object]], log: common.Log
) -> dict[str, int]:
    """Every record, in batches, one stream at a time. Returns the rows and bytes it sent."""
    auth = base64.b64encode(f"{email}:{secret}".encode()).decode()
    sent = {"rows": 0, "bytes": 0}
    for stream in ("heartbeat", "span", "log"):
        rows = [record for record in records if record["stream"] == stream]
        for start_at in range(0, len(rows), BATCH):
            chunk = rows[start_at : start_at + BATCH]
            body = json.dumps(chunk).encode()
            request = urllib.request.Request(  # noqa: S310
                f"{base}/api/{ORG}/{stream}/_json",
                data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                    response.read()
            except urllib.error.HTTPError as error:
                raise RuntimeError(
                    f"{stream} ingest answered {error.code}: {error.read()[:200]!r}"
                ) from error
            sent["rows"] += len(chunk)
            sent["bytes"] += len(body)
        log.say(f"{stream}: {len(rows)} rows sent")
    return sent


def stop(
    process: subprocess.Popen[bytes] | None, sampler: common.PeakSampler | None, log: common.Log
) -> None:
    """No probe service outlives its run: the whole group gets SIGTERM, then SIGKILL."""
    if sampler is not None:
        sampler.stop()
    if process is None or process.poll() is not None:
        return
    common.signal_pgroup(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        common.signal_pgroup(process.pid, signal.SIGKILL)
        process.wait(timeout=30)
    log.say(f"service stopped, exit {process.returncode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", type=int, default=20)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--day-seconds", type=int, default=86_400)
    parser.add_argument("--spans", type=int, default=20_000)
    parser.add_argument("--logs", type=int, default=5_000)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--start-timeout", type=float, default=180.0)
    args = parser.parse_args(argv)

    log = common.Log("prb-ds-oo")
    report = common.Report(PROBE)
    report.numbers.update({"openobserve_version": OO_VERSION, "url": OO_URL})
    process: subprocess.Popen[bytes] | None = None
    sampler: common.PeakSampler | None = None
    email, password = "qmx-probe@localhost", secrets.token_urlsafe(24)
    port = common.free_port()
    base = f"http://127.0.0.1:{port}"
    data_dir = common.PROBE_ROOT / "oo-data"
    try:
        binary = fetch(log)
        report.numbers["free_before_mb"] = common.free_mb()
        began = time.perf_counter()
        process = start(binary, port, data_dir, email, password)
        sampler = common.PeakSampler(process.pid, 1.0)
        sampler.start()
        if not common.wait_http(f"{base}/healthz", timeout_s=args.start_timeout):
            raise RuntimeError(f"the service does not start within {args.start_timeout} s")
        report.numbers["start_seconds"] = round(time.perf_counter() - began, 1)
        report.numbers["idle_peak_mb"] = common.group_peak_mb(process.pid)
        log.say(
            f"service up in {report.numbers['start_seconds']} s, "
            f"{report.numbers['idle_peak_mb']} MB idle"
        )
        secret = login(base, email, password, log)
        records = day_records(args.agents, args.interval, args.day_seconds, args.spans, args.logs)
        if args.scale != 1.0:
            records = records[: max(1, int(len(records) * args.scale))]
        sent = ingest(base, email, secret, records, log)
        replay = time.perf_counter() - began
        time.sleep(5.0)
        disk_mb = common.du_mb(data_dir)
        report.numbers.update(
            rows=sent["rows"],
            bytes=sent["bytes"],
            replay_seconds=round(replay, 1),
            peak_mb=sampler.peak_mb,
            disk_mb=disk_mb,
            disk_per_day_mb=round(disk_mb / args.scale, 1) if args.scale else disk_mb,
            free_after_mb=common.free_mb(),
        )
        report.note(
            f"one day replayed in {report.numbers['replay_seconds']} s: {sent['rows']} rows, "
            f"{sampler.peak_mb} MB peak, {disk_mb} MB on disk"
        )
    except Exception as error:
        report.fail(f"{type(error).__name__}: {error}")
        log.say(f"error: {report.problems[-1]}")
    finally:
        stop(process, sampler, log)
        log.close()
    return report.render()


if __name__ == "__main__":
    raise SystemExit(main())
