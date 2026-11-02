"""The shipped MIS app passes the real road: its own tests, then its proofs, then it starts.

No recorded evidence stands in here. The road runs `tests/` by unittest discovery in the app's
own environment, then `proofs/sandbox.json` with the network refused and `proofs/shadow.json`
on the read-only tools. The MIS is not a money app, so its shadow stage publishes it.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from qmx_apps.errors import Document
from qmx_apps.road.models import STAGES
from qmx_apps.supervisor import Supervisor

APP_FOLDER = Path(__file__).resolve().parents[1]
APP = "mis"


def test_the_app_passes_every_road_stage_and_starts_unconfigured(tmp_path: Path) -> None:
    owner = Supervisor(tmp_path / "home")
    try:
        revision = str(owner.install(APP_FOLDER, trust="first_party")["definition_hash"])
        for stage in STAGES[1:4]:
            owner.road.advance(APP, revision, stage)
        owner.start(APP)
        state = cast(Document, owner.call(APP, "status", {})["result"])
        evidence = owner.road.evidence(APP)
    finally:
        owner.close()

    assert cast(Document, state["value"])["state"] == "not configured"
    assert [(record["stage"], record["passed"]) for record in evidence] == [
        ("build", True),
        ("tests", True),
        ("sandbox", True),
        ("shadow", True),
        ("live", True),
    ]
    own = cast(Document, evidence[1]["results"])
    assert (own["tests_run"], own["skipped"], own["failures"], own["errors"]) == (7, 0, [], [])
