"""The Hub over HTTP: health, one `LibraryPort` verb round trip, a claim swap, and the pairing
key as the only door (Library AD-11)."""

from __future__ import annotations

import threading
import urllib.error
from collections.abc import Iterator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.client import HubClient
from qmx_library.port import Draft
from qmx_library.store import Store

from qmx_hub.server import Hub, serve

KEY = "pairing-key-of-this-test"


@pytest.fixture
def hub(tmp_path: Path) -> Iterator[tuple[HubClient, Store]]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as store:
        server = serve(Hub(store), host="127.0.0.1", port=0, key=KEY)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        home = tmp_path / "home"
        (home / "vault").mkdir(parents=True)
        (home / "vault" / "pairing-key").write_text(KEY, encoding="utf-8")
        url = f"http://127.0.0.1:{server.server_address[1]}"
        (home / "settings.toml").write_text(
            f'[library]\nprimary = "server"\nhub_url = "{url}"\n', encoding="utf-8"
        )
        try:
            yield HubClient.connect(home, who="operator"), store
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def test_the_hub_answers_health_and_round_trips_a_save(hub: tuple[HubClient, Store]) -> None:
    client, store = hub

    health = client.health()
    done = client.put(Draft("note", "n1", title="over the wire"), on="main", expected_head=None)
    view = client.get(done.object_id)

    refs = {row.ref: row.head for row in client.refs()}

    assert health["primary"] == "server"
    assert health["role"] == "writer"
    assert view["title"] == "over the wire"
    assert store.head("n1", "main") == (done.object_id, 1)
    assert refs["main"] == done.object_id
    assert "refs/hub/health" in refs


def test_a_claim_is_a_swap_over_the_wire(hub: tuple[HubClient, Store]) -> None:
    client, _ = hub

    first = client.claim("fingerprint:paper-17", "run-a", 60)
    second = client.claim("fingerprint:paper-17", "run-b", 60)
    client.release("fingerprint:paper-17", "run-a")
    third = client.claim("fingerprint:paper-17", "run-b", 60)

    assert (first.granted, second.granted, third.granted) == (True, False, True)
    assert second.run_id == "run-a"


def test_a_wrong_key_is_refused(hub: tuple[HubClient, Store]) -> None:
    client, _ = hub
    impostor = HubClient(client.url, "not-the-key", "operator")

    with pytest.raises(urllib.error.HTTPError) as refused:
        impostor.health()

    assert refused.value.code == 401
