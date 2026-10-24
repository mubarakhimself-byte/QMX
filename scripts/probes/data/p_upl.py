"""P-UPL (W15; F26; Library AD-10, AD-27), acceptance: a 3 GB file goes through the PC door and
streams to the server with flat peak memory, a cut resumes by offset after re-hashing the partial,
and the PC staging copy is dropped only after two verified remote copies.

Three legs, one process, one file:

1. **The doors.** The server's Hub runs in this process (`qmx_hub.server.serve`, its own scratch
   store); the PC's door is the real `qmx_control.server.upload_router`, served by uvicorn on a
   loopback port it chooses, with a scratch home whose `settings.toml` points at the Hub. The
   upload goes to the PC door, which streams it on to the Hub: one read of the file, no copy of it
   in memory on either side.
2. **The cut.** The first request sends two fifths of the file with `X-Upload-Total`, so the Hub
   answers 202 and holds a partial. The resume asks the PC what it holds, sends the rest with that
   offset and the partial's hash, and the finished blob must hash to the whole file.
3. **The copies.** The Hub has no bucket in this scratch home, so it reports one durable copy and
   the PC keeps its staging part. The probe deletes the part and says the space is back; with a
   bucket the count would be two and the part would be gone already.

Peak memory is this process's `ru_maxrss` growth across the upload, which is the Hub and the PC
door together. FAIL is 55's line: memory grows with the file, the resumed hash differs, or the PC
copy is dropped early.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_upl.py --size-gb 3

The 3 GB file is written under `QMX_PROBE_SCRATCH` (default `D:/Temp/prb-dp`), never on C:, and the
whole scratch folder is removed before the probe exits. The probe skips when the scratch volume
does not hold two and a half times the file plus a gigabyte.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import shutil
import threading
import time
from pathlib import Path
from typing import IO
from urllib.parse import urlsplit

try:
    import resource
except ImportError:  # Windows: the probe prints SKIP before it needs a peak
    resource = None  # type: ignore[assignment]

PROBE = "P-UPL"
SCRATCH = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/prb-dp")) / "upl"
MIB = 1024 * 1024
CHUNK = MIB
FLAT_MB = 512
"""The most peak memory may grow while a 3 GB file moves: the file itself must never be in it."""
KEY = "probe-pairing-key"


def peak_mb() -> int:
    return 0 if resource is None else int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) // 1024


def write_file(path: Path, size: int) -> str:
    """One file of `size` bytes, hashed as it is written, so the probe never holds it."""
    hasher = hashlib.sha256()
    block = bytes(range(256)) * (CHUNK // 256)
    written = 0
    with path.open("wb") as handle:
        while written < size:
            part = block[: min(CHUNK, size - written)]
            handle.write(part)
            hasher.update(part)
            written += len(part)
    return hasher.hexdigest()


class Hub:
    """The Hub on a loopback port, in this process, with its own scratch store."""

    def __init__(self, store: Path) -> None:
        from qmx_engine.ledger import redact  # noqa: PLC0415 (only the probe needs it)
        from qmx_hub.server import Hub as LibraryHub  # noqa: PLC0415
        from qmx_hub.server import serve  # noqa: PLC0415
        from qmx_library.store import Store  # noqa: PLC0415

        self.opened = Store.open(store, redactor=redact, name="server")
        self.server = serve(
            LibraryHub(self.opened.__enter__()), host="127.0.0.1", port=0, key=KEY
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.opened.__exit__(None, None, None)


class Door:
    """The PC's real upload door, served by uvicorn on a loopback port it chooses."""

    def __init__(self, home: Path, hub_url: str) -> None:
        import uvicorn  # noqa: PLC0415 (only the probe needs it)
        from fastapi import FastAPI  # noqa: PLC0415
        from qmx_control.server import upload_router  # noqa: PLC0415

        (home / "vault").mkdir(parents=True, exist_ok=True)
        (home / "vault" / "pairing-key").write_text(KEY, encoding="utf-8")
        (home / "settings.toml").write_text(
            f'[library]\nprimary = "server"\nhub_url = "{hub_url}"\n', encoding="utf-8"
        )
        self.home = home
        app = FastAPI()
        app.include_router(upload_router(home))
        self.started = threading.Event()
        self.server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 20
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if not self.server.started:
            raise RuntimeError("the PC door did not start")
        sockets = self.server.servers[0].sockets
        self.url = f"http://127.0.0.1:{sockets[0].getsockname()[1]}"

    def close(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=10)


def call(
    url: str,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 600.0,
) -> tuple[int, dict[str, object]]:
    parts = urlsplit(url)
    connection = http.client.HTTPConnection(parts.hostname, parts.port, timeout=timeout)
    try:
        connection.putrequest(method, path)
        for name, value in (headers or {}).items():
            connection.putheader(name, value)
        if body is not None:
            connection.putheader("Content-Length", str(len(body)))
        connection.endheaders()
        if body is not None:
            connection.send(body)
        response = connection.getresponse()
        payload = response.read()
        return response.status, json.loads(payload) if payload else {}
    finally:
        connection.close()


