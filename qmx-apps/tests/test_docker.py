from __future__ import annotations

import json
import os
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from qmx_apps.docker import DockerSupervisor, docker, proxy_config
from qmx_apps.errors import AppError, Document

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/apps/exchange-status"


def test_proxy_rules_fail_closed() -> None:
    policy = proxy_config(["example.com"])
    assert "http_access deny private" in policy
    assert "dstdomain -n example.com" in policy
    assert "http_access deny all" in policy
    assert "http_access allow declared" not in proxy_config([])
    for host in ["*", ".example.com", "example.com\nhttp_access allow all", "https://example.com"]:
        with pytest.raises(AppError):
            proxy_config([host])


@pytest.mark.serial
@pytest.mark.skipif(os.environ.get("QMX_TEST_DOCKER") != "1", reason="opt-in Docker integration")
def test_container_lifecycle_egress_and_restore(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    manifest = source / "app.toml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace("network = []", 'network = ["example.com"]')
    manifest.write_text(text, encoding="utf-8")
    events: list[Document] = []
    owner = DockerSupervisor(
        tmp_path / "home", node="sgp-test", event_sink=lambda app_id, event: events.append(event)
    )
    try:
        owner.install(source)
        state = owner.start("exchange-status")
        assert state["status"] == "running"
        assert state["tier"] == "T2" and state["node"] == "sgp-test"
        name = "qmx-" + str(state["instance_id"])
        host_config = json.loads(docker("inspect", name))[0]["HostConfig"]
        assert host_config["ReadonlyRootfs"]
        assert host_config["CapDrop"] == ["ALL"]
        assert host_config["Memory"] > 0 and host_config["NanoCpus"] > 0
        check = (
            "import urllib.request,urllib.error,socket; "
            "u='http://blocked.invalid'; "
            "\ntry: urllib.request.urlopen(u,timeout=5)\n"
            "except urllib.error.HTTPError as e: assert e.code==403\n"
            "else: raise AssertionError('proxy allowed blocked host')\n"
            "try: socket.create_connection(('1.1.1.1',443),timeout=1)\n"
            "except OSError: pass\nelse: raise AssertionError('direct egress bypass')\n"
            "try: open('/image/escape','w')\nexcept OSError: pass\n"
            "else: raise AssertionError('root filesystem writable')\nprint('isolated')"
        )
        assert docker("exec", name, "python", "-c", check) == "isolated"
        owner.call(
            "exchange-status",
            "record",
            {
                "exchange": "fixture",
                "status": "unknown",
                "observed_at": "2026-10-08",
            },
        )
        owner.restart("exchange-status")
        result = owner.call("exchange-status", "snapshot", {})
        assert "fixture" in json.dumps(result)
        assert any(event.get("type") == "log" for event in events)
        assert any(event.get("status") == "running" and "metrics" in event for event in events)
        owner.stop("exchange-status")
        backup = tmp_path / "backup"
        snapshot = owner.snapshot("exchange-status", backup)
        fresh = DockerSupervisor(tmp_path / "fresh", node="nyc-test")
        try:
            fresh.install(source)
            fresh.restore("exchange-status", snapshot)
            fresh.start("exchange-status")
            assert "fixture" in json.dumps(fresh.call("exchange-status", "snapshot", {}))
            with closing(sqlite3.connect(fresh.home / "apps/exchange-status/app.db")) as db:
                assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            fresh.close()
        corrupt = tmp_path / "corrupt"
        shutil.copytree(snapshot, corrupt)
        with (corrupt / "app.db").open("ab") as file:
            file.write(b"tampered")
        rejected = DockerSupervisor(tmp_path / "rejected")
        try:
            rejected.install(source)
            with pytest.raises(AppError, match="checksum"):
                rejected.restore("exchange-status", corrupt)
            assert not (rejected.home / "apps/exchange-status/app.db").exists()
        finally:
            rejected.close()
        manifest.write_text(
            text.replace('network = ["example.com"]', "network = []").replace(
                'version = "1.0.0"', 'version = "1.0.1"'
            ),
            encoding="utf-8",
        )
        owner.install(source)
        denied = owner.start("exchange-status")
        config = json.loads(docker("inspect", "qmx-" + str(denied["instance_id"])))[0]
        assert config["HostConfig"]["NetworkMode"] == "none"
        replicated = DockerSupervisor(
            tmp_path / "replicated", replicas={"exchange-status": "s3://backup/example"}
        )
        try:
            replicated.install(source)
            with pytest.raises(AppError, match="SQLite"):
                replicated.start("exchange-status")
            assert not replicated._resources
        finally:
            replicated.close()
    finally:
        owner.close()
