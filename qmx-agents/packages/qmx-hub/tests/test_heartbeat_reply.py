"""The Hub's heartbeat route (AD-65): the PC's row writes the one pause flag, the reply carries
it back with the claim batch's count, and no other host's row can move it."""

from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path

from qmx_engine.heartbeat import UNKNOWN, Heartbeat, Pause
from qmx_engine.ledger import redact
from qmx_library.store import Store

from qmx_hub.server import Hub, serve

KEY = "pairing-key-of-this-test"
AT = "2026-10-22T00:00:00+00:00"


def row(**changes: object) -> Heartbeat:
    fields: dict[str, object] = {
        "subject": "host",
        "id": "pc",
        "at": AT,
        "cpu_seconds": 12.0,
        "rss_bytes": 1_024,
        "machine_minutes": 3.0,
        "claims": ("fingerprint:ops2",),
        "qmx_version": "0.1.0",
        "kinds_digest": "digest",
        "paused": True,
    }
    return Heartbeat.model_validate({**fields, **changes})


def test_the_pcs_row_writes_the_flag_and_its_claims_are_renewed(tmp_path: Path) -> None:
    home = tmp_path / "hub-home"
    home.mkdir()
    with Store.open(tmp_path / "server", redactor=redact, name="server") as store:
        hub = Hub(store, home=home)
        claim = store.claim(store.engine, "fingerprint:ops2", "run-1", 60)

        paused, renewed = hub.hear(row().model_dump(mode="json"))
        elsewhere, _ = hub.hear(row(id="contabo", paused=False, claims=()).model_dump(mode="json"))

    written = json.loads((home / "autonomy.json").read_text(encoding="utf-8"))
    assert (claim.granted, paused, renewed) == (True, True, 1)
    assert elsewhere is True
    assert (written["paused"], written["at"]) == (True, AT)


def test_the_route_answers_with_the_flag_and_the_claim_batch(tmp_path: Path) -> None:
    home = tmp_path / "hub-home"
    home.mkdir()
    with Store.open(tmp_path / "server", redactor=redact, name="server") as store:
        hub = Hub(store, home=home)
        store.claim(store.engine, "fingerprint:ops2", "run-1", 60)
        server = serve(hub, host="127.0.0.1", port=0, key=KEY)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_address[1]}/v1/heartbeat",
            data=json.dumps({"heartbeat": row().model_dump(mode="json")}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as answer:  # noqa: S310
                reply = json.loads(answer.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    assert reply == {"autonomy_paused": True, "claims_renewed": 1}


def test_a_row_without_its_reply_leaves_the_flag_standing_and_says_unknown() -> None:
    pause = Pause(paused=True, heard_at=1_000.0, source="hub")

    assert pause.state(1_299.0) == "known"
    assert (pause.shows(1_300.0), pause.flag(1_300.0)) == (UNKNOWN, True)
