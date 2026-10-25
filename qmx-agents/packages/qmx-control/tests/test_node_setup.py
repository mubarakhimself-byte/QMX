"""`qmx node setup`, `rebuild`, `pair` and `vault install` make the server ready to be home
(WRAPUP-PLAN WU9; DATA-PLAN DR2B, DR2D)."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Sequence
from pathlib import Path

from qmx_router.vault import MemorySource, VaultKey, VaultStore, as_text

from qmx_control.node import (
    host_unit,
    pair,
    pc_vault_document,
    rebuild,
    setup,
    setup_steps,
)

REVISION = "0" * 40


class Server:
    """The commands setup sends, answered as a fresh server would."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def __call__(self, command: list[str], text: str | None) -> str:
        self.sent.append(text if text is not None else command[-1])
        if command[-1] == "tailscale ip -4":
            return "100.64.0.9\n"
        if command[-1].startswith("sudo cat "):
            return "pairing-code\n"
        return "PASS host"


def test_setup_stops_the_hub_imports_then_starts_the_host(tmp_path: Path) -> None:
    server = Server()
    assert setup("qmx-server", tmp_path, revision=REVISION, call=server, say=lambda _: None) == 0
    scripts = server.sent[1:6]
    assert [
        line for script in scripts for line in script.splitlines() if line.startswith("systemctl")
    ] == [
        "systemctl daemon-reload",
        "systemctl stop qmx-host || true",
        "systemctl disable --now qmx-hub qmx-node",
        "systemctl enable --now qmx-host",
    ]
    assert "node import --home /var/lib/qmx --root /srv/qmx/library" in scripts[3]
    with (tmp_path / "settings.toml").open("rb") as handle:
        assert tomllib.load(handle) == {"library": {"hub_url": "http://100.64.0.9:8766"}}
    assert (tmp_path / "vault" / "pairing-key").read_text(encoding="utf-8") == "pairing-code\n"


def test_the_import_and_the_host_unit_name_the_one_root() -> None:
    importing = dict(setup_steps(REVISION))["import as qmx"]
    exec_start = next(line for line in host_unit().splitlines() if line.startswith("ExecStart="))
    assert exec_start == (
        "ExecStart=/opt/qmx/qmx-agents/.venv/bin/python -m qmx_host serve --home "
        "/srv/qmx/home/.qmx --port 8766 --role server --library-root /srv/qmx/library"
    )
    assert importing.endswith("--root /srv/qmx/library\n")


def test_a_dry_run_prints_the_order_and_writes_nothing(tmp_path: Path) -> None:
    said: list[str] = []
    setup("qmx-server", tmp_path, revision=REVISION, call=Server(), say=said.append, dry_run=True)
    assert [line for line in said if line.startswith("step ")] == [
        "step 1: bootstrap",
        "step 2: install the host",
        "step 3: stop and disable the standalone Hub",
        "step 4: move the pairing key",
        "step 5: import as qmx",
        "step 6: start the host",
    ]
    assert list(tmp_path.iterdir()) == []


def test_rebuild_stops_the_services_before_it_restores(tmp_path: Path) -> None:
    calls: list[Sequence[str]] = []

    def runner(call: Sequence[str]) -> str:
        calls.append(call)
        return ""

    found = rebuild(remote="bucket", root=tmp_path / "library", runner=runner)
    assert calls[0] == ("systemctl", "stop", "qmx-host", "qmx-hub")
    assert [call[1] for call in calls[1:]] == ["copy"] * 4 + ["copyto"] * 2
    assert found["restored"] is True


def test_re_pairing_keeps_the_outgoing_key_for_its_passes(tmp_path: Path) -> None:
    pair(tmp_path, "first")
    (tmp_path / "vault" / "run-pass-key").write_bytes(b"x" * 32)
    pair(tmp_path, "second")
    vault = tmp_path / "vault"
    assert (vault / "pairing-key").read_text(encoding="utf-8") == "second\n"
    assert (vault / "pairing-key.previous").read_text(encoding="utf-8") == "first\n"
    assert not (vault / "run-pass-key").exists()


def test_the_pcs_vault_document_opens_on_the_server_and_carries_no_trade_key(
    tmp_path: Path,
) -> None:
    server_key = VaultKey.generate()
    source = MemorySource(
        {
            "qmx/read/ctrader-app": '{"clientId":"id","clientSecret":"app"}',
            "qmx/openrouter": "model-key",
            "qmx/ctrader-live": "trade-key",
        }
    )
    document = json.loads(
        pc_vault_document(
            tmp_path, as_text(server_key.public_bytes()), machine="contabo", source=source
        )
    )
    copy = VaultStore("contabo")
    copy.sync(document)
    assert copy.names() == ("qmx/openrouter", "qmx/read/ctrader-app")
    assert copy.open("qmx/read/ctrader-app", server_key) == '{"clientId":"id","clientSecret":"app"}'
    assert "trade-key" not in json.dumps(document)
    assert source.values["qmx/ctrader-live"] == "trade-key"
