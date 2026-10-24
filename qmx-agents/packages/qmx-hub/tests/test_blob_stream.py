"""The Hub's streaming door: bytes move in chunks both ways, a resume re-hashes its partial, and
no request body meets a 64 MB limit (Library AD-10, AD-27)."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.store import Store

from qmx_hub.server import UPLOAD_ROUTE, Hub, in_process, serve

KEY = "pairing-key-of-this-test"
URL = "http://127.0.0.1:{port}"


@pytest.fixture
def server(tmp_path: Path) -> Iterator[tuple[str, Store]]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as store:
        running = serve(Hub(store), host="127.0.0.1", port=0, key=KEY)
        thread = threading.Thread(target=running.serve_forever, daemon=True)
        thread.start()
        try:
            yield URL.format(port=running.server_address[1]), store
        finally:
            running.shutdown()
            running.server_close()
            thread.join(timeout=5)


def call(
    method: str, url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None
) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(  # noqa: S310 (the test's own loopback server)
        url,
        data=data,
        headers={"Authorization": f"Bearer {KEY}", **(headers or {})},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as answer:  # noqa: S310
            body = answer.read()
            return answer.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_the_upload_door_takes_a_body_larger_than_the_old_64_mb_limit(
    server: tuple[str, Store],
) -> None:
    url, store = server
    data = b"x" * (66 * 1024 * 1024)

    status, answer = call("POST", f"{url}/v1/blob", data=data)

    assert status == 200
    assert answer["blob_id"] == f"sha256:{sha256(data).hexdigest()}"
    assert answer["bytes"] == len(data)
    assert store.has_blob(str(answer["blob_id"]))


def test_a_resumed_upload_rehashes_its_partial_and_keeps_what_it_holds(
    server: tuple[str, Store],
) -> None:
    url, _ = server
    head, tail = b"a" * 4096, b"b" * 8192
    opened, first = call(
        "POST",
        f"{url}{UPLOAD_ROUTE}",
        data=head,
        headers={"X-Upload-Id": "up-9", "X-Upload-Total": str(len(head) + len(tail))},
    )
    status, before = call("GET", f"{url}{UPLOAD_ROUTE}/up-9")
    wrong, refused = call(
        "POST",
        f"{url}{UPLOAD_ROUTE}",
        data=tail,
        headers={
            "X-Upload-Id": "up-9",
            "X-Upload-Offset": str(len(head)),
            "X-Upload-Partial-Sha256": "00" * 32,
            "X-Upload-Total": str(len(head) + len(tail)),
        },
    )
    done, landed = call(
        "POST",
        f"{url}{UPLOAD_ROUTE}",
        data=tail,
        headers={
            "X-Upload-Id": "up-9",
            "X-Upload-Offset": str(len(head)),
            "X-Upload-Partial-Sha256": sha256(head).hexdigest(),
            "X-Upload-Total": str(len(head) + len(tail)),
        },
    )

    assert (opened, first["offset"], first["sha256"]) == (
        202,
        len(head),
        sha256(head).hexdigest(),
    )
    assert (status, before["offset"]) == (200, len(head))
    assert (wrong, refused["code"]) == (409, "hash_mismatch")
    assert done == 200
    assert landed["sha256"] == sha256(head + tail).hexdigest()
    request = urllib.request.Request(  # noqa: S310
        f"{url}/v1/blob/{landed['sha256']}", headers={"Authorization": f"Bearer {KEY}"}
    )
    fetched = urllib.request.urlopen(request, timeout=30).read()  # noqa: S310
    assert fetched == head + tail


def test_the_one_process_router_streams_the_same_upload(tmp_path: Path) -> None:
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    data = b"streamed through the host" * 100_000
    with Store.open(tmp_path / "host", redactor=redact, name="server") as store:
        app = FastAPI()
        app.include_router(in_process(Hub(store, buckets=(tmp_path / "bucket",)), KEY))
        with TestClient(app) as client:
            answer = client.post(
                UPLOAD_ROUTE,
                content=data,
                headers={"Authorization": f"Bearer {KEY}", "X-Upload-Id": "host-1"},
            )
            fetched = client.get(
                f"/v1/blob/{answer.json()['sha256']}",
                headers={"Authorization": f"Bearer {KEY}"},
            )

    assert answer.status_code == 200
    assert answer.json()["copies"] == 1
    assert fetched.content == data
