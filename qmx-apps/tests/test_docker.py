from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
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
def test_app_with_locked_git_dependency(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    project = source / "pyproject.toml"
    project.write_text(
        project.read_text(encoding="utf-8").replace(
            '"fastmcp==4.0.11"', '"fastmcp==4.0.11", "typing-extensions"'
        )
        + "\n[tool.uv.sources]\ntyping-extensions = { git = "
        + '"https://github.com/python/typing_extensions", '
        + 'rev = "3ae9b7553a5c560dc09b484078d98ece2985eecd" }\n',
        encoding="utf-8",
    )
    uv = shutil.which("uv")
    assert uv is not None
    subprocess.run([uv, "lock", "--project", str(source)], check=True, capture_output=True)
    owner = DockerSupervisor(tmp_path / "node")
    try:
        definition = owner.install(source)
        image = "qmx-app:" + str(definition["definition_hash"])
        assert (
            docker(
                "run",
                "--rm",
                "--network",
                "none",
                "--entrypoint",
                "sh",
                image,
                "-c",
                "test ! -x /usr/bin/git && /opt/app-env/bin/python -c "
                "'import typing_extensions; print(\"installed\")'",
            )
            == "installed"
        )
        assert owner.start("exchange-status")["status"] == "running"
        assert owner.call("exchange-status", "snapshot", {})["artifact_ref"]
    finally:
        owner.close()


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
            "import urllib.request,urllib.error,socket,os,errno; "
            "u='http://blocked.invalid'; "
            "\ntry: urllib.request.urlopen(u,timeout=5)\n"
            "except urllib.error.HTTPError as e: assert e.code==403\n"
            "else: raise AssertionError('proxy allowed blocked host')\n"
            "try: socket.create_connection(('1.1.1.1',443),timeout=1)\n"
            "except OSError: pass\nelse: raise AssertionError('direct egress bypass')\n"
            "try: open('/image/escape','w')\nexcept OSError: pass\n"
            "else: raise AssertionError('root filesystem writable')\n"
            # exec starts a fresh interpreter without the bootstrap audit hook.
            "try: fd=os.open('/volume/road/steps.jsonl',os.O_WRONLY)\n"
            "except OSError as e: assert e.errno==errno.EROFS\n"
            "else: os.close(fd); raise AssertionError('road authority writable')\n"
            "print('isolated')"
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
            original = rejected.home / "apps/exchange-status/app.db"
            before = original.read_bytes()
            with pytest.raises(AppError, match="checksum"):
                rejected.restore("exchange-status", corrupt)
            assert original.read_bytes() == before
        finally:
            rejected.close()
        manifest.write_text(
            text.replace('network = ["example.com"]', "network = []").replace(
                'version = "1.0.0"', 'version = "1.0.1"'
            ),
            encoding="utf-8",
        )
        owner.install(source, expected_hash=str(owner.get("exchange-status")["definition_hash"]))
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
            state = replicated.status("exchange-status")
            assert state["status"] == "tripped"
            assert not docker(
                "ps",
                "-a",
                "--filter",
                "name=qmx-" + str(state["instance_id"]),
                "--format",
                "{{.Names}}",
            )
        finally:
            replicated.close()
    finally:
        owner.close()
