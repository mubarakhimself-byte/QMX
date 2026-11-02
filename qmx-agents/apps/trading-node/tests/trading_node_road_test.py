"""The shipped trading-node app passes the real road: its own tests, then its proofs.

No recorded evidence stands in here. The road runs `tests/` by unittest discovery in the app's
own environment, then `proofs/sandbox.json` with the network refused and `proofs/shadow.json`
on the read-only tools. The keys document is a fake with no venue in it.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import cast

from qmx_apps.errors import Document
from qmx_apps.road.models import STAGES
from qmx_apps.supervisor import Supervisor

APP_FOLDER = Path(__file__).resolve().parents[1]
APP = "trading-node"
KEYS = '{"schema_version": "qmx.node.keys/1"}'


def test_the_app_passes_every_road_stage_and_starts_ready(tmp_path: Path) -> None:
    owner = Supervisor(tmp_path / "home", secret_getter=lambda _service, _name: KEYS)
    try:
        revision = str(owner.install(APP_FOLDER, trust="first_party")["definition_hash"])
        for stage in STAGES[1:4]:
            owner.road.advance(APP, revision, stage)
        owner.road.signing_key(secrets.token_urlsafe(32))
        owner.road.publish(APP, revision, signature=owner.road.sign(APP, revision, None))
        owner.start(APP)
        state = cast(Document, owner.call(APP, "status", {})["result"])
        evidence = owner.road.evidence(APP)
    finally:
        owner.close()

    assert cast(Document, state["value"])["headline"] == "Ready, no units yet"
    assert [(record["stage"], record["passed"]) for record in evidence] == [
        ("build", True),
        ("tests", True),
        ("sandbox", True),
        ("shadow", True),
        ("live", True),
    ]
