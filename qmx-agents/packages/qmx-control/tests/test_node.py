from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from qmx_apps.docker import DockerSupervisor

from qmx_control.node import bootstrap_script, main, read_secret, run, verify
from qmx_control.server import create_app
from qmx_control.service import ControlService


def test_node_uses_same_authenticated_control_doors(tmp_path: Path) -> None:
    service = ControlService(tmp_path, tier="T2", node="sgp-1")
    service.settings_put("providers", {"litestream": {"orders": "s3://backup/orders"}})
    runtime = service.app_runtime()
    assert isinstance(runtime, DockerSupervisor)
    assert runtime.node == "sgp-1" and runtime.replicas == {"orders": "s3://backup/orders"}
    with TestClient(create_app(service, "per-node-fixture", "http://localhost")) as client:
        assert client.get("/api/apps").status_code == 401
        assert (
            client.get(
                "/api/apps", headers={"Authorization": "Bearer per-node-fixture"}
            ).status_code
            == 200
        )
        assert client.post("/mcp", json={}).status_code == 401


def test_vault_references_and_absent_credentials(tmp_path: Path) -> None:
    assert read_secret(tmp_path, "qmx/firecrawl", "firecrawl") is None
    (tmp_path / "firecrawl").write_text("fixture-secret", encoding="utf-8")
    (tmp_path / "firecrawl").chmod(0o600)
    assert read_secret(tmp_path, "qmx/firecrawl", "firecrawl") == "fixture-secret"
    with pytest.raises(ValueError):
        read_secret(tmp_path, "../token", "token")


def test_installer_is_pinned_and_has_no_subscription_material() -> None:
    script = bootstrap_script("a" * 40)
    assert "@REVISION@" not in script
    assert "tar -xf /opt/qmx-deploy/source.tar -C /opt/qmx-versions/" + "a" * 40 in script
    assert (
        "uv sync --project /opt/qmx/qmx-agents --package qmx-control --frozen --no-default-groups"
        in script
    )
    assert "systemctl enable qmx-node" in script
    with pytest.raises(ValueError):
        bootstrap_script("main; exit")


def test_the_server_setup_keeps_this_pc_primary() -> None:
    lines = bootstrap_script("a" * 40).splitlines()

    assert [line for line in lines if line.startswith("primary = ")] == ['primary = "pc"']


def test_a_vault_key_names_the_servers_place_or_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["qmx", "node", "vault", "key", "--home", str(tmp_path)])
    with pytest.raises(SystemExit):
        main()
    refused = capsys.readouterr().err
    monkeypatch.setattr(sys, "argv", [*sys.argv, "--machine", "home-server"])

    assert main() == 0
    assert "Name the server's place with --machine" in refused
    assert len(capsys.readouterr().out.strip()) == 44


def test_remote_script_pipe_preserves_linux_newlines() -> None:
    output = run(
        [sys.executable, "-c", "import sys; print(sys.stdin.buffer.read().hex())"],
        input_text="set -euo pipefail\necho ready\n",
    )
    assert bytes.fromhex(output) == b"set -euo pipefail\necho ready\n"


def test_verify_reports_missing_components(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(command: list[str], *, input_text: str | None = None) -> str:
        raise OSError("fixture: fresh node")

    monkeypatch.setattr("qmx_control.node.run", unavailable)
    assert not any(verify(tmp_path, tmp_path).values())