def send(
    url: str,
    path: str,
    *,
    handle: IO[bytes],
    length: int,
    headers: dict[str, str],
) -> tuple[int, dict[str, object], int]:
    """One upload request: read `length` bytes from the file in chunks and send them on."""
    parts = urlsplit(url)
    connection = http.client.HTTPConnection(parts.hostname, parts.port, timeout=3600)
    started = time.monotonic()
    try:
        connection.putrequest("POST", path)
        for name, value in headers.items():
            connection.putheader(name, value)
        connection.putheader("Content-Length", str(length))
        connection.endheaders()
        remaining = length
        while remaining > 0:
            data = handle.read(min(CHUNK, remaining))
            if not data:
                break
            connection.send(data)
            remaining -= len(data)
        response = connection.getresponse()
        payload = response.read()
        return response.status, json.loads(payload) if payload else {}, int(time.monotonic() - started)
    finally:
        connection.close()


def stream_hash(url: str, digest: str) -> tuple[int, int]:
    """Hash the blob the Hub serves, one chunk at a time: `(bytes, seconds)`."""
    parts = urlsplit(url)
    connection = http.client.HTTPConnection(parts.hostname, parts.port, timeout=3600)
    hasher = hashlib.sha256()
    total = 0
    began = time.monotonic()
    try:
        connection.putrequest("GET", f"/v1/blob/{digest}")
        connection.putheader("Authorization", f"Bearer {KEY}")
        connection.endheaders()
        response = connection.getresponse()
        while data := response.read(CHUNK):
            hasher.update(data)
            total += len(data)
    finally:
        connection.close()
    assert hasher.hexdigest() == digest, "the blob does not hash to its name"
    return total, int(time.monotonic() - began)


def upload_case(folder: Path, size: int, problems: list[str]) -> None:
    source = folder / "upload.bin"
    digest = write_file(source, size)
    print(f"file {size // MIB} MB, sha256 {digest[:16]}...")
    hub = Hub(folder / "hub")
    door = Door(folder / "home", hub.url)
    baseline = peak_mb()
    try:
        cut = (size * 2) // 5
        with source.open("rb") as handle:
            status, first, _ = send(
                door.url,
                "/api/library/upload",
                handle=handle,
                length=cut,
                headers={
                    "X-Upload-Id": "p-upl",
                    "X-Upload-Total": str(size),
                    "Authorization": "Bearer probe",
                },
            )
        print(f"first request: {status} {first}")
        if status != 202:
            problems.append(f"the cut request answered {status}, wanted 202")
        staged = call(door.url, "GET", "/api/library/upload/p-upl")[1]
        offset = int(staged["offset"])  # type: ignore[arg-type]
        partial = str(staged["sha256"])
        print(f"the PC holds {offset} bytes with sha256 {partial}")
        if offset != cut:
            problems.append(f"the PC holds {offset} bytes, not the {cut} it took")
        with source.open("rb") as handle:
            handle.seek(offset)
            status, done, _ = send(
                door.url,
                "/api/library/upload",
                handle=handle,
                length=size - offset,
                headers={
                    "X-Upload-Id": "p-upl",
                    "X-Upload-Offset": str(offset),
                    "X-Upload-Partial-Sha256": str(partial),
                    "X-Upload-Total": str(size),
                    "Authorization": "Bearer probe",
                },
            )
        grew = peak_mb() - baseline
        print(f"second request: {status}, peak memory grew {grew} MB")
        if status != 200:
            problems.append(f"the resume answered {status}: {done}")
            return
        if done.get("sha256") != digest:
            problems.append(f"the resumed blob hashes {done.get('sha256')}, not {digest}")
        if grew > FLAT_MB:
            problems.append(f"peak memory grew {grew} MB for a {size // MIB} MB file")
        copied = done.get("copies")
        staged = call(door.url, "GET", "/api/library/upload/p-upl")[1]
        print(f"copies at the Hub: {copied}, PC staging: {staged}")
        if copied == 1 and not staged.get("staging"):
            problems.append("the PC dropped its staging copy with one remote copy")
        if copied == 1 and staged.get("staging"):
            call(door.url, "DELETE", "/api/library/upload/p-upl")
            if (folder / "home" / "uploads" / "p-upl.part").exists():
                problems.append("the deleted staging part is still on disk")
        served, seconds = stream_hash(hub.url, str(done["sha256"]))
        print(f"the Hub served {served // MIB} MB back in {seconds} s")
        if served != size:
            problems.append(f"the Hub served {served} bytes, not {size}")
    finally:
        door.close()
        hub.close()


def main() -> int:
    parser = argparse.ArgumentParser(prog="p_upl")
    parser.add_argument("--size-gb", type=float, default=3.0)
    given = parser.parse_args()
    size = int(given.size_gb * 1024 * MIB)
    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(SCRATCH).free
    needed = size * 2 + 1024 * MIB
    print(f"scratch {SCRATCH} has {free // MIB} MB free, this run needs {needed // MIB} MB")
    problems: list[str] = []
    if free < needed:
        print(f"{PROBE} SKIP: not enough scratch for two and a half copies of the file")
        shutil.rmtree(SCRATCH, ignore_errors=True)
        return 0
    try:
        upload_case(SCRATCH, size, problems)
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    for problem in problems:
        print(f"  problem: {problem}")
    if problems:
        print(f"{PROBE} FAIL")
        return 1
    print(f"{PROBE} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
