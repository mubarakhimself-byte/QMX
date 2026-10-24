"""The PC's upload door: bytes stream on to the server while a staging copy is kept, a resume
re-hashes what the PC holds, and the staging copy goes only when two durable copies exist
(Library AD-10, AD-27)."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from qmx_control.server import COPIES_REQUIRED, STAGING, UPLOAD_ROUTE, upload_router

KEY = "pairing-key-of-this-test"
TOKEN = "local-bearer-of-this-test"


class FakeHub(BaseHTTPRequestHandler):
    """The server's upload door, as far as the PC can tell: append, hash, answer the copies."""

    protocol_version = "HTTP/1.1"
    held: dict[str, bytes] = {}
    copies: int = 2
    seen: list[dict[str, Any]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        upload_id = self.headers["X-Upload-Id"]
        held = self.held.get(upload_id, b"")
        offset = int(self.headers.get("X-Upload-Offset") or 0)
        assert offset == len(held)
        announced = self.headers.get("X-Upload-Partial-Sha256")
        if announced is not None:
            assert announced == sha256(held).hexdigest()
        body = self.rfile.read(length)
        self.held[upload_id] = held + body
        self.seen.append({"upload_id": upload_id, "offset": offset, "length": length})
        total = self.headers.get("X-Upload-Total")
        whole = self.held[upload_id]
        if total is not None and len(whole) < int(total):
            self._answer(
                HTTPStatus.ACCEPTED,
                {"upload_id": upload_id, "offset": len(whole), "sha256": sha256(whole).hexdigest()},
            )
            return
        self._answer(
            HTTPStatus.OK,
            {
                "ok": True,
                "blob_id": f"sha256:{sha256(whole).hexdigest()}",
                "bytes": len(whole),
                "sha256": sha256(whole).hexdigest(),
                "copies": self.copies,
                "upload_id": upload_id,
            },
        )

    def _answer(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def door(tmp_path: Path) -> Iterator[tuple[TestClient, Path, FakeHub]]:
    FakeHub.held, FakeHub.seen, FakeHub.copies = {}, [], COPIES_REQUIRED
    hub = ThreadingHTTPServer(("127.0.0.1", 0), FakeHub)
    thread = threading.Thread(target=hub.serve_forever, daemon=True)
    thread.start()
    home = tmp_path / "home"
    (home / "vault").mkdir(parents=True)
    (home / "vault" / "pairing-key").write_text(KEY, encoding="utf-8")
    (home / "settings.toml").write_text(
        f'[library]\nprimary = "server"\nhub_url = "http://127.0.0.1:{hub.server_address[1]}"\n',
        encoding="utf-8",
    )
    app = FastAPI()
    app.include_router(upload_router(home))
    try:
        yield TestClient(app), home, FakeHub
    finally:
        hub.shutdown()
        hub.server_close()
        thread.join(timeout=5)


def test_the_bytes_reach_the_server_and_the_staging_copy_goes_with_two_copies(
    door: tuple[TestClient, Path, FakeHub],
) -> None:
    client, home, hub = door
    data = b"the book that must be searchable" * 100_000

    answer = client.post(
        UPLOAD_ROUTE,
        content=data,
        headers={"X-Upload-Id": "up-1", "X-Upload-Name": "book.pdf"},
    )

    assert answer.status_code == 200
    assert answer.json()["sha256"] == sha256(data).hexdigest()
    assert answer.json()["staging_kept"] is False
    assert b"".join(hub.held.values()) == data
    assert not (home / STAGING / "up-1.part").exists()


def test_one_copy_keeps_the_staging_part_and_its_manifest(
    door: tuple[TestClient, Path, FakeHub],
) -> None:
    client, home, hub = door
    hub.copies = 1
    data = b"kept until the bucket has it"

    answer = client.post(UPLOAD_ROUTE, content=data, headers={"X-Upload-Id": "up-2"})
    staged = client.get(f"{UPLOAD_ROUTE}/up-2")
    manifest = json.loads((home / STAGING / "up-2.json").read_text(encoding="utf-8"))
    discarded = client.delete(f"{UPLOAD_ROUTE}/up-2")

    assert answer.json()["staging_kept"] is True
    assert staged.json()["offset"] == len(data)
    assert staged.json()["staging"] is True
    assert manifest["blob_id"] == f"sha256:{sha256(data).hexdigest()}"
    assert discarded.json() == {"discarded": "up-2"}
    assert not (home / STAGING / "up-2.part").exists()


def test_a_resumed_upload_asks_the_partial_hash_before_it_takes_more(
    door: tuple[TestClient, Path, FakeHub],
) -> None:
    client, _, hub = door
    head, tail = b"a" * 4096, b"b" * 8192
    opened = client.post(
        UPLOAD_ROUTE,
        content=head,
        headers={"X-Upload-Id": "up-3", "X-Upload-Total": str(len(head) + len(tail))},
    )
    wrong = client.post(
        UPLOAD_ROUTE,
        content=tail,
        headers={
            "X-Upload-Id": "up-3",
            "X-Upload-Offset": str(len(head)),
            "X-Upload-Partial-Sha256": "00" * 32,
            "X-Upload-Total": str(len(head) + len(tail)),
        },
    )
    done = client.post(
        UPLOAD_ROUTE,
        content=tail,
        headers={
            "X-Upload-Id": "up-3",
            "X-Upload-Offset": str(len(head)),
            "X-Upload-Partial-Sha256": sha256(head).hexdigest(),
            "X-Upload-Total": str(len(head) + len(tail)),
        },
    )

    assert (opened.status_code, opened.json()["offset"]) == (202, len(head))
    assert (wrong.status_code, wrong.json()["detail"]["code"]) == (409, "hash_mismatch")
    assert done.status_code == 200
    assert done.json()["sha256"] == sha256(head + tail).hexdigest()
    assert hub.held["up-3"] == head + tail
