"""An app env built as the supervisor builds it holds the data files its libraries read (C-38).

``uv sync --no-editable`` installs QMX's libraries as wheels, so a path that climbs out of a
package finds nothing. These build the trading node's and QMB's real envs from their locks and
read from each env's own Python, run isolated from this checkout.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NODE_APP = ROOT / "qmx-agents" / "apps" / "trading-node"
QMB_APP = ROOT / "qmx-agents" / "apps" / "qmb"
RELEASE_91_SHA256 = "044991dd5fd4ea9941289e76f1a7b65c15931d6ba4f39fab33fc24e5c3173eb2"
"""The pin ``qmx-agents/packages/qmx-broker/tests/test_protocol_default.py`` holds."""
SHIPPED = {
    "cme-crypto@1",
    "cme-energy@1",
    "cme-equity@1",
    "cme-fx@1",
    "cme-grains@1",
    "cme-metals@1",
    "cme-rates@1",
    "crypto-24x7@1",
    "de-index-cfd@1",
    "fx-24x5@1",
    "jp-index-cfd@1",
    "metals-24x5@1",
    "nyse@1",
    "uk-index-cfd@1",
    "us-index-cfd@1",
}

NODE_READS = """
import hashlib, json, sys
from pathlib import Path

from qmf.venue.proto import SPOTWARE_PROTO_PACKAGE, compile_descriptor_set
from qmn.app.server import DEFINITIONS
from qmn.observability.alerts import load_alert_allow_list
from qmn.time.calendars import market_calendars

raw = DEFINITIONS.read_bytes()
compiled = compile_descriptor_set(raw, package_name=SPOTWARE_PROTO_PACKAGE, release_tag=91)
print(json.dumps({
    "calendars": sorted(market_calendars()),
    "definitions_sha256": hashlib.sha256(raw).hexdigest(),
    "definitions_in_env": Path(sys.prefix) in DEFINITIONS.parents,
    "compiled": type(compiled).__name__,
    "alarm_list": type(load_alert_allow_list()).__name__,
    "extensions_imported": sorted(m for m in sys.modules if m.startswith("qmf.calendar_")),
    "broker_door": any(m.startswith("qmx_broker") for m in sys.modules),
}))
"""
QMB_READS = """
import json, sys

from qmb.data.gap_check import calendar_files, open_time

gold = open_time("metals-24x5@1")
print(json.dumps({
    "metals": None if gold is None else gold.ref,
    "files": len(calendar_files()),
    "extensions_imported": sorted(m for m in sys.modules if m.startswith("qmf.calendar_")),
}))
"""


def _build(app: Path, env: Path) -> Path:
    uv = shutil.which("uv")
    assert uv is not None, "uv is on PATH, as the supervisor requires"
    environment = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(env)}
    environment.pop("VIRTUAL_ENV", None)
    built = subprocess.run(
        [uv, "sync", "--frozen", "--no-editable", "--project", str(app)],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    return env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _ask(python: Path, script: str, folder: Path) -> dict[str, object]:
    asked = subprocess.run(
        [str(python), "-I", "-c", script],
        cwd=folder,
        capture_output=True,
        text=True,
        check=False,
    )
    assert asked.returncode == 0, asked.stderr
    return json.loads(asked.stdout.splitlines()[-1])


@pytest.mark.serial
def test_the_node_env_reads_every_calendar_and_its_ctrader_definitions(tmp_path: Path) -> None:
    python = _build(NODE_APP, tmp_path / "node-env")

    found = _ask(python, NODE_READS, tmp_path)

    assert set(SHIPPED) <= set(found["calendars"])  # type: ignore[arg-type]
    assert found["definitions_sha256"] == RELEASE_91_SHA256
    assert found["definitions_in_env"] is True
    assert found["compiled"] == "Ok"
    assert found["alarm_list"] == "Ok"
    assert found["broker_door"] is False


@pytest.mark.serial
def test_the_qmb_env_reads_the_gold_calendar_and_imports_no_extension(tmp_path: Path) -> None:
    python = _build(QMB_APP, tmp_path / "qmb-env")

    found = _ask(python, QMB_READS, tmp_path)

    assert found == {"metals": "metals-24x5@1", "files": 15, "extensions_imported": []}


def test_the_definitions_file_is_the_pinned_one_in_the_venue_package() -> None:
    held = ROOT / "packages/qmf-venue/src/qmf/venue/protocol/openapi-91.pb"

    assert hashlib.sha256(held.read_bytes()).hexdigest() == RELEASE_91_SHA256
    assert not (
        ROOT / "qmx-agents/packages/qmx-broker/src/qmx_broker/protocol/openapi-91.pb"
    ).exists()
