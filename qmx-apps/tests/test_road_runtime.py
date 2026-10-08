"""Actual locked app tests, recorded sandbox, live HTTP shadow and T1 activation."""

from __future__ import annotations

import json
import secrets
import shutil
import sqlite3
import threading
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast

import pytest

from qmx_apps.errors import AppError, Document
from qmx_apps.supervisor import Supervisor

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/apps/exchange-status"
OWN_TEST = """import json, os, socket, unittest
from pathlib import Path
class OwnTests(unittest.TestCase):
    def test_recorded_environment(self):
        self.assertEqual(os.environ["QMX_STAGE"], "tests")
        self.assertNotIn("DECLARED_SECRET", os.environ)
        self.assertEqual(json.loads(Path("data/source.json").read_text())["recorded"], 7)
        with socket.socket() as connection:
            with self.assertRaises(PermissionError):
                connection.connect(("127.0.0.1", 1))
        Path("data/tests-ran.txt").write_text("actual own tests")
"""


@pytest.mark.parametrize("risk", ["shows", "runs", "money"])
def test_real_road_and_isolated_live_outputs(tmp_path: Path, risk: str) -> None:
    reads: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            reads.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"value": 19}')

        def log_message(self, format: str, *args: object) -> None:
            pass

    source = tmp_path / "definition"
    shutil.copytree(EXAMPLE, source)
    shutil.copyfile(Path(__file__).with_name("road_fixture.py"), source / "server.py")
    manifest = source / "app.toml"
    manifest.write_text(manifest.read_text().replace('risk = "shows"', f'risk = "{risk}"'))
    (source / "tests").mkdir()
    (source / "tests/test_own.py").write_text(OWN_TEST)
    (source / "proofs").mkdir()
    for stage, origin, value in (("sandbox", "recorded", 7), ("shadow", "live", 19)):
        (source / f"proofs/{stage}.json").write_text(
            json.dumps(
                {
                    "source": origin,
                    "cases": [
                        {"tool": "observe", "arguments": {}, "expected": {"value": value}},
                        {
                            "tool": "report",
                            "arguments": {},
                            "expected": {"output": "snapshot", "data": {"observations": []}},
                        },
                    ],
                }
            )
        )
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        owner = Supervisor(tmp_path / "home")
        try:
            installed = owner.install(source, trust="first_party")
            revision = str(installed["definition_hash"])
            volume = owner.home / "apps/exchange-status"
            (volume / "data/source.json").write_text(
                json.dumps({"recorded": 7, "url": f"http://127.0.0.1:{server.server_port}/live"})
            )
            if risk == "money":
                with pytest.raises(AppError, match="signature"):
                    owner.start("exchange-status")
            assert owner.road.advance("exchange-status", revision, "tests")["passed"] is True
            assert not reads
            assert not (volume / "data/tests-ran.txt").exists()
            assert owner.road.advance("exchange-status", revision, "sandbox")["stage"] == "sandbox"
            assert not reads
            result = owner.road.advance("exchange-status", revision, "shadow")
            assert reads == ["/live"]
            assert not (volume / "data/observed.json").exists()
            with closing(sqlite3.connect(owner.artifacts.index)) as db:
                assert db.execute("SELECT COUNT(*) FROM artifacts").fetchone() == (0,)
            if risk == "money":
                assert result["stage"] == "shadow"
                owner.road.signing_key(secrets.token_urlsafe(32))
                signature = owner.road.sign("exchange-status", revision, None)
                result = owner.road.publish("exchange-status", revision, signature=signature)
            assert result["stage"] == "live"
            assert owner.status("exchange-status")["status"] == "running"
            evidence = owner.road.evidence("exchange-status")
            assert [record["stage"] for record in evidence] == [
                "build",
                "tests",
                "sandbox",
                "shadow",
                "live",
            ]
            shadow_results = cast(Document, evidence[-2]["results"])
            assert shadow_results["outputs_consumed"] is False
            assert all(
                record["inputs"] and record["versions"] and record["results"] for record in evidence
            )
            with pytest.raises(AppError, match="owned by the host"):
                owner.call("exchange-status", "forge_evidence", {})
            assert owner.road.evidence("exchange-status") == evidence
        finally:
            owner.close()
            server.shutdown()
            thread.join(timeout=5)


@pytest.mark.parametrize(
    "suite",
    [
        "",
        "import unittest\nclass F(unittest.TestCase):\n"
        " def test_bad(self): self.fail('actual failure')\n",
    ],
)
def test_real_empty_or_failing_suite_never_advances(tmp_path: Path, suite: str) -> None:
    source = tmp_path / "definition"
    shutil.copytree(EXAMPLE, source)
    (source / "tests").mkdir()
    (source / "tests/test_own.py").write_text(suite)
    owner = Supervisor(tmp_path / "home")
    try:
        revision = str(owner.install(source, trust="first_party")["definition_hash"])
        with pytest.raises(AppError, match="actual app tests"):
            owner.road.advance("exchange-status", revision, "tests")
        record = owner.road.evidence("exchange-status")[-1]
        assert record["stage"] == "tests" and record["passed"] is False
        results = cast(Document, record["results"])
        assert results["exit_code"] != 0
        assert cast(Document, owner.get("exchange-status")["road"])["stage"] == "build"
    finally:
        owner.close()


def test_resolved_mcp_money_alias_is_denied(tmp_path: Path) -> None:
    source = tmp_path / "definition"
    shutil.copytree(EXAMPLE, source)
    (source / "server.py").write_text(
        'from fastmcp import FastMCP\nm = FastMCP("denied")\n'
        '@m.tool(meta={"tool_name": "create_order"})\ndef harmless(): return {}\nm.run()\n'
    )
    owner = Supervisor(tmp_path / "home")
    try:
        owner.install(source, trust="first_party")
        with pytest.raises(AppError, match="locked MCP server"):
            owner.start("exchange-status")
        assert owner.registry() == []
    finally:
        owner.close()
